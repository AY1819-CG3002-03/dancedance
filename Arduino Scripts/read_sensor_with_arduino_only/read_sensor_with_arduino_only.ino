/*
Advanced_I2C.ino
Brian R Taylor
brian.taylor@bolderflight.com

Copyright (c) 2017 Bolder Flight Systems

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the "Software"), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is 
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or 
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING 
BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND 
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
  */

#include "MPU9250.h"
#include <Arduino_FreeRTOS.h>
#include <event_groups.h>

// Constants
const int SENSOR_PIN = A0;  // Input pin for measuring Vout
const float RS = 0.1;          // Shunt resistor value (in ohms)
const int VOLTAGE_REF = 5;  // Reference voltage for analog read
const int INDEX_FLEX_PIN= A1; // Pin connected to voltage divider output for flex sensor on index finger
const int PINKY_FLEX_PIN= A2; // Pin connected to voltage divider output for flex sensor on pinky finger
const int VOLTAGE_SENSOR_PIN = A3;

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
float sensorValue;   // Variable to store value from analog read
float voltageValue;
float current;       // Calculated current value
long prevTime = 0;
long timeElapsed = 0;
float power = 0;
float energy = 0;

// FreeRTOS variables
#define BIT_0 (1 << 0)
#define BIT_1 (1 << 1)
#define STACK_SIZE 200
const TickType_t period = 2;  // 30ms period 
TickType_t sensorReaderLastWake;
TickType_t timeHandlerLastWake = 0;
static void sensorReader(void *p);
static void timeHandler(void *p);
unsigned long sensorReaderFirstWake;
unsigned int periodToCollect;
EventGroupHandle_t eventGroup = xEventGroupCreate();

// an MPU9250 object with the MPU-9250 sensor on I2C bus 0 with address 0x68
MPU9250 IMU(Wire,0x68);
int status;

// =========================== setup ==================================
void setup() {
  // serial to display data
  Serial.begin(57600);
  xTaskCreate(sensorReader,"sensorReader",STACK_SIZE,NULL,1,NULL);
  xTaskCreate(timeHandler,"timeHandler",STACK_SIZE,NULL,2,NULL);
  pinMode(INDEX_FLEX_PIN, INPUT);
  pinMode(PINKY_FLEX_PIN, INPUT);
  pinMode(VOLTAGE_SENSOR_PIN, INPUT);
  while(!Serial) {}

  // start communication with IMU 
  status = IMU.begin();
  if (status < 0) {
    Serial.println("IMU initialization unsuccessful");
    Serial.println("Check IMU wiring or try cycling power");
    Serial.print("Status: ");
    Serial.println(status);
    while(1) {}
  }
  // setting the accelerometer full scale range to +/-2G 
  if(IMU.setAccelRange(MPU9250::ACCEL_RANGE_2G) > 0){
    Serial.println("Accelerometer range set success!"); 
  }
  // setting the gyroscope full scale range to +/-500 deg/s
  if(IMU.setGyroRange(MPU9250::GYRO_RANGE_500DPS) > 0){
    Serial.println("Gyroscope range set success!");
  }
  // setting DLPF bandwidth to 20 Hz
  IMU.setDlpfBandwidth(MPU9250::DLPF_BANDWIDTH_20HZ);
  // setting SRD to 19 for a 50 Hz update rate
  IMU.setSrd(19);
  IMU.calibrateAccel();
  IMU.calibrateGyro();
  prevTime = millis();

  xEventGroupSetBits(eventGroup,BIT_1);
}

void loop() {}  //Empty as scheduler is automatically started

// ======================== Task ===========================
void timeHandler(void *p){
  int inChar;
  int timeToWait;
  while(1){
    xEventGroupWaitBits(eventGroup,BIT_1,pdTRUE,pdTRUE,portMAX_DELAY); // Waits indefinitely until BIT_1 is set
    //Serial.println(millis());
    timeToWait = 0;
    Serial.println("Enter no. of seconds to collect:");
    while(!Serial.available()){}
    while(Serial.available()){
      delay(5);
      inChar = Serial.read();
      if(isDigit((char)inChar)){
        //Serial.println(inChar);
        timeToWait *= 10;
        timeToWait += inChar - 48;
      }
    }
    
    //Serial.println(timeToWait);
    periodToCollect = timeToWait*1000;  //Multiply by 1000 to get ms
    //Serial.println(periodToCollect);
    
    sensorReaderLastWake = xTaskGetTickCount();
    sensorReaderFirstWake = millis();
    //Serial.println(sensorReaderFirstWake);
    xEventGroupSetBits(eventGroup,BIT_0);
  }
}

