#include "Arduino_FreeRTOS.h" //Preemption turned off in FreeRTOSConfig.h
#include "queue.h"
#include "semphr.h"
#include "event_groups.h"
#include "MPU9250.h"

/*
  By using Arduino_FreeRTOS library, one tick has been defined as 15ms
  https://github.com/feilipu/Arduino_FreeRTOS_Library
  In 1 second, 66.67 cycles of 15ms occur
*/

// ================ For debugging ===================
#include <stdarg.h>
#include <string.h>

char debugBuffer[1024];
void debugPrint(const char *str) {
  Serial.println(str);
  Serial.flush();
}
void dprintf(const char *fmt, ...) {
  va_list argptr;
  va_start(argptr, fmt);
  vsprintf(debugBuffer, fmt, argptr);
  va_end(argptr);
  debugPrint(debugBuffer);
}

// ===================================================

// ========================== values for FreeRTOS =========================
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
#define SETUP_DONE 5

// Task Variables
// The period of each tick is 15ms
const TickType_t oneTickPeriod = 1;  // 15ms period
const TickType_t sensorReaderPeriod = 2;  // 30ms period
const TickType_t oneSecondPeriod = 67;    // 1005ms period
const TickType_t twoSecondPeriod = 133;    // 1995ms period
const TickType_t fiveSecondPeriod = 333;  // 4995ms period
TickType_t sensorReaderLastWake;
TickType_t connHandlerLastWake = 0;

// Global variables
byte evenParityBit;
SemaphoreHandle_t queueSemaphore; // Used to lock the queue to one task
EventGroupHandle_t flagGroup;

static void sensorReader(void *p);
static void dataSender(void *p);
static void connHandler(void *p);


// ===================== values for Reading sensors ==============================
const float RS = 0.1;          // Shunt resistor value (in ohms)
const int VOLTAGE_REF = 5;  // Reference voltage for analog read
const int INDEX_FLEX_PIN = A1; // Pin connected to voltage divider output for flex sensor on index finger
const int PINKY_FLEX_PIN = A2; // Pin connected to voltage divider output for flex sensor on pinky finger
const int VOLTAGE_SENSOR_PIN = A5;
const int CURRENT_SENSOR_PIN = A4;  // Input pin for measuring Vout

// Measure the voltage at 5V and the actual resistance of your
// 10k resistor, and enter them below:
const float VCC = 4.98; // Measured voltage of Arduino 5V line
const float R_DIV_INDEX = 9881.0; // Measured resistance of 10k resistor on index
const float R_DIV_PINKY = 9861.0; // Measured resistance of 10k resistor on pinky

// Upload the code, then try to adjust these values to more
// accurately calculate bend degree.
const float INDEX_STRAIGHT = 34012.2; // resistance when index finger straight
const float PINKY_STRAIGHT = 30537.0; // resistance when pinky finger straight
const float INDEX_BEND = 70012.20; // resistance at 90 deg for index
const float PINKY_BEND = 90374.0; // resistance at 90 deg for pinky

// Global Variables
int currentValue;   // Variable to store analog read current
int voltageValue;   // Variable to store analog read voltage
float current;      // Calculated current value
float voltage;      // Calculated voltage value
long prevTime = 0;
long timeElapsed = 0;
float power = 0;
float energy = 0;
const int NO_OF_READINGS = 10;
float readingsArray[NO_OF_READINGS];  // Used to pass readings between tasks
byte readingsBuffer[100];

// an MPU9250 object with the MPU-9250 sensor on I2C bus 0 with address 0x68
MPU9250 IMU(Wire, 0x68);
int status;

// =================== Helper functions =====================
// Package data for sending
int serialise(float readings[], int len) {
  long tempReading;
  int start;
  byte tempByte;
  byte xorBit = 0;
  for (int i = 0; i < len; i++) {
    tempReading = (long)(readings[i] * 1000000);  //Converts float to int with 5 decimal place precision
    start = i * sizeof(tempReading);
    for (int j = 0; j < sizeof(tempReading); j++) {
      tempByte = tempReading & 255; //Extract 8 LSB
      readingsBuffer[start + j] = tempByte;
      tempReading = tempReading >> 8;
      for (int k = 0; k < 8; k++) {
        xorBit = xorBit ^ bitRead(tempByte, k);
      }
    }
  }
  //Serial.println();
  evenParityBit = xorBit;
  return len * sizeof(tempReading);
}

