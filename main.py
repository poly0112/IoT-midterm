import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import QRect
from PyQt5.QtWidgets import QDialog
from PyQt5.QtCore import QTime, QTimer

from mqtt import MqttClient
from valve_controller import ValveController
from timer import ScheduleDialog

class AppController:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.login_window = uic.loadUi("ui/login.ui")
        self.main_window = uic.loadUi("ui/main.ui")
        self.active_valves = set()
        self.mqtt = MqttClient(on_message_callback=self.on_mqtt_message)
        self.valves = ValveController(self.main_window)
        self.reserve ={}
        self.valve_ids = ["L1", "L2","L3","L4","L5","R1", "R2","R3","R4","R5"]
        self.reserve = {vid: [] for vid in self.valve_ids}
        self.setup_login()
        
        # 지도용 Pixmap 원본 유지
        self.original_map = QPixmap("ui/map.PNG")

    def setup_timer(self):
    # 1. 먼저 현재 시각을 가져옴
        current_time = QTime.currentTime()
        msec_until_next_minute = (60 - current_time.second()) * 1000 - current_time.msec()

        # 2. 최초 00초 맞추기 위한 단발성 타이머
        self.init_timer = QTimer(self.main_window)
        self.init_timer.setSingleShot(True)
        self.init_timer.timeout.connect(self.start_repeating_timer)
        self.init_timer.start(msec_until_next_minute)  # 남은 시간만큼 딱 한 번 기다림

    def start_repeating_timer(self):
        # 3. 이후엔 매 분 00초마다 실행될 반복 타이머
        self.timer = QTimer(self.main_window)
        self.timer.timeout.connect(self.check_schedule_and_send_mqtt)
        self.timer.start(60 * 1000)  # 매 60초
        self.check_schedule_and_send_mqtt()  # 처음 한 번 즉시 실행 (필요 시)
        
    def check_schedule_and_send_mqtt(self):
        now_str = QTime.currentTime().toString("HH:mm")
        for valve_id in self.valve_ids:
            for time_str, state in self.reserve[valve_id]:
                if time_str == now_str:
                    status = 1 if state == "On" else 0
                    self.toggle_valve(valve_id,status)
                    now = QTime.currentTime()
                    min_diff = 24 * 60  # 1440분 (최대 하루)
                    next_time = None
                    next_state = None

                    for time_str, state in self.reserve[valve_id]:
                        t = QTime.fromString(time_str, "HH:mm")
                        if not t.isValid():
                            continue

                        # 현재 시각과의 분 단위 차이 계산
                        diff = (t.hour() - now.hour()) * 60 + (t.minute() - now.minute())
                        if diff < 0:
                            diff += 24 * 60  # 내일 실행될 예약
                        if diff==0:
                            continue
                        if diff < min_diff:
                            min_diff = diff
                            next_time = t
                            next_state = state

                    label = getattr(self.main_window, f"reserve_{valve_id}")
                    if next_time:
                        label.setText(f"다음 예약 : {next_time.toString('HH:mm')}  /  {next_state}")
                    print(f"[MQTT] {valve_id} → {status}")

    def setup_login(self):
        self.login_window.btn_login.clicked.connect(self.check_login)
        self.login_window.show()

    def check_login(self):
        username = self.login_window.input_username.text()
        password = self.login_window.input_password.text()

        if username == "admin" and password == "1234":
            self.login_window.close()
            self.main_window.show()
            self.connect_valve_buttons()
            self.setup_camera_buttons()
            self.main_window.btn_exit.clicked.connect(self.exit_app)
            self.mqtt.connect()
            self.connect_timer_buttons()
            self.setup_timer()
            # 초기 지도 표시
            self.main_window.pipe_image.setPixmap(self.original_map)
            self.main_window.pipe_image.setScaledContents(False)
        else:
            QtWidgets.QMessageBox.warning(self.login_window, "Login Failed", "Invalid credentials")
            
    def toggle_label_visibility(self, label):
        # print(label)
        label.setVisible(not label.isVisible())

    def setup_camera_buttons(self):
        for i in range(1, 6):
            button = getattr(self.main_window, f"pushButton_{i}")
            label = getattr(self.main_window, f"Camera{i}")
            label.setVisible(False)
            button.clicked.connect(lambda _, l=label: self.toggle_label_visibility(l))

    def connect_valve_buttons(self):
        for valve_id in self.valves.get_all_valve_ids():
            button = getattr(self.main_window, f"btn_valve{valve_id}")
            button.clicked.connect(lambda _, vid=valve_id: self.toggle_valve(vid))

    def toggle_valve(self, valve_id,status=2):
        status = self.valves.toggle(valve_id,status)
        self.mqtt.publish(valve_id, "on" if status else "off")

        if status:
            self.active_valves.add(valve_id)
        else:
            self.active_valves.discard(valve_id)
        self.update_map_highlight()

    def exit_app(self):
        self.app.quit()

    def update_map_highlight(self):
        zone_mapping = {
            "L1": [QRect(330, 325, 25, 25), QRect(370, 180, 25, 25)],   # 예시: L1 → 두 영역
            "L2": [QRect(415, 405, 25, 25), QRect(510, 395, 25, 25), QRect(500, 430, 25, 25), QRect(555, 430, 25, 25), QRect(450, 515, 25, 25), QRect(415, 565, 25, 25)],
            "L3": [QRect(332, 422, 25, 25), QRect(272, 477, 25, 25), QRect(320, 615, 25, 25)],
            "L4": [QRect(70, 535, 25, 25), QRect(100, 580, 25, 20), QRect(85, 620, 25, 25)],
            "L5": [QRect(190, 400, 25, 25), QRect(123, 330, 25, 25)],
            "R1": [QRect(375, 310, 25, 25), QRect(470, 310, 25, 25)],
            "R2": [QRect(525, 515, 25, 25), QRect(525, 605, 25, 25)],
            "R3": [QRect(350, 495, 25, 25), QRect(315, 562, 25, 25), QRect(415, 617, 25, 25)],
            "R4": [QRect(183, 535, 25, 25), QRect(178, 610, 25, 25)],
            "R5": [QRect(95, 380, 25, 25), QRect(110, 450, 25, 25), QRect(153, 480, 25, 25)],
        }

        pixmap = QPixmap(self.original_map)
        painter = QPainter(pixmap)
        color = QColor(255, 0, 0, 120)

        for valve_id in self.active_valves:
            for rect in zone_mapping.get(valve_id, []):
                painter.fillRect(rect, color)

        painter.end()
        self.main_window.pipe_image.setPixmap(pixmap)
        self.main_window.pipe_image.setScaledContents(False)

    def on_mqtt_message(self, topic, payload):
        self.valves.update_status_from_mqtt(topic, payload)

    def run(self):
        sys.exit(self.app.exec_())
    def connect_timer_buttons(self):
        for valve_id in ["L1", "L2", "L3", "L4", "L5", "R1", "R2", "R3", "R4", "R5"]:
            button = getattr(self.main_window, f"timer_{valve_id}")
            button.clicked.connect(lambda _, vid=valve_id: self.open_schedule_dialog(vid))
            
    def open_schedule_dialog(self, valve_id):
        dialog = ScheduleDialog(self.main_window, valve_id,self.reserve[valve_id])
        if dialog.exec_() == QDialog.Accepted:
            self.reserve[valve_id] = dialog.get_data()
            # if self.reserve[valve_id]:
            now = QTime.currentTime()
            min_diff = 24 * 60  # 1440분 (최대 하루)
            next_time = None
            next_state = None

            for time_str, state in self.reserve[valve_id]:
                t = QTime.fromString(time_str, "HH:mm")
                if not t.isValid():
                    continue

                # 현재 시각과의 분 단위 차이 계산
                diff = (t.hour() - now.hour()) * 60 + (t.minute() - now.minute())
                if diff < 0:
                    diff += 24 * 60  # 내일 실행될 예약
                if diff==0:
                    continue
                if diff < min_diff:
                    min_diff = diff
                    next_time = t
                    next_state = state

            label = getattr(self.main_window, f"reserve_{valve_id}")
            if next_time:
                label.setText(f"다음 예약 : {next_time.toString('HH:mm')}  /  {next_state}")
            else:
                label.setText(f"다음 예약 : 없음")
            # label.setText(f"예약 시간 : {selected_time.toString('HH:mm')}  /  {selected_state}")
            # print(f"[{valve_id}] 예약 시간: {selected_time.toString()}, 상태: {selected_state}")
            # 이 자리에서 예약 저장 또는 처리 로직 추가


if __name__ == "__main__":
    app = AppController()
    app.run()
