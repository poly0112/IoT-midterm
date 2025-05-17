import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import QRect

from mqtt import MqttClient
from valve_controller import ValveController


class AppController:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.login_window = uic.loadUi("ui/login.ui")
        self.main_window = uic.loadUi("ui/main.ui")
        self.active_valves = set()
        self.mqtt = MqttClient(on_message_callback=self.on_mqtt_message)
        self.valves = ValveController(self.main_window)

        self.setup_login()

        # 지도용 Pixmap 원본 유지
        self.original_map = QPixmap("ui/map.PNG")

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
            

            # 초기 지도 표시
            self.main_window.pipe_image.setPixmap(self.original_map)
            self.main_window.pipe_image.setScaledContents(True)
        else:
            QtWidgets.QMessageBox.warning(self.login_window, "Login Failed", "Invalid credentials")
            
    def setup_camera_buttons(self):
        for i in range(1, 6):
            button = getattr(self.main_window, f"pushButton_{i}")
            label = getattr(self.main_window, f"Camera{i}")
            label.setVisible(False)  # 초기에는 안 보이게

            # 클릭 시 해당 라벨 토글
            button.clicked.connect(lambda _, l=label: l.setVisible(not l.isVisible()))

    def connect_valve_buttons(self):
        for valve_id in self.valves.get_all_valve_ids():
            button = getattr(self.main_window, f"btn_valve{valve_id}")
            button.clicked.connect(lambda _, vid=valve_id: self.toggle_valve(vid))

    def toggle_valve(self, valve_id):
        status = self.valves.toggle(valve_id)
        self.mqtt.publish(valve_id, "left on" if status else "left off")

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
        self.main_window.pipe_image.setScaledContents(True)

    def on_mqtt_message(self, topic, payload):
        self.valves.update_status_from_mqtt(topic, payload)

    def run(self):
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    app = AppController()
    app.run()