void clearRxBuffer() {
  while (Serial2.available()) { //Clear the RX serial buffer
    Serial2.read();
  }
}

boolean serialTimeout() {
  //TickType_t timeoutCounter = xTaskGetTickCount();
  boolean hasTimeout = false;
  while (!Serial2.available()) { //Loops until data is recevied or timeout occurs
    /*
      if(xTaskGetTickCount() - timeoutCounter > 333){
      hasTimeout = true;
      break;
      }
    */
  }
  delay(1);   //Wait for the data to arrive
  return hasTimeout;
}

int cleanPacket(int packet) {
  int filter = 7;
  return packet & filter;
}

// ==================== Setup ================================
void setup() {
  Serial.begin(57600);
  Serial2.begin(57600);
  Serial2.println("Setup starts");
  Serial2.flush();

  pinMode(LED_BUILTIN, OUTPUT);

  // ---- Tasks setup: Higher numerical value, higher priority ----
  queueSemaphore = xSemaphoreCreateCounting(1, 0); //Used this instead of others as initial count can be set
  flagGroup = xEventGroupCreate();
  xTaskCreate(sensorReader, "sensorReader", STACK_SIZE, NULL, 1, NULL);
  xTaskCreate(dataSender, "dataSender", STACK_SIZE, NULL, 2, NULL);
  xTaskCreate(connHandler, "connHandler", STACK_SIZE, NULL, 3, NULL);

  // ------------- Sensors setup ----------------
  pinMode(INDEX_FLEX_PIN, INPUT);
  pinMode(PINKY_FLEX_PIN, INPUT);
  pinMode(VOLTAGE_SENSOR_PIN, INPUT);
  //while(!Serial) {}

  // start communication with IMU
  status = IMU.begin();
  if (status < 0) {
    //Serial.println("IMU initialization unsuccessful");
    //Serial.println("Check IMU wiring or try cycling power");
    //Serial.print("Status: ");
    //Serial.println(status);

    Serial2.println("Check IMU wiring or try cycling power");
    Serial2.flush();
    Serial2.println("IMU initialization unsuccessful");
    Serial2.flush();
    Serial2.print("Status: ");
    Serial2.println(status);
    Serial2.flush();
    while (1) {}
  }
  // setting the accelerometer full scale range to +/-2G
  if (IMU.setAccelRange(MPU9250::ACCEL_RANGE_2G) > 0) {
    //Serial.println("Accelerometer range set success!");
    Serial2.println("Accelerometer range set success!");
    Serial2.flush();
  }
  // setting the gyroscope full scale range to +/-500 deg/s
  if (IMU.setGyroRange(MPU9250::GYRO_RANGE_500DPS) > 0) {
    //Serial.println("Gyroscope range set success!");
    Serial2.println("Gyroscope range set success!");
    Serial2.flush();
  }
  // setting DLPF bandwidth to 20 Hz
  IMU.setDlpfBandwidth(MPU9250::DLPF_BANDWIDTH_20HZ);
  // setting SRD to 19 for a 50 Hz update rate
  IMU.setSrd(19);
  prevTime = millis();
  Serial2.println("Done");
  Serial2.flush();
}

// ==================== Loop ================================
void loop() {
  //Empty as scheduler is automatically started
}