void sensorReader(void *p){
  
  while(1){
    xEventGroupWaitBits(eventGroup,BIT_0,pdFALSE,pdTRUE,portMAX_DELAY); // Waits indefinitely until BIT_0 is set
    sensorValue = analogRead(SENSOR_PIN);
    voltageValue = analogRead(VOLTAGE_SENSOR_PIN);
    voltageValue = 2 * voltageValue * 5.0 / 1024;
    // Remap the ADC value into a voltage number (5V reference)
    sensorValue = (sensorValue * VOLTAGE_REF) / 1023;

    // Follow the equation given by the INA169 datasheet to
    // determine the current flowing through RS. Assume RL = 10k
    // Is = (Vout x 1k) / (RS x RL)
    current = sensorValue / (10 * RS);

    //Calculate Power and Energy
  //  timeElapsed = millis() - prevTime;
  //  prevTime = millis();
  //  power = voltageValue * current;
  //  Serial.print("Time Elapsed = ");
  //  Serial.println(timeElapsed);
  //  energy += ((float)power * timeElapsed) / (1000.0 * 3600.0);
  //  // Output value (in amps) to the serial monitor to 3 decimal
  //  // places
  //  Serial.print(current, 3);
  //  Serial.println(" A");
  //  Serial.print(voltageValue, 3);
  //  Serial.println(" V");
  //  Serial.print(power, 3);
  //  Serial.println(" W");
  //  Serial.print(energy, 10);
  //  Serial.println(" Wh");

  //  delay(500);

  //   read the sensor
    IMU.readSensor();

    // display the data
  //  Serial.print("Accelerometer Readings: ");  
  //  Serial.print("\t");
//  Serial.print("Gyroscope Readings: ");
//  Serial.print("\t");
//  Serial.print("Temperature: ");
//  Serial.println(IMU.getTemperature_C(),6);
//  Serial.print("X: ");
//  Serial.print(IMU.getAccelX_mss(),6);
//  Serial.print("\t\t\t");
//  Serial.println(IMU.getGyroX_rads(),6);
//  Serial.print("Y: ");  
//  Serial.print(IMU.getAccelY_mss(),6);
//  Serial.print("\t\t\t");
//  Serial.println(IMU.getGyroY_rads(),6);
//  Serial.print("Z: ");
//  Serial.print(IMU.getAccelZ_mss(),6);
//  Serial.print("\t\t\t");
//  Serial.println(IMU.getGyroZ_rads(),6);
//  delay(100);

    Serial.print(IMU.getAccelX_mss(), 6);
    Serial.print(",");
    Serial.print(IMU.getAccelY_mss(), 6);    
    Serial.print(",");
    Serial.print(IMU.getAccelZ_mss(), 6);
    Serial.print(",");    
    Serial.print(IMU.getGyroX_rads(), 6);
    Serial.print(",");
    Serial.print(IMU.getGyroY_rads(), 6);
    Serial.print(",");
    Serial.print(IMU.getGyroZ_rads(), 6);
    Serial.print(",");
    
    int indexADC = analogRead(INDEX_FLEX_PIN);
    float indexV = indexADC * VCC / 1023.0;
    float indexR = R_DIV_INDEX * (VCC / indexV - 1.0);

    //  Serial.println("Resistance of index finger: " + String(indexR) + " ohms");

    // Use the calculated resistance to estimate the sensor's
    // bend angle:
    float indexAngle = map(indexR, INDEX_STRAIGHT,INDEX_BEND,
                   0, 90.0);

    Serial.print(indexAngle);
    //Serial.print(String(indexAngle));
    Serial.print(",");                      
//  Serial.println("Bend of index finger: " + String(indexAngle) + " degrees");
//  Serial.println();

 // Read the ADC of pinky’s flex sensor, and calculate voltage and resistance from it
    int pinkyADC = analogRead(PINKY_FLEX_PIN);
    float pinkyV = pinkyADC * VCC / 1023.0;
    float pinkyR = R_DIV_PINKY * (VCC / pinkyV - 1.0);
//  Serial.println("Resistance of pinky finger: " + String(pinkyR) + " ohms");

//  // Use the calculated resistance to estimate the sensor's
//  // bend angle:
    float pinkyAngle = map(pinkyR, PINKY_STRAIGHT, PINKY_BEND,
                   0, 90.0);
//  Serial.println("Bend of pinky finger: " + String(pinkyAngle) + " degrees");
    Serial.print(pinkyAngle);
    //Serial.print(String(pinkyAngle));
    Serial.println();

    //Check whether time is up
    //Serial.println(sensorReaderFirstWake + periodToCollect);
    //Serial.println(millis());
    if( millis() > (sensorReaderFirstWake + periodToCollect)){
      xEventGroupClearBits(eventGroup,BIT_0);
      xEventGroupSetBits(eventGroup,BIT_1);
    }else{
      vTaskDelayUntil(&sensorReaderLastWake,period);
    }
  }
}
