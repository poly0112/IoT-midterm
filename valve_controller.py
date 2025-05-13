import time

class ValveController:
    def __init__(self, ui):
        self.ui = ui
        self.status = {}
        self.usage_time = {}
        self.start_time = {}

        for valve_id in self.get_all_valve_ids():
            self.status[valve_id] = False
            self.usage_time[valve_id] = 0

    def get_all_valve_ids(self):
        return [f"L{i}" for i in range(1, 6)] + [f"R{i}" for i in range(1, 6)]

    def toggle(self, valve_id):
        now = time.time()
        self.status[valve_id] = not self.status[valve_id]

        label = getattr(self.ui, f"status_valve{valve_id}")
        if self.status[valve_id]:
            label.setText("● ON")
            self.start_time[valve_id] = now
        else:
            label.setText("● OFF")
            if self.start_time[valve_id]:
                self.usage_time[valve_id] += now - self.start_time[valve_id]
                self.start_time[valve_id] = None
            self.update_time_label(valve_id)

        return self.status[valve_id]

    def update_time_label(self, valve_id):
        seconds = int(self.usage_time[valve_id])
        h, m, s = seconds // 3600, (seconds % 3600) // 60, seconds % 60
        label = getattr(self.ui, f"time_valve{valve_id}")
        label.setText(f"Time: {h:02}:{m:02}:{s:02}")

    def update_status_from_mqtt(self, topic, payload):
        valve_id = topic.split("/")[-1]
        if payload == "on":
            self.status[valve_id] = True
        else:
            self.status[valve_id] = False
        self.toggle(valve_id)