// ===================== Tasks ================================
// Gather readings from sensors and enqueue the readings
void sensorReader(void *p) {
  int indexADC;
  float indexV;
  float indexR;
  while (1) {
    sensorReaderLastWake = xTaskGetTickCount();
    EventBits_t xbit = xEventGroupWaitBits(flagGroup, BIT_2, pdFALSE, pdTRUE, portMAX_DELAY); // Waits indefinitely until BIT_2 is set

    // ------ Reading voltage and current sensor data ------
    voltageValue = analogRead(VOLTAGE_SENSOR_PIN);    // Reading voltage value
    voltage = 2 * voltageValue * 5.0 / 1024;    // Remap the ADC value into a voltage number (5V reference)
    readingsArray[8] = voltage;

    // Follow the equation given by the INA169 datasheet to determine the current flowing through RS
    // Assume RL = 10k, Is = (Vout x 1k) / (RS x RL)
    currentValue = analogRead(CURRENT_SENSOR_PIN);    // Reading current value
    current = (currentValue * VOLTAGE_REF) / 1023.0;
    current = current / (10 * RS);
    readingsArray[9] = current;


    // ----- Read the IMU sensor -------
    IMU.readSensor();

    //Serial.print(IMU.getAccelX_mss(), 6);
    //Serial.print(" ");
    //Serial.print(IMU.getAccelY_mss(), 6);
    //Serial.print(" ");
    //Serial.print(IMU.getAccelZ_mss(), 6);
    //Serial.print(" ");
    //Serial.print(IMU.getGyroX_rads(), 6);
    //Serial.print(" ");
    //Serial.print(IMU.getGyroY_rads(), 6);
    //Serial.print(" ");
    //Serial.print(IMU.getGyroZ_rads(), 6);
    //Serial.print(" ");

    // Write sensor readings to global array: readingsArray
    readingsArray[0] = IMU.getAccelX_mss();
    readingsArray[1] = IMU.getAccelY_mss();
    readingsArray[2] = IMU.getAccelZ_mss();
    readingsArray[3] = IMU.getGyroX_rads();
    readingsArray[4] = IMU.getGyroY_rads();
    readingsArray[5] = IMU.getGyroZ_rads();

    // ----- Read the index finger's flex sensor -------
    // Read the ADC of index finger’s flex sensor, and calculate voltage and resistance from it
    indexADC = analogRead(INDEX_FLEX_PIN);
    indexV = indexADC * VCC / 1023.0;
    indexR = R_DIV_INDEX * (VCC / indexV - 1.0);

    // Use the calculated resistance to estimate the sensor's bend angle:
    float indexAngle = map(indexR, INDEX_STRAIGHT, INDEX_BEND, 0, 90.0);
    //Serial.print(indexAngle);
    //Serial.print(" ");
    readingsArray[6] = indexAngle;

    // ----- Read the pinky finger's flex sensor -------
    // Read the ADC of pinky’s flex sensor, and calculate voltage and resistance from it
    int pinkyADC = analogRead(PINKY_FLEX_PIN);
    float pinkyV = pinkyADC * VCC / 1023.0;
    float pinkyR = R_DIV_PINKY * (VCC / pinkyV - 1.0);
    // Use the calculated resistance to estimate the sensor's bend angle:
    float pinkyAngle = map(pinkyR, PINKY_STRAIGHT, PINKY_BEND, 0, 90.0);
    //Serial.print(pinkyAngle);
    //Serial.println();
    readingsArray[7] = pinkyAngle;

    //dprintf("Done with reading sensors");
    xSemaphoreGive(queueSemaphore);
    vTaskDelayUntil(&sensorReaderLastWake, sensorReaderPeriod);
  }
}

