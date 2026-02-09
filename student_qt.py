import sys, os, json, random
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QFont

# Import the shared networking module
import network_logic

class StudentWindow(QMainWindow):
    def __init__(self, name, teacher_ip, portal, classname):
        super().__init__()
        # 1. ASSIGN VARIABLES FIRST
        self.portal = portal
        self.teacher_ip = teacher_ip
        self.student_name = name
        self.student_class = classname
        
        # State Variables
        self.exam_active = False
        self.current_exam_data = {}
        self.answer_widgets = []
        self.detections = []
        self.start_time = None
        self.timer_id = QTimer()

        # 2. UI Setup
        self.setWindowTitle("Proctora Student Portal")
        self.setFixedSize(900, 600)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.init_detection_log_ui()
        
        # 3. Enter Dashboard
        self.init_dashboard_view()
        QApplication.instance().installEventFilter(self)

    def refresh_exam_list(self):
        """Fetch exam list from the teacher via network"""
        self.exam_table.setRowCount(0)
        resp = network_logic.network_request(self.teacher_ip, {
            "type": "GET_EXAM_LIST", "classname": self.student_class
        })
        if resp.get("status") == "success":
            for ex_name in resp.get("exams", []):
                row = self.exam_table.rowCount()
                self.exam_table.insertRow(row)
                self.exam_table.setItem(row, 0, QTableWidgetItem(ex_name))
                self.exam_table.setItem(row, 1, QTableWidgetItem("AVAILABLE"))

    def init_detection_log_ui(self):
        """Creates the bottom detection log used during exams"""
        self.log_dock = QWidget()
        self.log_dock.setFixedHeight(120)
        layout = QVBoxLayout(self.log_dock)
        
        header = QLabel("<b>Detection Log (Live Monitoring)</b>")
        header.setStyleSheet("color: #333;") 
        layout.addWidget(header)
        
        self.detection_display = QTextEdit()
        self.detection_display.setReadOnly(True)
        self.detection_display.setFont(QFont("Courier", 9))
        self.detection_display.setStyleSheet("""
            QTextEdit {
                background-color: #f0f0f0; 
                color: #ff0000;
                border: 1px solid #ccc;
                padding: 5px;
            }
        """)
        layout.addWidget(self.detection_display)
        self.log_dock.hide()

    # ===================== VIEWS =====================

    def init_dashboard_view(self):
        page = QWidget(); lay = QVBoxLayout(page)
        
        header = QLabel(f"Welcome, {self.student_name}")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B2C5D;")
        lay.addWidget(header)

        # Display the class assigned by the teacher
        class_info = QLabel(f"Current Class: <b>{self.student_class}</b>")
        lay.addWidget(class_info)

        lay.addWidget(QLabel("Assigned Exams (Double-click to start):"))
        self.exam_table = QTableWidget(0, 2)
        self.exam_table.setHorizontalHeaderLabels(["Exam Name", "Status"])
        self.exam_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.exam_table.itemDoubleClicked.connect(self.check_and_load_exam)
        lay.addWidget(self.exam_table)

        start_btn = QPushButton("START SELECTED EXAM")
        start_btn.setFixedHeight(50)
        start_btn.setStyleSheet("background-color: #0B2C5D; color: white; font-weight: bold;")
        start_btn.clicked.connect(self.check_and_load_exam)
        lay.addWidget(start_btn)

        self.refresh_exam_list()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        
    def refresh_exam_list(self):
        """Fetch exam list from the teacher via network"""
        self.exam_table.setRowCount(0)
        resp = network_logic.network_request(self.teacher_ip, {
            "type": "GET_EXAM_LIST", "classname": self.student_class
        })
        if resp.get("status") == "success":
            for ex_name in resp.get("exams", []):
                row = self.exam_table.rowCount()
                self.exam_table.insertRow(row)
                self.exam_table.setItem(row, 0, QTableWidgetItem(ex_name))
                self.exam_table.setItem(row, 1, QTableWidgetItem("AVAILABLE"))

    # ===================== EXAM LOGIC =====================

    def check_and_load_exam(self):
        row = self.exam_table.currentRow()
        if row == -1: return
        
        ex_name = self.exam_table.item(row, 0).text()

        # Download the specific exam JSON from the teacher
        resp = network_logic.network_request(self.teacher_ip, {
            "type": "GET_EXAM", 
            "exam_name": ex_name
        })
        
        if resp.get("status") == "success":
            self.current_exam_data = resp["data"]
            
            if self.current_exam_data.get("settings", {}).get("shuffle"):
                random.shuffle(self.current_exam_data["questions"])
            
            self.setup_welcome_screen(ex_name)
        else:
            QMessageBox.critical(self, "Error", "Failed to download exam from teacher.")

    def setup_welcome_screen(self, name):
        page = QWidget(); lay = QVBoxLayout(page)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay.addWidget(QLabel(f"<h2>Exam: {name}</h2>"))
        
        settings = self.current_exam_data.get("settings", {})
        info = "<b>Rules:</b><br/>- Anti-cheat active<br/>- Tab switching is logged"
        if settings.get("duration_enabled"):
            info += f"<br/>- Time Limit: {settings.get('duration')} minutes"
        
        info_lbl = QLabel(info); info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(info_lbl)

        start_btn = QPushButton("BEGIN EXAM")
        start_btn.setFixedSize(200, 50)
        start_btn.clicked.connect(self.start_exam)
        lay.addWidget(start_btn)

        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def start_exam(self):
        self.setup_exam_ui()
        self.exam_active = True
        self.start_time = datetime.now()
        self.detections = []
        self.detection_display.clear()

        settings = self.current_exam_data.get("settings", {})
        if settings.get("duration_enabled"):
            self.remaining_seconds = settings.get("duration", 0) * 60
            self.timer_id.timeout.connect(self.update_timer_label)
            self.timer_id.start(1000)

        if settings.get("show_detections", True):
            self.log_dock.show()
        else:
            self.log_dock.hide()

    def setup_exam_ui(self):
        page = QWidget(); outer_lay = QVBoxLayout(page)
        
        self.timer_lbl = QLabel("Time Remaining: --:--")
        self.timer_lbl.setStyleSheet("font-weight: bold; color: red; font-size: 14px;")
        outer_lay.addWidget(self.timer_lbl)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        content = QWidget(); self.q_container = QVBoxLayout(content)
        self.answer_widgets = []

        for i, q in enumerate(self.current_exam_data["questions"]):
            box = QGroupBox(f"Question {i+1}")
            b_lay = QVBoxLayout(box)
            b_lay.addWidget(QLabel(q["question"]))

            if q["type"] == "mcq":
                grp = QButtonGroup(box)
                self.answer_widgets.append(grp)
                options = q.get("options") or []
                for idx, txt in enumerate(options):
                    rb = QRadioButton(txt)
                    grp.addButton(rb, idx)
                    b_lay.addWidget(rb)
            
            elif q["type"] == "tf":
                grp = QButtonGroup(box)
                self.answer_widgets.append(grp)
                t_rb = QRadioButton("True"); grp.addButton(t_rb, 1)
                f_rb = QRadioButton("False"); grp.addButton(f_rb, 0)
                b_lay.addWidget(t_rb); b_lay.addWidget(f_rb)

            elif q["type"] == "text":
                le = QLineEdit(); le.setPlaceholderText("Answer here...")
                self.answer_widgets.append(le)
                b_lay.addWidget(le)

            self.q_container.addWidget(box)

        scroll.setWidget(content)
        outer_lay.addWidget(scroll)
        outer_lay.addWidget(self.log_dock) 

        submit = QPushButton("SUBMIT EXAM")
        submit.clicked.connect(self.finalize_exam)
        outer_lay.addWidget(submit)

        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def update_timer_label(self):
        if self.remaining_seconds > 0:
            self.remaining_seconds -= 1
            m, s = divmod(self.remaining_seconds, 60)
            self.timer_lbl.setText(f"Time Remaining: {m:02d}:{s:02d}")
        else:
            self.timer_id.stop()
            self.log_cheat_event("Time Expired")
            self.finalize_exam()

    def finalize_exam(self):
        self.exam_active = False
        self.timer_id.stop()
        
        score = 0
        user_answers = []

        for i, q in enumerate(self.current_exam_data["questions"]):
            ans_widget = self.answer_widgets[i]
            is_correct = False
            val = ""

            if q["type"] in ("mcq", "tf"):
                val = ans_widget.checkedId()
                correct_val = q.get("answer_index") if q["type"] == "mcq" else (1 if q.get("correct_tf") else 0)
                if val == correct_val: is_correct = True
            
            elif q["type"] == "text":
                val = ans_widget.text().strip()
                if val.lower() == q.get("answer_text", "").strip().lower(): is_correct = True
            
            user_answers.append(val)
            if is_correct: score += 1

        finish_time = datetime.now()
        duration = (finish_time - self.start_time).total_seconds() if self.start_time else 0
        
        # Prepare the packet to send to the Teacher
        log_packet = {
            "type": "SUBMIT_LOG",
            "exam_name": self.current_exam_data.get("exam_name"),
            "student_name": self.student_name,
            "classname": self.student_class,
            "score": score,
            "detections": self.detections,
            "duration_taken_sec": duration,
            "finished_at": finish_time.strftime("%Y-%m-%d %H:%M:%S")
        }

        # Send the results back to the Teacher's computer
        resp = network_logic.network_request(self.teacher_ip, log_packet)

        msg = "Exam Submitted Successfully!"
        if self.current_exam_data.get("settings", {}).get("show_score", True):
            msg += f"\nScore: {score} / {len(self.current_exam_data['questions'])}"
        
        QMessageBox.information(self, "Finished", msg)
        self.init_dashboard_view() 

    # ===================== CHEAT DETECTION =====================

    def log_cheat_event(self, msg):
        now = datetime.now()
        rel = int((now - self.start_time).total_seconds()) if self.start_time else 0
        event_data = {
            "timestamp_relative_sec": rel,
            "event": msg
        }
        self.detections.append(event_data)
        self.detection_display.append(f"[{rel}s] {msg}")

    def eventFilter(self, obj, event):
        if self.exam_active and event.type() == QEvent.Type.KeyPress:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                key = event.key()
                if key == Qt.Key.Key_C or key == Qt.Key.Key_V:
                    if obj.isWidgetType():
                        action = "Copy" if key == Qt.Key.Key_C else "Paste"
                        self.log_cheat_event(f"{action} action detected")
                        return False 
        return super().eventFilter(obj, event)

    def changeEvent(self, event):
        if self.exam_active and event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                self.log_cheat_event("Window focus lost (Tab Switched)")
        super().changeEvent(event)

    def closeEvent(self, event):
        if self.exam_active:
            res = QMessageBox.question(self, "Quit?", "Exam is in progress. Quit and fail?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if res == QMessageBox.StandardButton.No:
                event.ignore()
                return
        self.portal.show()
        event.accept()