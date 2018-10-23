// ========== For debugging ===================
/*
#include <stdarg.h>
#include <string.h>

int incomingByte;
char inData[20];
int index = 0;
*/
void setup() {
  // put your setup code here, to run once:
  Serial.begin(57600);
  Serial3.begin(57600);
}

String a;
int incomingByte;
void loop() {
  Serial.println("Checking for connection request");
  /*
  // Test sending to RPi
  Serial2.println("send smth");
  Serial2.flush();
  */
  Serial.print("No of bytes received: ");
  Serial.println(Serial3.available());
  // Test receiving from RPI
  while (Serial3.available()){
    Serial.println("Received smth");
    incomingByte = Serial3.read();
    Serial.println(incomingByte);
    Serial3.println(incomingByte);
    //a = Serial.readString();
    //Serial.println(a);
  }
  
  
  delay(2000);

}