// Receives and sends data from/to Raspberry Pi
void dataSender(void *p) {
  int incomingByte;
  int buffLen;
  TickType_t timeoutCounter;

  while (1) {
    EventBits_t xbit = xEventGroupWaitBits(flagGroup, BIT_1, pdFALSE, pdTRUE, portMAX_DELAY); // Waits indefinitely until BIT_1 is set

    if (xSemaphoreTake(queueSemaphore, oneTickPeriod) == pdTRUE) {
      //Send no. of readings
      buffLen = serialise(readingsArray, NO_OF_READINGS);
      Serial2.write(buffLen);
      //Serial.print("Buffer len: ");
      //Serial.println(buffLen);
      Serial2.flush();

      //Wait for ACK or disconn request before sending data
      if (!serialTimeout()) {
        incomingByte = Serial2.read();
        //clearRxBuffer();
        if (incomingByte == cleanPacket(DISCONN_REQ)) {
          //dprintf("- Disconnection Request received");
          xEventGroupSetBits(flagGroup, BIT_0);
        } else if (incomingByte == cleanPacket(ACK)) {
          //dprintf("ACK for buffer length received");
          //dprintf("dataSender sending parity bit");
          Serial2.write(evenParityBit);
          Serial2.flush();
          //dprintf("dataSender sending data");
          Serial2.write(readingsBuffer, buffLen);
          Serial2.flush();

          if (!serialTimeout()) {
            incomingByte = Serial2.read();
            //clearRxBuffer();

            if (incomingByte == cleanPacket(DISCONN_REQ)) {
              //dprintf("- Disconnection Request received");
              xEventGroupSetBits(flagGroup, BIT_0);
            } else if (incomingByte == cleanPacket(ACK)) {
              // Do nothing
              //dprintf("- ACK received");
            } else if (incomingByte == cleanPacket(NAK)) {
              xSemaphoreGive(queueSemaphore);   // Initiate rerun of dataSender
              //dprintf("- NAK received");
            } else {
              //dprintf("- Unknown response from RPi");
            }
          }
        } else {
          //Serial.println(incomingByte);
        }
      } else {
        //dprintf("- Timeout");
        xEventGroupSetBits(flagGroup, BIT_0);
      }
    }
  }
}

// Handles connection/disconnection request from Raspberry Pi
// Blocks/unblocks tasks depending on request received
void connHandler(void *p) {
  int incomingByte;
  boolean hasTimeout;

  while (1) {
    //dprintf("Checking for connection request");
    digitalWrite(LED_BUILTIN, LOW);
    if (Serial2.available()) {
      delay(1);
      digitalWrite(LED_BUILTIN, HIGH);
      incomingByte = Serial2.read();
      //Serial.println(incomingByte);
      clearRxBuffer();

      if (incomingByte == cleanPacket(CONN_REQ)) { // When incoming byte is CONN_REQ
        //dprintf("Send ACK to RPi");
        Serial2.write(ACK);
        Serial2.flush();
        clearRxBuffer();

        hasTimeout = serialTimeout();
        if (!hasTimeout) {
          incomingByte = Serial2.read();
          clearRxBuffer();
        }
        if (!hasTimeout && incomingByte == cleanPacket(ACK)) {
          //dprintf("Receive ACK from RPi");
          //dprintf("-- Connected --");

          sensorReaderLastWake = xTaskGetTickCount();
          xEventGroupSetBits(flagGroup, BIT_1 | BIT_2);
          xEventGroupWaitBits(flagGroup, BIT_0, pdTRUE, pdTRUE, portMAX_DELAY);  // Waits indefinitely until BIT_0 is set

          //dprintf("Send ACK for disconnection request to RPi");
          Serial2.write(ACK);
          Serial2.flush();

          hasTimeout = serialTimeout();
          if (!hasTimeout) {
            incomingByte = Serial2.read();
            clearRxBuffer();
          }

          if (!hasTimeout && incomingByte == cleanPacket(ACK)) {
            //dprintf("Receive ACK for disconnection ACK from RPi");
            //dprintf("-- Disconnected --");
          } else {
            //dprintf("No ACK received from RPi for disconn request/timeout");
            //dprintf("-- Disconnected from timeout --");
          }
          xEventGroupClearBits(flagGroup, BIT_1 | BIT_2);
        } else {
          //dprintf("No ACK received from RPi for connection request/timeout");
          //dprintf("-- Connection request closed from timeout --");
        }
        clearRxBuffer();
        connHandlerLastWake = xTaskGetTickCount();
        vTaskDelayUntil(&connHandlerLastWake, fiveSecondPeriod);
      } else { //When incomingByte is anything but CONN_REQ
        //dprintf("Invalid request received from RPi");
        Serial2.write(NAK);
        Serial2.flush();
        clearRxBuffer();
      }
    } else {
      // Do polling of Serial.available() every 5 seconds to check for connection request from RPi
      clearRxBuffer();
      vTaskDelayUntil(&connHandlerLastWake, fiveSecondPeriod);
    }
  }
}
