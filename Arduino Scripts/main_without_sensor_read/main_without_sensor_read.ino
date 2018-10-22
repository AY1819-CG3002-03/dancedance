#include "Arduino_FreeRTOS.h" //Preemption turned off in FreeRTOSConfig.h
#include "queue.h"
#include "semphr.h"
#include "event_groups.h"

/*
 *By using Arduino_FreeRTOS library, one tick has been defined as 15ms
 *https://github.com/feilipu/Arduino_FreeRTOS_Library
 *In 1 second, 66.67 cycles of 15ms occur
*/

// ========== For debugging ===================
#include <stdarg.h>
#include <string.h>

char debugBuffer[1024];
void debugPrint(const char *str){
  Serial.println(str);
  Serial.flush();
}
void dprintf(const char *fmt, ...){
  va_list argptr;
  va_start(argptr, fmt);
  vsprintf(debugBuffer, fmt, argptr);
  va_end(argptr);
  debugPrint(debugBuffer);
}

// ============================================

//Serial: Pin 17 (RX) connect to Pin 10 (RX on RPi)
//Serial: Pin 16 (TX) connect to Pin 8 (TX on RPi)

//Use uxTaskGetSystemState() to find stack usage and adjust accordingly
#define STACK_SIZE 200

// Bits used as flags for flagGroup
#define BIT_0 (1 << 0)
#define BIT_1 (1 << 1)
#define BIT_2 (1 << 2)

// Define the packet types
#define CONN_REQ 1
#define DISCONN_REQ 2
#define ACK 3
#define NAK 4

// cycle period = 67 ticks * 15ms per tick = 1005ms
const TickType_t oneTickPeriod = 1;  // 15ms period
const TickType_t sensorReaderPeriod = 2;  // 30ms period
const TickType_t oneSecondPeriod = 67;    //1005ms
const TickType_t twoSecondPeriod = 133;    //1995ms
const TickType_t fiveSecondPeriod = 333;  //4995ms
TickType_t sensorReaderLastWake;
TickType_t connHandlerLastWake = 0;

#define NO_OF_READINGS 10
byte readingsBuffer[100];
byte evenParityBit;
float readingsArray[NO_OF_READINGS];  // Used to pass readings between tasks
SemaphoreHandle_t queueSemaphore; // Used to lock the queue to one task
EventGroupHandle_t flagGroup;

static void sensorReader(void *p);
static void dataSender(void *p);
static void connHandler(void *p);
TaskHandle_t xSensorReader = NULL;
TaskHandle_t xDataSender = NULL;
TaskHandle_t xConnHandler = NULL;


// =================== Helper functions =====================
// Package data for sending
int serialise(float readings[],int len){
  long tempReading;
  int start;
  byte tempByte;
  byte xorBit = 0;
  for(int i=0; i<len; i++){
    tempReading = (long)(readings[i] * 100000);  //Converts float to int with 5 decimal place precision
    start = i*sizeof(tempReading);
    for(int j=0; j<sizeof(tempReading); j++){
      tempByte = tempReading & 255; //Extract 8 LSB
      readingsBuffer[start + j] = tempByte;
      tempReading = tempReading >> 8;
      for(int k=0; k<8; k++){
        xorBit = xorBit ^ bitRead(tempByte,k);
      }
      //Serial.println(xorBit);
    }
  }
  evenParityBit = xorBit;
  return len*sizeof(tempReading);
}

void clearRxBuffer(){
  while(Serial2.available()){  //Clear the RX serial buffer
    Serial2.read();
  }
}

boolean serialTimeout(){
  TickType_t timeoutCounter = xTaskGetTickCount();
  boolean hasTimeout = false;
  while(!Serial2.available()){   //Loops until data is received or timeout occurs
    /*
    if(xTaskGetTickCount() - timeoutCounter > 333){
      hasTimeout = true;
      break;
    }
    */
  }
  //delay(1);   //Wait for the data to arrive
  return hasTimeout;
}

int cleanPacket(int packet){
  int filter = 7;
  return packet & filter;
}

// ==================== Setup ================================
void setup() {
  //Higher numerical value, higher priority
  queueSemaphore = xSemaphoreCreateCounting(1,0); //Used this instead of others as initial count can be set
  flagGroup = xEventGroupCreate();
  xTaskCreate(sensorReader,"sensorReader",STACK_SIZE,NULL,1,&xSensorReader);
  xTaskCreate(dataSender,"dataSender",STACK_SIZE,NULL,2,&xDataSender);
  xTaskCreate(connHandler,"connHandler",STACK_SIZE,NULL,3,&xConnHandler);
  Serial.begin(57600);
  Serial2.begin(57600);
}

// ==================== Loop ================================
void loop() {
  //Empty as scheduler is automatically started
}

// ===================== Tasks ================================
// Gather readings from sensors and enqueue the readings
void sensorReader(void *p){
  float readings[10] = {0.0,1.0,2.0,3.0,4.0,5.0,6.0,7.0,8.0,9.0};  //Mimic 10 sensor readings
  char temp[10];
  long cReading;
  byte buf[4];
  while(1){
    sensorReaderLastWake = xTaskGetTickCount();
    EventBits_t xbit = xEventGroupWaitBits(flagGroup,BIT_2, pdFALSE, pdTRUE, portMAX_DELAY);  // Waits indefinitely until BIT_2 is set

    //Reading sensor data
    for(int i=0; i<NO_OF_READINGS; i++){
      readings[i] += 0.01;
      readingsArray[i] = readings[i];
      //dtostrf(readings[i],7,4,temp);  //Converts float to string
    }
    
    //dprintf("sensors read");
    xSemaphoreGive(queueSemaphore);
    //dprintf("sensorReader here");
    vTaskDelayUntil(&sensorReaderLastWake,sensorReaderPeriod);
  }
}

