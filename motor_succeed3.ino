#include <AccelStepper.h>

// ピン配置
const int EN_PIN   = 8; // イネーブルピン
const int STEP_PIN = 2; // X軸 STEPピン
const int DIR_PIN  = 5; // X軸 DIRピン

// モーター＆シリアル設定
#define BAUD_RATE 9600

// AccelStepperオブジェクトの初期化 (DRIVERモード)
AccelStepper stepper1(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

const byte buffSize = 64;
char inputBuffer[buffSize];
const char startMarker = '<';
const char endMarker = '>';

byte bytesRecvd = 0;
boolean readInProgress = false;
boolean newDataFromPC = false;

// 受信データ変数
char mode[buffSize] = {0};
char setting[buffSize] = {0};
int motorID = 0;
float value = 0.0;
char dir[buffSize] = {0};
float p1_optional = 0.0;

void setup() {
  Serial.begin(BAUD_RATE);

  pinMode(EN_PIN, OUTPUT);
  digitalWrite(EN_PIN, HIGH); // 待機時は非通電 (HIGH) にして発熱を防止

  stepper1.setMaxSpeed(4000.0);
  stepper1.setAcceleration(5000.0);

  Serial.println("<Arduino is ready>");
}

void loop() {
  getDataFromPC();
}

void getDataFromPC() {
  if (Serial.available() > 0) {
    char x = Serial.read();

    if (x == endMarker) {
      readInProgress = false;
      newDataFromPC = true;
      inputBuffer[bytesRecvd] = 0;
      parseData();
      return;
    }

    if (readInProgress) {
      inputBuffer[bytesRecvd] = x;
      bytesRecvd++;
      if (bytesRecvd >= buffSize) {
        bytesRecvd = buffSize - 1;
      }
    }

    if (x == startMarker) {
      bytesRecvd = 0;
      readInProgress = true;
    }
  }
}

void parseData() {
  char * strtokIndx;

  strtokIndx = strtok(inputBuffer, ",");
  if (strtokIndx == NULL) return;
  strcpy(mode, strtokIndx);

  strtokIndx = strtok(NULL, ",");
  if (strtokIndx == NULL) return;
  strcpy(setting, strtokIndx);

  strtokIndx = strtok(NULL, ",");
  if (strtokIndx == NULL) return;
  motorID = atoi(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  if (strtokIndx == NULL) return;
  value = atof(strtokIndx);

  strtokIndx = strtok(NULL, ",");
  if (strtokIndx == NULL) return;
  strcpy(dir, strtokIndx);

  strtokIndx = strtok(NULL, ",");
  if (strtokIndx == NULL) return;
  p1_optional = atof(strtokIndx);

  replyToPC();
  executeCommand();
}

void replyToPC() {
  Serial.print("<ACK:");
  Serial.print(mode);
  Serial.print(",");
  Serial.print(setting);
  Serial.println(">");
}

void executeCommand() {
  if (strcmp(mode, "SETTING") == 0) {
    if (strcmp(setting, "SPEED") == 0) {
      stepper1.setMaxSpeed(value);
    } else if (strcmp(setting, "ACCEL") == 0) {
      stepper1.setAcceleration(value);
    }
  } 
  else if (strcmp(mode, "RUN") == 0) {
    long stepsToMove = (long)p1_optional;
    if (strcmp(dir, "B") == 0) {
      stepsToMove = -stepsToMove;
    }

    // 1. 動作直前にモーターを通電（励磁）
    digitalWrite(EN_PIN, LOW);
    delay(5); // 電流が安定するまでわずかに待機

    stepper1.move(stepsToMove);
    
    // 目標位置までモーターを駆動
    while (stepper1.distanceToGo() != 0) {
      stepper1.run();
    }

    // 2. 動作完了後にモーターを消磁（非通電）
    digitalWrite(EN_PIN, HIGH);
  } 
  else if (strcmp(mode, "STOP") == 0) {
    stepper1.stop();
    digitalWrite(EN_PIN, HIGH); // 非常停止時も消磁
  }
}