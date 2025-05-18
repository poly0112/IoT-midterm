from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTimeEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import QTime


class ScheduleDialog(QDialog):
    def __init__(self, parent=None, valve_id=None,reserve_list=None):
        super().__init__(parent)
        self.valve_id = valve_id
        if valve_id and len(valve_id) == 2:
            number = valve_id[1]
            side = valve_id[0]
            if side == 'L':
                zone_name = f"{number}-1구역"
            elif side == 'R':
                zone_name = f"{number}-2구역"
            else:
                zone_name = valve_id  # fallback
        else:
            zone_name = valve_id  # fallback

        self.setWindowTitle(f"{zone_name} 예약 설정")
        # self.setWindowTitle(f"{valve_id} 예약 설정")
        self.resize(400, 300)
        self.selected_time = None
        self.selected_state = None
        self.reserve_list =reserve_list
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                font-size: 14px;
            }
            QLabel {
                font-weight: bold;
                margin-bottom: 4px;
            }
            QTimeEdit, QComboBox {
                height: 30px;
                padding: 2px 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 4px;
                height: 28px;
                width: 80px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        self.state_combo = QComboBox()
        self.state_combo.addItems(["On", "Off"])
        input_layout.addWidget(QLabel("상태:"))
        input_layout.addWidget(self.state_combo)

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())
        input_layout.addWidget(QLabel("시간:"))
        input_layout.addWidget(self.time_edit)

        self.add_button = QPushButton("추가")
        self.add_button.clicked.connect(self.add_schedule)
        input_layout.addWidget(self.add_button)

        layout.addLayout(input_layout)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["시간", "상태", "삭제"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(QLabel("예약 목록"))
        layout.addWidget(self.table)

        self.ok_button = QPushButton("확인")
        self.ok_button.clicked.connect(self.accept)

        layout.addWidget(self.ok_button)
        self.setLayout(layout)
        
        if self.reserve_list:
            for time_str, state_str in self.reserve_list:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(time_str))
                self.table.setItem(row, 1, QTableWidgetItem(state_str))

                delete_button = QPushButton("삭제")
                delete_button.clicked.connect(lambda _, r=row: self.table.removeRow(r))
                self.table.setCellWidget(row, 2, delete_button)

    def add_schedule(self):
        self.selected_time = self.time_edit.time()
        self.selected_state = self.state_combo.currentText()

        time_str = self.selected_time.toString("HH:mm")
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(time_str))
        self.table.setItem(row, 1, QTableWidgetItem(self.selected_state))

        delete_button = QPushButton("삭제")
        delete_button.clicked.connect(lambda _, r=row: self.table.removeRow(r))
        self.table.setCellWidget(row, 2, delete_button)

    def get_data(self):
        schedule_list = []
        for row in range(self.table.rowCount()):
            time_item = self.table.item(row, 0)
            state_item = self.table.item(row, 1)
            if time_item and state_item:
                time_str = time_item.text()
                state_str = state_item.text()
                schedule_list.append((time_str, state_str))
        return schedule_list