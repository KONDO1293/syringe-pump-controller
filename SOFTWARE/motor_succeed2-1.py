import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import time
import csv
import os
from datetime import datetime

class PoseidonControllerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Syringe Pump Control Panel (motor_succeed1)")
        self.root.geometry("520x600")
        self.ser = None

        # CSVログ管理用変数
        self.is_logging = False          # ログ記録中かどうか
        self.current_log_path = None     # 現在記録中のCSVフルパス
        self.current_log_name = None     # 現在記録中のCSVファイル名

        # シリンジ選択データ (NIPRO シリンジの断面積 mm^2)
        self.syringes = {
            "NIPRO 2.5 mL": 96.76891,
            "NIPRO 5 mL": 141.02609,
            "NIPRO 10 mL": 201.06193,
            "NIPRO 20 mL": 346.36059,
            "NIPRO 30 mL": 452.38934,
            "NIPRO 50 mL": 646.92461
        }

        self.create_widgets()

    def generate_log_filename(self):
        """本日の日付と回数に基づいたファイル名を自動生成（プログラムと同じフォルダに保存）"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        date_str = datetime.now().strftime("%Y%m%d")
        
        count = 1
        while True:
            filename = f"{date_str}_log_{count}.csv"
            filepath = os.path.join(script_dir, filename)
            if not os.path.exists(filepath):
                return filepath, filename
            count += 1

    def start_logging(self):
        """ログ記録の開始"""
        if self.is_logging:
            messagebox.showinfo("案内", "すでにログ記録中です。")
            return

        self.current_log_path, self.current_log_name = self.generate_log_filename()
        
        # ヘッダー行の書き込み
        try:
            with open(self.current_log_path, mode='w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "日時 (Timestamp)",          # 実行日時（ミリ秒単位）
                    "COMポート (COM Port)",           # 使用COMポート
                    "シリンジ種類 (Syringe Type)",       # シリンジ種類
                    "設定速度(Speed_Value)",        # 速度設定値
                    "速度単位(Speed_Unit)",         # 速度単位
                    "加速度 (Accel Value)",        # 加速度設定値
                    "マイクロステップ (Microstep)",          # マイクロステップ
                    "動作種別 (Action Type)",        # 動作種別 (RUN / JOG / STOP)
                    "設定移動量 (Amount Value)",       # 設定移動量
                    "計算ステップ数 (Calculated Steps)",   # 内部変換ステップ数
                    "送信コマンド (Raw Command)"         # 送信コマンド
                ])
            
            self.is_logging = True
            self.lbl_log_status.config(text=f"状態: 記録中 ({self.current_log_name})", foreground="green")
            self.btn_start_log.config(state="disabled")
            self.btn_stop_log.config(state="normal")
            self.log(f">> ログ記録を開始しました: {self.current_log_name}")
        except Exception as e:
            messagebox.showerror("エラー", f"ログファイル作成失敗: {e}")

    def stop_logging(self):
        """ログ記録の停止と保存先の提示"""
        if not self.is_logging:
            return

        saved_path = self.current_log_path
        saved_name = self.current_log_name

        self.is_logging = False
        self.current_log_path = None
        self.current_log_name = None

        self.lbl_log_status.config(text="状態: 停止中", foreground="red")
        self.btn_start_log.config(state="normal")
        self.btn_stop_log.config(state="disabled")

        self.log(f">> ログ記録を停止しました。")
        self.log(f">> [保存ファイル名]: {saved_name}")
        self.log(f">> [保存先パス]: {saved_path}")

        # ダイヤログで通知
        messagebox.showinfo(
            "ログ保存完了",
            f"CSVログの保存を停止しました。\n\n"
            f"【ファイル名】\n{saved_name}\n\n"
            f"【保存場所】\n{saved_path}"
        )

    def save_experiment_log(self, action_type, amount_val, steps_val, raw_cmd):
        """実験ログをCSVファイルへ追記（記録中のみ実行）"""
        if not self.is_logging or not self.current_log_path:
            return

        try:
            # タイムスタンプを「秒.ミリ秒2桁」までフォーマット
            now = datetime.now()
            # microsecond // 10000 により 0〜99 の2桁（小数第2位）を取得して :02d でゼロ埋め
            ms_2digits = now.microsecond // 10000
            timestamp = f"{now.strftime('%Y-%m-%d %H:%M:%S')}.{ms_2digits:02d}"
            
            port = self.combo_port.get() if (self.ser and self.ser.is_open) else "N/A"
            syringe = self.combo_syringe.get()
            speed = self.entry_speed.get()
            unit = self.combo_unit.get()
            accel = self.entry_accel.get()
            mstep = self.combo_mstep.get()

            with open(self.current_log_path, mode='a', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    port,
                    syringe,
                    speed,
                    unit,
                    accel,
                    mstep,
                    action_type,
                    amount_val,
                    f"{steps_val:.2f}" if isinstance(steps_val, (int, float)) else steps_val,
                    raw_cmd
                ])
        except Exception as e:
            self.log(f">> ログ追記エラー: {e}")

    def create_widgets(self):
        # 1. シリアル接続設定
        frame_conn = ttk.LabelFrame(self.root, text="シリアル接続設定")
        frame_conn.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_conn, text="COMポート:").grid(row=0, column=0, padx=5, pady=5)
        self.combo_port = ttk.Combobox(frame_conn, values=self.get_ports(), width=12)
        self.combo_port.grid(row=0, column=1, padx=5, pady=5)

        self.btn_refresh = ttk.Button(frame_conn, text="更新", command=self.refresh_ports)
        self.btn_refresh.grid(row=0, column=2, padx=5, pady=5)

        self.btn_connect = ttk.Button(frame_conn, text="接続", command=self.toggle_connect)
        self.btn_connect.grid(row=0, column=3, padx=5, pady=5)

        # 2. ポンプ設定 (シリンジ、速度、加速度、マイクロステップ)
        frame_param = ttk.LabelFrame(self.root, text="ポンプパラメータ設定")
        frame_param.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_param, text="シリンジ種類:").grid(row=0, column=0, padx=5, pady=3, sticky="e")
        self.combo_syringe = ttk.Combobox(frame_param, values=list(self.syringes.keys()), width=18)
        self.combo_syringe.set("NIPRO 10 mL")
        self.combo_syringe.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(frame_param, text="単位:").grid(row=0, column=2, padx=5, pady=3, sticky="e")
        self.combo_unit = ttk.Combobox(frame_param, values=['mm/s', 'mL/s', 'mL/hr', 'µL/hr'], width=8)
        self.combo_unit.set("mm/s")
        self.combo_unit.grid(row=0, column=3, padx=5, pady=3)

        ttk.Label(frame_param, text="速度:").grid(row=1, column=0, padx=5, pady=3, sticky="e")
        self.entry_speed = ttk.Entry(frame_param, width=10)
        self.entry_speed.insert(0, "2.0")
        self.entry_speed.grid(row=1, column=1, padx=5, pady=3, sticky="w")

        ttk.Label(frame_param, text="加速度:").grid(row=1, column=2, padx=5, pady=3, sticky="e")
        self.entry_accel = ttk.Entry(frame_param, width=10)
        self.entry_accel.insert(0, "10.0")
        self.entry_accel.grid(row=1, column=3, padx=5, pady=3, sticky="w")

        ttk.Label(frame_param, text="マイクロステップ:").grid(row=2, column=0, padx=5, pady=3, sticky="e")
        self.combo_mstep = ttk.Combobox(frame_param, values=['1', '2', '4', '8', '16', '32'], width=8)
        self.combo_mstep.set("1")
        self.combo_mstep.grid(row=2, column=1, padx=5, pady=3, sticky="w")

        self.btn_send_settings = ttk.Button(frame_param, text="設定をArduinoへ送信", command=self.send_settings)
        self.btn_send_settings.grid(row=3, column=0, columnspan=4, pady=8)

        # 3. 動作・JOG制御
        frame_control = ttk.LabelFrame(self.root, text="動作制御")
        frame_control.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_control, text="移動量 (単位依存):").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.entry_amount = ttk.Entry(frame_control, width=10)
        self.entry_amount.insert(0, "5.0")
        self.entry_amount.grid(row=0, column=1, padx=5, pady=5)

        self.btn_run = ttk.Button(frame_control, text="RUN (指定量移動)", command=self.run_pump)
        self.btn_run.grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frame_control, text="JOG送り幅:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.combo_jog_delta = ttk.Combobox(frame_control, values=['0.01', '0.1', '1.0', '10.0'], width=8)
        self.combo_jog_delta.set("1.0")
        self.combo_jog_delta.grid(row=1, column=1, padx=5, pady=5)

        frame_jog_btns = ttk.Frame(frame_control)
        frame_jog_btns.grid(row=2, column=0, columnspan=3, pady=5)

        self.btn_jog_plus = ttk.Button(frame_jog_btns, text="JOG + (押し出し)", command=lambda: self.jog_pump("F"))
        self.btn_jog_plus.pack(side="left", padx=5)

        self.btn_jog_minus = ttk.Button(frame_jog_btns, text="JOG - (引き込み)", command=lambda: self.jog_pump("B"))
        self.btn_jog_minus.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(frame_control, text="STOP (非常停止)", command=self.stop_pump)
        self.btn_stop.grid(row=3, column=0, columnspan=3, pady=5)

        # 4. 実験データ保存設定（ボタン式）
        frame_log_setting = ttk.LabelFrame(self.root, text="実験データ保存設定")
        frame_log_setting.pack(fill="x", padx=10, pady=5)

        self.btn_start_log = ttk.Button(frame_log_setting, text="ログ記録開始", command=self.start_logging)
        self.btn_start_log.grid(row=0, column=0, padx=10, pady=5)

        self.btn_stop_log = ttk.Button(frame_log_setting, text="ログ記録停止", command=self.stop_logging, state="disabled")
        self.btn_stop_log.grid(row=0, column=1, padx=10, pady=5)

        self.lbl_log_status = ttk.Label(frame_log_setting, text="状態: 停止中", foreground="red")
        self.lbl_log_status.grid(row=0, column=2, padx=10, pady=5, sticky="w")

        # 5. 通信ログ出力欄
        frame_log = ttk.LabelFrame(self.root, text="通信・動作ログ")
        frame_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.txt_log = tk.Text(frame_log, height=6)
        self.txt_log.pack(fill="both", expand=True, padx=5, pady=5)

    def log(self, msg):
        self.txt_log.insert(tk.END, msg + "\n")
        self.txt_log.see(tk.END)

    def get_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def refresh_ports(self):
        self.combo_port['values'] = self.get_ports()

    def toggle_connect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.btn_connect.config(text="接続")
            self.log(">> 切断しました。")
        else:
            try:
                port = self.combo_port.get()
                if not port:
                    messagebox.showwarning("警告", "COMポートを選択してください。")
                    return
                self.ser = serial.Serial(port, 9600, timeout=1)
                time.sleep(2) # リセット待機
                self.btn_connect.config(text="切断")
                self.log(f">> {port} に接続しました。(9600 bps)")
            except Exception as e:
                messagebox.showerror("エラー", f"接続失敗: {e}")

    def send_cmd(self, cmd):
        if self.ser and self.ser.is_open:
            self.ser.write(cmd.encode())
            self.log(f"送信: {cmd}")
            time.sleep(0.05)
            if self.ser.in_waiting > 0:
                res = self.ser.readline().decode('utf-8', errors='ignore').strip()
                self.log(f"受信: {res}")
        else:
            messagebox.showwarning("警告", "シリアル接続されていません。")

    def calc_steps(self, val_str):
        val = float(val_str)
        unit = self.combo_unit.get()
        s_area = self.syringes[self.combo_syringe.get()]
        mstep = int(self.combo_mstep.get())

        length_unit = unit.split('/')[0]
        if length_unit == "mm":
            mm = val
        elif length_unit == "mL":
            mm = (val * 1000.0) / s_area
        elif length_unit == "µL":
            mm = val / s_area

        # 1回転0.8mmピッチネジ、200ステップ/回転を基準
        steps = (mm / 0.8) * 200 * mstep
        return steps

    def send_settings(self):
        try:
            sp_val = float(self.entry_speed.get())
            ac_val = float(self.entry_accel.get())

            time_unit = self.combo_unit.get().split('/')[1]
            scale = 1.0
            if time_unit == "min": scale = 1.0 / 60.0
            elif time_unit == "hr": scale = 1.0 / 3600.0

            speed_steps = self.calc_steps(sp_val) * scale
            accel_steps = self.calc_steps(ac_val) * (scale ** 2)

            self.send_cmd(f"<SETTING,SPEED,1,{speed_steps:.2f},F,0.0>")
            self.send_cmd(f"<SETTING,ACCEL,1,{accel_steps:.2f},F,0.0>")
            messagebox.showinfo("完了", "設定を送信しました。")
        except Exception as e:
            messagebox.showerror("エラー", f"入力値エラー: {e}")

    def run_pump(self):
        try:
            amount_str = self.entry_amount.get()
            steps = self.calc_steps(amount_str)
            cmd = f"<RUN,DIST,1,0,F,{steps:.2f}>"
            self.send_cmd(cmd)
            
            # 単位から距離・体積部分のみを取り出す (例: "mm/s" -> "mm")
            unit_length = self.combo_unit.get().split('/')[0]

            # 記録中の場合のみ書き込み
            self.save_experiment_log(
                action_type="RUN",
                amount_val=f"{amount_str} {unit_length}",
                steps_val=steps,
                raw_cmd=cmd
            )
        except Exception as e:
            messagebox.showerror("エラー", f"送信失敗: {e}")

    def jog_pump(self, direction):
        try:
            amount_str = self.combo_jog_delta.get()
            steps = self.calc_steps(amount_str)
            cmd = f"<RUN,DIST,1,0,{direction},{steps:.2f}>"
            self.send_cmd(cmd)

            # 単位から距離・体積部分のみを取り出す (例: "mm/s" -> "mm")
            unit_length = self.combo_unit.get().split('/')[0]

            # 記録中の場合のみ書き込み
            action_label = "JOG_PUSH(+)" if direction == "F" else "JOG_PULL(-)"
            self.save_experiment_log(
                action_type=action_label,
                amount_val=f"{amount_str} {unit_length}",
                steps_val=steps,
                raw_cmd=cmd
            )
        except Exception as e:
            messagebox.showerror("エラー", f"送信失敗: {e}")

    def stop_pump(self):
        cmd = "<STOP,BLAH,1,0,F,0.0>"
        self.send_cmd(cmd)
        
        # 記録中の場合のみ書き込み
        self.save_experiment_log(
            action_type="STOP",
            amount_val="0",
            steps_val=0,
            raw_cmd=cmd
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = PoseidonControllerGUI(root)
    root.mainloop()