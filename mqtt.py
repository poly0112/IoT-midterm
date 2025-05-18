import paho.mqtt.client as mqtt
import ssl

# HiveMQ Cloud 설정
BROKER = "90c8db7f280c4be791395b4e7f0d7643.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "pohang"
PASSWORD = "Iotmidterm1234"

TOPIC_PREFIX = "iottest/valve"

class MqttClient:
    def __init__(self, on_message_callback):
        self.client = mqtt.Client()
        self.client.username_pw_set(USERNAME, PASSWORD)

        # TLS 설정 (테스트 목적: 인증서 검증 생략)
        self.client.tls_set(cert_reqs=ssl.CERT_NONE)
        self.client.tls_insecure_set(True)

        self.client.on_message = self._on_message
        self.client.on_connect = self._on_connect
        self.on_message_callback = on_message_callback

    def connect(self):
        self.client.connect(BROKER, PORT, 60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("🟢 연결 성공 (HiveMQ)")
            self.client.subscribe(f"{TOPIC_PREFIX}/status/+")
        else:
            print(f"🔴 연결 실패, 반환 코드: {rc}")

    def _on_message(self, client, userdata, msg):
        print(f"📩 수신됨: {msg.topic} -> {msg.payload.decode()}")
        self.on_message_callback(msg.topic, msg.payload.decode())

    def publish(self, valve_id, state):
        topic = f"{TOPIC_PREFIX}/{valve_id}"
        print(f"📤 발행: {topic} -> {state}")
        self.client.publish(topic, state, qos=1)
