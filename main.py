import sys
from PyQt5 import QtWidgets, uic
from mqtt import MqttClient
from valve_controller import ValveController

class AppController:
    def __init__(self):
        self.app = QtWidgets.QApplication(sys.argv)
        self.login_window = uic.loadUi("ui/login.ui")
        self.main_window = uic.loadUi("ui/main.ui")

        self.mqtt = MqttClient(on_message_callback=self.on_mqtt_message)
        self.valves = ValveController(self.main_window)

        self.setup_login()

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
            self.mqtt.connect()
        else:
            QtWidgets.QMessageBox.warning(self.login_window, "Login Failed", "Invalid credentials")

    def connect_valve_buttons(self):
        for valve_id in self.valves.get_all_valve_ids():
            button = getattr(self.main_window, f"btn_valve{valve_id}")
            button.clicked.connect(lambda _, vid=valve_id: self.toggle_valve(vid))

    def toggle_valve(self, valve_id):
        status = self.valves.toggle(valve_id)
        self.mqtt.publish(valve_id, "left on" if status else "left off")
        print(f'valve_id{valve_id}')
        # print("")

    def on_mqtt_message(self, topic, payload):
        self.valves.update_status_from_mqtt(topic, payload)

    def run(self):
        sys.exit(self.app.exec_())

if __name__ == "__main__":
    app = AppController()
    app.run()