// Receives and sends data from/to Raspberry Pi
void dataSender(void *p){
  int incomingByte;
  int buffLen;
  TickType_t timeoutCounter;
  
  while(1){
    EventBits_t xbit = xEventGroupWaitBits(flagGroup,BIT_1, pdFALSE, pdTRUE, portMAX_DELAY);  // Waits indefinitely until BIT_1 is set
    
    if(xSemaphoreTake(queueSemaphore, oneTickPeriod) == pdTRUE){
      //Send no. of readings
      buffLen = serialise(readingsArray,NO_OF_READINGS);
      Serial2.write(buffLen);
      Serial2.flush();

      //Wait for ACK or disconn request before sending data
      if(!serialTimeout()){
        incomingByte = Serial2.read();
        //clearRxBuffer();
        if(incomingByte == cleanPacket(DISCONN_REQ)){
          //dprintf("- Disconnection Request received");
          xEventGroupSetBits(flagGroup,BIT_0);
        }else if(incomingByte == cleanPacket(ACK)){
          //dprintf("ACK for buffer length received");
          //dprintf("dataSender sending parity bit");
          Serial2.write(evenParityBit);
          Serial2.flush();
          //dprintf("dataSender sending data");
          Serial2.write(readingsBuffer,buffLen);
          Serial2.flush();
      
          if(!serialTimeout()){
            incomingByte = Serial2.read();
            //clearRxBuffer();
        
            if(incomingByte == cleanPacket(DISCONN_REQ)){
              //dprintf("- Disconnection Request received");
              xEventGroupSetBits(flagGroup,BIT_0);
            }else if(incomingByte == cleanPacket(ACK)){
              // Do nothing
              //dprintf("- ACK received");
            }else if(incomingByte == cleanPacket(NAK)){
              xSemaphoreGive(queueSemaphore);   // Initiate rerun of dataSender
              //dprintf("- NAK received");
            }else{
              //dprintf("- Unknown response from RPi");
            }
          }
        }else{
          //Serial.println(incomingByte);
        }
      }else{
        //dprintf("- Timeout");
        xEventGroupSetBits(flagGroup,BIT_0);
      }
    }
  }
}

// Handles connection/disconnection request from Raspberry Pi
// Blocks/unblocks tasks depending on request received
void connHandler(void *p){
  int incomingByte;
  boolean hasTimeout;
  
  while(1){
    dprintf("Checking for connection request");
    if (Serial2.available()){
      //delay(1);
      incomingByte = Serial2.read();
      Serial.println(incomingByte);
      //clearRxBuffer();

      if(incomingByte == cleanPacket(CONN_REQ)){ // When incoming byte is CONN_REQ
        dprintf("Send ACK to RPi");
        //Serial2.println("send smth");
        Serial2.write(ACK);
        Serial2.flush();
        //clearRxBuffer();

        hasTimeout = serialTimeout();
        if(!hasTimeout){
          incomingByte = Serial2.read();
          //clearRxBuffer();
        }
        if(!hasTimeout && incomingByte == cleanPacket(ACK)){
          //dprintf("Receive ACK from RPi");
          //dprintf("-- Connected --");
        
          sensorReaderLastWake = xTaskGetTickCount();
          xEventGroupSetBits(flagGroup,BIT_1 | BIT_2);
          xEventGroupWaitBits(flagGroup, BIT_0, pdTRUE, pdTRUE, portMAX_DELAY);  // Waits indefinitely until BIT_0 is set
        
          //dprintf("Send ACK for disconnection request to RPi");
          Serial2.write(ACK);
          Serial2.flush();

          hasTimeout = serialTimeout();
          if(!hasTimeout){
            incomingByte = Serial2.read();
            //clearRxBuffer();
          }
            
          if(!hasTimeout && incomingByte == cleanPacket(ACK)){
              //dprintf("Receive ACK for disconnection ACK from RPi");
              //dprintf("-- Disconnected --");
          }else{
            //dprintf("No ACK received from RPi for disconn request/timeout");
            //dprintf("-- Disconnected from timeout --");
          }
          xEventGroupClearBits(flagGroup,BIT_1 | BIT_2);
        }else{
          //dprintf("No ACK received from RPi for connection request/timeout");
          //dprintf("-- Connection request closed from timeout --");  
        }
        //clearRxBuffer();
        connHandlerLastWake = xTaskGetTickCount();
        vTaskDelayUntil(&connHandlerLastWake,fiveSecondPeriod);
      }else{  //When incomingByte is anything but CONN_REQ
        //dprintf("Invalid request received from RPi");
        Serial2.write(NAK);
        Serial2.flush();
        //clearRxBuffer();
      }
    }else{
      // Do polling of Serial.available() every 5 seconds to check for connection request from RPi
      //clearRxBuffer();
      vTaskDelayUntil(&connHandlerLastWake,fiveSecondPeriod);
    }
  }
}
