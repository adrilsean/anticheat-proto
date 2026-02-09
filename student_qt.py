import sys, os, json, random
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QFont

class StudentWindow(QMainWindow):
    def __init__(self, name, password, portal):
        super().__init__()
        # 1. State Variables
        self.portal = portal
        self.student_name = name
        self.student_class = "Unknown"
        self.student_classes_data = [] 
        
        self.exam_active = False
        self.current_exam_data = {}
        self.answer_widgets = []
        self.detections = []
        self.start_time = None
        self.timer_id = QTimer()
        self.remaining_seconds = 0

        # 2. UI Setup
        self.setWindowTitle("Proctora Student Portal")
        self.setFixedSize(900, 600)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Build shared Detection Log
        self.init_detection_log_ui()
        
        # 3. Logic Initialization
        self.perform_login_logic(name, password)

        # 4. CRITICAL FIX: Install Global Event Filter
        # This allows the window to catch keystrokes even if a QLineEdit is focused.
        QApplication.instance().installEventFilter(self)

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

    def perform_login_logic(self, name, password):
        if not os.path.exists("classes"): os.makedirs("classes")
        
        found = False
        for f in os.listdir("classes"):
            if f.endswith(".json"):
                with open(f"classes/{f}", "r", encoding="utf-8") as file:
                    data = json.load(file)
                    for s in data.get("students", []):
                        if s["name"] == name and s["password"] == password:
                            self.student_classes_data.append((data["classname"], data.get("exams", [])))
                            found = True
        
        if found:
            self.init_dashboard_view()
        else:
            QMessageBox.warning(self, "Login Error", "No student record found or invalid password.")
            QTimer.singleShot(0, self.close)

    def get_taken_exams(self):
        taken = set()
        if os.path.exists("logs"):
            for f in os.listdir("logs"):
                if f.endswith(".json"):
                    with open(f"logs/{f}", "r", encoding="utf-8") as file:
                        log = json.load(file)
                        if log.get("student_name") == self.student_name:
                            taken.add(log.get("exam_name"))
        return taken

    # ===================== VIEWS =====================

    def init_dashboard_view(self):
        page = QWidget(); lay = QVBoxLayout(page)
        
        header = QLabel(f"Welcome, {self.student_name}")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B2C5D;")
        lay.addWidget(header)

        lay.addWidget(QLabel("Select Class:"))
        self.class_combo = QComboBox()
        for cname, _ in self.student_classes_data:
            self.class_combo.addItem(cname)
        self.class_combo.currentIndexChanged.connect(self.refresh_exam_list)
        lay.addWidget(self.class_combo)

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
        self.exam_table.setRowCount(0)
        taken_exams = self.get_taken_exams()
        
        selected_class = self.class_combo.currentText()
        exams = []
        for cname, ex_list in self.student_classes_data:
            if cname == selected_class:
                exams = ex_list
                self.student_class = cname
                break

        for ex in exams:
            ex_name = ex[:-5] if ex.endswith(".json") else ex
            row = self.exam_table.rowCount()
            self.exam_table.insertRow(row)
            
            name_item = QTableWidgetItem(ex_name)
            name_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
            
            status_text = "COMPLETED" if ex_name in taken_exams else "AVAILABLE"
            status_item = QTableWidgetItem(status_text)
            status_item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)

            if status_text == "COMPLETED":
                status_item.setForeground(Qt.GlobalColor.red)
            else:
                status_item.setForeground(Qt.GlobalColor.darkGreen)

            self.exam_table.setItem(row, 0, name_item)
            self.exam_table.setItem(row, 1, status_item)

    # ===================== EXAM LOGIC =====================

    def check_and_load_exam(self):
        row = self.exam_table.currentRow()
        if row == -1: return
        
        ex_name = self.exam_table.item(row, 0).text()
        status = self.exam_table.item(row, 1).text()

        if status == "COMPLETED":
            QMessageBox.information(self, "Already Taken", "You have already submitted this exam.")
            return

        path = f"exams/{ex_name}.json"
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                self.current_exam_data = json.load(f)
            
            if self.current_exam_data.get("settings", {}).get("shuffle"):
                random.shuffle(self.current_exam_data["questions"])
            
            self.setup_welcome_screen(ex_name)
        else:
            QMessageBox.critical(self, "Error", "Exam file not found.")

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
                options = q.get("options") or q.get("choices") or []
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
        wrong_indices = []
        user_answers = []

        for i, q in enumerate(self.current_exam_data["questions"]):
            ans_widget = self.answer_widgets[i]
            is_correct = False
            val = ""

            if q["type"] in ("mcq", "tf"):
                val = ans_widget.checkedId()
                correct_val = q.get("answer") if q.get("answer") is not None else q.get("answer_index")
                if val == correct_val: is_correct = True
            
            elif q["type"] == "text":
                val = ans_widget.text().strip()
                if val.lower() == q.get("answer_text", "").strip().lower(): is_correct = True
            
            user_answers.append(val)
            if is_correct: score += 1
            else: wrong_indices.append(i + 1)

        finish_time = datetime.now()
        duration = (finish_time - self.start_time).total_seconds() if self.start_time else 0
        
        log_packet = {
            "exam_name": self.current_exam_data.get("exam_name"),
            "student_name": self.student_name,
            "class_name": self.student_class,
            "answers": user_answers,
            "wrong_questions": wrong_indices,
            "score": score,
            "detections": self.detections,
            "started_at": self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else "",
            "finished_at": finish_time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_taken_sec": duration
        }

        os.makedirs("logs", exist_ok=True)
        filename = f"{self.current_exam_data.get('exam_name')}_{self.student_name}.json"
        with open(f"logs/{filename}", "w", encoding="utf-8") as f:
            json.dump(log_packet, f, indent=4)

        show_score = self.current_exam_data.get("settings", {}).get("show_score", True)
        msg = "Exam Submitted Successfully!"
        if show_score:
            msg += f"\nScore: {score} / {len(self.current_exam_data['questions'])}"
        
        QMessageBox.information(self, "Finished", msg)
        self.init_dashboard_view() 

    # ===================== CHEAT DETECTION =====================

    def log_cheat_event(self, msg):
        now = datetime.now()
        rel = int((now - self.start_time).total_seconds()) if self.start_time else 0
        event_data = {
            "timestamp_earth": now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp_relative_sec": rel,
            "event": msg
        }
        self.detections.append(event_data)
        self.detection_display.append(f"[{rel}s] {msg}")

    def eventFilter(self, obj, event):
        # 1. Check if an exam is actually running
        if self.exam_active and event.type() == QEvent.Type.KeyPress:
            
            # 2. Check for the Control Key
            # We use bitwise '&' to detect Ctrl even if other keys (like CapsLock) are on
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                
                key = event.key()
                # 3. Detect C (Copy) or V (Paste)
                if key == Qt.Key.Key_C or key == Qt.Key.Key_V:
                    
                    # We only log if the object is a 'Window' or 'Input' type 
                    # to prevent the "double logging" you saw earlier.
                    if obj.isWidgetType():
                        action = "Copy" if key == Qt.Key.Key_C else "Paste"
                        self.log_cheat_event(f"{action} action detected")
                        
                        # Return False so the actual Copy/Paste still works 
                        # (Change to True if you want to BLOCK the cheating)
                        return False 
        
        # Pass all other events back to the system
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