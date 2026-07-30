import serial
import serial.tools.list_ports
import threading
import time
import sys

def list_ports():
    """利用可能なCOMポートを一覧表示"""
    ports = serial.tools.list_ports.comports()
    if not ports:
        print("利用可能なシリアルポートが見つかりませんでした。")
        return []
    
    print("\n--- 利用可能なシリアルポート ---")
    for i, port in enumerate(ports):
        print(f"[{i}] {port.device} - {port.description}")
    print("--------------------------------\n")
    return ports

def read_from_arduino(ser, stop_event):
    """Arduinoからの応答メッセージを受信して表示するスレッド"""
    while not stop_event.is_set():
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"\n[Arduino応答]: {line}")
                    print("> ", end="", flush=True)
        except Exception as e:
            print(f"\n[エラー] 受信エラー: {e}")
            break
        time.sleep(0.01)

def main():
    print("=== モーター制御 ターミナルスクリプト (9600 bps) ===")
    
    # 1. COMポートの選択
    ports = list_ports()
    if not ports:
        sys.exit(1)
    
    port_input = input("接続するポート番号を入力してください (例: 0 または COM3): ").strip()
    
    # インデックス指定かポート名直接指定かを判定
    if port_input.isdigit() and int(port_input) < len(ports):
        selected_port = ports[int(port_input)].device
    else:
        selected_port = port_input.upper()

    # 2. シリアル接続の確立 (Arduinoに合わせて 9600 bps に設定)
    try:
        ser = serial.Serial(selected_port, 9600, timeout=1)
        print(f"\n>> {selected_port} に接続しました。(ボーレート: 9600)")
        print(">> Arduinoのリセット待機中 (約2秒)...")
        time.sleep(2) # Arduino接続時の自動リセットを待機
    except Exception as e:
        print(f"[エラー] {selected_port} に接続できませんでした: {e}")
        sys.exit(1)

    print("\n--------------------------------------------------")
    print("【操作方法】")
    print("  'CW'  : 時計回りに1秒回転")
    print("  'CCW' : 反時計回りに1秒回転")
    print("  'q'   : 終了")
    print("--------------------------------------------------\n")

    # 3. 応答受信スレッドの開始
    stop_event = threading.Event()
    recv_thread = threading.Thread(target=read_from_arduino, args=(ser, stop_event), daemon=True)
    recv_thread.start()

    # 4. コマンド入力ルーチン
    try:
        while True:
            cmd = input("> ").strip()
            
            if cmd.lower() == 'q':
                print("終了します...")
                break
            
            if cmd:
                # Arduinoへ改行コード付きで送信
                ser.write((cmd + '\n').encode('utf-8'))
                
    except KeyboardInterrupt:
        print("\nCtrl+C が押されました。終了します...")
    finally:
        stop_event.set()
        if ser.is_open:
            ser.close()
        print("シリアルポートを切断しました。")

if __name__ == "__main__":
    main()