const int INDEX_FLEX_PIN= A1; // Pin connected to voltage divider output for flex sensor on index finger
const int PINKY_FLEX_PIN= A2; // Pin connected to voltage divider output for flex sensor on pinky finger

// Measure the voltage at 5V and the actual resistance of your
// 10k resistor, and enter them below:
const float VCC = 4.98; // Measured voltage of Arduino 5V line
const float R_DIV_INDEX = 9881.0; // Measured resistance of 10k resistor on index
const float R_DIV_PINKY = 9861.0; // Measured resistance of 10k resistor on pinky

// Upload the code, then try to adjust these values to more
// accurately calculate bend degree.
const float INDEX_STRAIGHT = 32012.2; // resistance when index finger straight
const float PINKY_STRAIGHT = 26137.0; // resistance when pinky finger straight
const float INDEX_BEND = 74012.20; // resistance at 90 deg for index
const float PINKY_BEND = 64374.0; // resistance at 90 deg for pinky

void setup() 
{
  Serial.begin(9600);
  pinMode(INDEX_FLEX_PIN, INPUT);
  pinMode(PINKY_FLEX_PIN, INPUT);
}

void loop() 
{
  // Read the ADC, and calculate voltage and resistance from it
  int indexADC = analogRead(INDEX_FLEX_PIN);
  float indexV = indexADC * VCC / 1023.0;
  float indexR = R_DIV_INDEX * (VCC / indexV - 1.0);
  Serial.println("Resistance of index finger: " + String(indexR) + " ohms");

  // Use the calculated resistance to estimate the sensor's
  // bend angle:
  float indexAngle = map(indexR, INDEX_STRAIGHT,INDEX_BEND,
                   0, 90.0);
  Serial.println("Bend of index finger: " + String(indexAngle) + " degrees");
  Serial.println();

 // Read the ADC of pinky’s flex sensor, and calculate voltage and resistance from it
  int pinkyADC = analogRead(PINKY_FLEX_PIN);
  float pinkyV = pinkyADC * VCC / 1023.0;
  float pinkyR = R_DIV_PINKY * (VCC / pinkyV - 1.0);
  Serial.println("Resistance of pinky finger: " + String(pinkyR) + " ohms");

  // Use the calculated resistance to estimate the sensor's
  // bend angle:
  float pinkyAngle = map(pinkyR, PINKY_STRAIGHT, PINKY_BEND,
                   0, 90.0);
  Serial.println("Bend of pinky finger: " + String(pinkyAngle) + " degrees");
  Serial.println();

  delay(500);
}

