import paho.mqtt.client as mqtt

BROKER= "broker.emqx.io"
PORT = 1883
TOPIC= "iottest/valve/1"
class MqttClient:
    def __init__(self, on_message_callback):
        self.client = mqtt.Client()
        self.client.on_message = self._on_message
        # self.client.on_connect = self._on_connect
        self.on_message_callback = on_message_callback

    def connect(self, host="localhost", port=1883):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        for i in range(1, 6):
            self.client.subscribe(f"valve/L{i}")
            self.client.subscribe(f"valve/R{i}")

    def _on_message(self, client, userdata, msg):
        self.on_message_callback(msg.topic, msg.payload.decode())

    def publish(self, valve_id, state):
        self.client.publish(f"iottest/valve/{valve_id}", state,qos=1)
