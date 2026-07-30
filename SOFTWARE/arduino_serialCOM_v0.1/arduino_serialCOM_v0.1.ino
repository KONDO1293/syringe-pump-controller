// CNCシールド モーター回転テスト（時計回り・反時計回り）

const int EN_PIN   = 8; // イネーブルピン (全軸共通)

const int STEP_PIN = 2; // X軸 STEPピン (Y軸なら3, Z軸なら4)

const int DIR_PIN  = 5; // X軸 DIRピン  (Y軸なら6, Z軸なら7)



// モーターの速度調整（数値が小さいほど速く回ります。通常 500〜2000 程度）

const int STEP_DELAY_US = 1000;



void setup() {

  Serial.begin(9600);



  // ピンを出力用に設定

  pinMode(EN_PIN, OUTPUT);

  pinMode(STEP_PIN, OUTPUT);

  pinMode(DIR_PIN, OUTPUT);



  // モーターを有効化（通電）

  digitalWrite(EN_PIN, LOW);



  Serial.println("==========================================");

  Serial.println("   Motor Direction Test Started");

  Serial.println("==========================================");

}



void loop() {

  // ----------------------------------------------------

  // 1. 時計回り（HIGH）で 5秒間 回転

  // ----------------------------------------------------

  Serial.println("[回転] 時計回り (5秒間)...");

  digitalWrite(DIR_PIN, HIGH); // 方向設定：時計回り

  rotateMotorForSeconds(5);    // 5秒間パルスを出力して回転



  delay(1000); // 1秒一時停止



  // ----------------------------------------------------

  // 2. 反時計回り（LOW）で 5秒間 回転

  // ----------------------------------------------------

  Serial.println("[回転] 反時計回り (5秒間)...");

  digitalWrite(DIR_PIN, LOW);  // 方向設定：反時計回り

  rotateMotorForSeconds(5);    // 5秒間パルスを出力して回転



  delay(2000); // 2秒一時停止して次のループへ

}



// 指定した秒数（seconds）だけモーターにパルスを送って回転させる関数

void rotateMotorForSeconds(float seconds) {

  unsigned long startMillis = millis();

  unsigned long durationMillis = seconds * 1000;



  while (millis() - startMillis < durationMillis) {

    // 1ステップ分動かす（パルス出力）

    digitalWrite(STEP_PIN, HIGH);

    delayMicroseconds(STEP_DELAY_US);

    digitalWrite(STEP_PIN, LOW);

    delayMicroseconds(STEP_DELAY_US);

  }

} 

