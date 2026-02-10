import sys, os, json, random
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import Qt, QTimer, QEvent
from PyQt6.QtGui import QFont, QBrush, QColor

# Import the shared networking module
import network_logic

# Button style helper to match teacher UI
BUTTON_RADIUS = 8
BUTTON_PADDING = "6px 12px"
BUTTON_FONT_SIZE = 14
def make_btn_style(bg_color, text_color="white"):
    return f"background-color: {bg_color}; color: {text_color}; border-radius: {BUTTON_RADIUS}px; padding: {BUTTON_PADDING}; font-size: {BUTTON_FONT_SIZE}px; font-weight: bold; border: none;"

class StudentWindow(QWidget):
    def __init__(self, name, teacher_ip, portal, classname):
        super().__init__(portal)
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

        # 2. UI Setup (embedded widget)
        self.setFixedSize(900, 600)
        self.setGeometry(0, 0, 900, 600)
        self.stack = QStackedWidget()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)
        self.init_detection_log_ui()

        # 3. Enter Dashboard
        self.init_dashboard_view()
        QApplication.instance().installEventFilter(self)

    def __del__(self):
        try:
            QApplication.instance().removeEventFilter(self)
        except Exception:
            pass

    def refresh_exam_list(self):
        """Fetch exam list and CHECK each one's status from the teacher"""
        self.exam_table.setRowCount(0)
        
        # 1. Get the list of exams
        resp = network_logic.network_request(self.teacher_ip, {
            "type": "GET_EXAM_LIST", "classname": self.student_class
        })
        
        if resp.get("status") == "success":
            for ex_name in resp.get("exams", []):
                row = self.exam_table.rowCount()
                self.exam_table.insertRow(row)
                
                # 2. Ask the teacher if THIS student has taken THIS exam
                status_resp = network_logic.network_request(self.teacher_ip, {
                    "type": "CHECK_TAKEN", 
                    "exam_name": ex_name, 
                    "student_name": self.student_name
                })
                
                is_taken = status_resp.get("taken", False)
                status_text = "COMPLETED" if is_taken else "AVAILABLE"
                
                name_item = QTableWidgetItem(ex_name)
                status_item = QTableWidgetItem(status_text)
                
                # Style the status with background color for visibility
                if is_taken:
                    status_item.setBackground(QBrush(QColor("#ffebee")))  # Light red background
                    status_item.setForeground(QBrush(QColor("#c62828")))  # Dark red text
                else:
                    status_item.setBackground(QBrush(QColor("#e8f5e9")))  # Light green background
                    status_item.setForeground(QBrush(QColor("#2e7d32")))  # Dark green text
                    
                self.exam_table.setItem(row, 0, name_item)
                self.exam_table.setItem(row, 1, status_item)

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
                background-color: #ffffff; 
                color: #d32f2f;
                border: 1px solid #cccccc;
                padding: 5px;
            }
        """)
        layout.addWidget(self.detection_display)
        self.log_dock.hide()

    # ===================== VIEWS =====================

    def init_dashboard_view(self):
        page = QWidget()
        page.setStyleSheet("background-color: #F8DD70;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        # Top row with back button and header
        top_row = QWidget()
        top_row.setStyleSheet("background-color: #F8DD70;")
        top_layout = QHBoxLayout(top_row)
        back_btn = QPushButton("← Home")
        back_btn.setFixedSize(90, 34)
        back_btn.setStyleSheet("background-color: #0B2C5D; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px;")
        back_btn.clicked.connect(self.return_to_portal)

        # Layout: back button | stretch | centered header | stretch | placeholder
        # The placeholder matches the back button size so the header remains centered
        top_layout.addWidget(back_btn)
        top_layout.addStretch()

        header = QLabel(f"Welcome, {self.student_name}")
        header.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B2C5D; background-color: #F8DD70;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(header)
        top_layout.addStretch()

        placeholder = QWidget()
        placeholder.setFixedSize(90, 34)
        top_layout.addWidget(placeholder)

        top_layout.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(top_row)

        # Display the class assigned by the teacher
        class_info = QLabel(f"Current Class: <b>{self.student_class}</b>")
        class_info.setStyleSheet("font-size: 14px; color: #0B2C5D; background-color: #F8DD70;")
        lay.addWidget(class_info)

        exams_label = QLabel("Assigned Exams (Double-click to start):")
        exams_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0B2C5D; background-color: #F8DD70;")
        lay.addWidget(exams_label)

        self.exam_table = QTableWidget(0, 2)
        self.exam_table.setHorizontalHeaderLabels(["Exam Name", "Status"])
        self.exam_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.exam_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.exam_table.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #e8e8e8;
                color: #000000;
                padding: 4px;
                border: 1px solid #cccccc;
            }
            QTableCornerButton::section {
                background-color: #e8e8e8;
            }
        """)
        self.exam_table.setAlternatingRowColors(True)
        self.exam_table.itemDoubleClicked.connect(self.check_and_load_exam)
        lay.addWidget(self.exam_table)

        start_btn = QPushButton("START SELECTED EXAM")
        start_btn.setFixedHeight(50)
        start_btn.setStyleSheet(make_btn_style("#0B2C5D", "white") + " font-size: 14px;")
        start_btn.clicked.connect(self.check_and_load_exam)
        lay.addWidget(start_btn)

        self.refresh_exam_list()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def return_to_portal(self):
        """Return to portal, clean up this student widget, and show login page."""
        # Stop any active exam timers
        try:
            self.timer_id.stop()
        except Exception:
            pass
        
        self.hide()
        try:
            # Clear the reference in portal and show opening page
            self.portal.s_win = None
            self.portal.show_opening_page()
            self.portal.show()
        except Exception:
            try:
                self.portal.show()
            except Exception:
                pass

    def check_and_load_exam(self):
        """Block entry if the exam is already marked as completed"""
        row = self.exam_table.currentRow()
        if row == -1: return
        
        ex_name = self.exam_table.item(row, 0).text()
        status = self.exam_table.item(row, 1).text()

        # Safety Check: Source of Truth verification
        if status == "COMPLETED":
            QMessageBox.warning(self, "Access Denied", "You have already submitted this exam.")
            return

        # Proceed to download if available
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
        page = QWidget()
        page.setStyleSheet("background-color: #F8DD70;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)
        
        # Header row with back button (centered title)
        header_row = QWidget()
        header_row.setStyleSheet("background-color: #F8DD70;")
        header_layout = QHBoxLayout(header_row)
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(90, 34)
        back_btn.setStyleSheet("background-color: #0B2C5D; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px;")
        back_btn.clicked.connect(self.init_dashboard_view)
        
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        
        title = QLabel(f"Exam: {name}")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #0B2C5D;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        placeholder = QWidget()
        placeholder.setFixedSize(90, 34)
        header_layout.addWidget(placeholder)
        header_layout.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(header_row)
        
        # Add spacing
        lay.addSpacing(30)
        
        # Info box (rules and details) - centered and larger
        info_container = QWidget()
        info_container_layout = QHBoxLayout(info_container)
        info_container_layout.addStretch()
        
        info_box = QGroupBox()
        info_box.setStyleSheet("""
            QGroupBox {
                color: #0B2C5D;
                font-weight: bold;
                font-size: 16px;
                border: 3px solid #0B2C5D;
                border-radius: 6px;
                padding: 15px 20px 20px 20px;
                background-color: #ffffff;
            }
            QLabel {
                background-color: #ffffff;
                color: #333;
            }
        """)
        info_box.setFixedWidth(600)
        info_layout = QVBoxLayout(info_box)
        info_layout.setSpacing(15)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        settings = self.current_exam_data.get("settings", {})
        rules_text = "• Anti-cheat system is active\n• Tab switching will be logged\n• Copy/Paste actions are monitored"
        if settings.get("duration_enabled"):
            rules_text += f"\n• Time Limit: {settings.get('duration')} minutes"
        
        rules_lbl = QLabel(rules_text)
        rules_lbl.setStyleSheet("background-color: #ffffff; color: #333; font-size: 16px; line-height: 1.8; font-weight: normal;")
        rules_lbl.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(rules_lbl)
        
        info_container_layout.addWidget(info_box)
        info_container_layout.addStretch()
        info_container_layout.setContentsMargins(0, 0, 0, 0)
        
        lay.addWidget(info_container)
        
        # Add stretch for spacing
        lay.addStretch()
        
        # Begin button (centered)
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.addStretch()
        
        start_btn = QPushButton("BEGIN EXAM")
        start_btn.setFixedSize(240, 60)
        start_btn.setStyleSheet(make_btn_style("#0B2C5D", "white") + "font-size: 16px;")
        start_btn.clicked.connect(self.start_exam)
        btn_layout.addWidget(start_btn)
        
        btn_layout.addStretch()
        btn_layout.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(btn_container)

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
        page = QWidget()
        page.setStyleSheet("background-color: #F8DD70;")
        outer_lay = QVBoxLayout(page)
        outer_lay.setContentsMargins(20, 20, 20, 20)
        outer_lay.setSpacing(15)
        
        # Header row with back button and title
        header_row = QWidget()
        header_row.setStyleSheet("background-color: #F8DD70;")
        header_layout = QHBoxLayout(header_row)
        back_btn = QPushButton("← Back")
        back_btn.setFixedSize(90, 34)
        back_btn.setStyleSheet("background-color: #0B2C5D; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 12px;")
        back_btn.clicked.connect(self.return_to_portal)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        title = QLabel("Exam In Progress")
        title.setStyleSheet("font-size: 26px; font-weight: bold; color: #0B2C5D; background-color: #F8DD70;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addStretch()
        placeholder = QWidget()
        placeholder.setFixedSize(90, 34)
        header_layout.addWidget(placeholder)
        header_layout.setContentsMargins(0, 0, 0, 0)
        outer_lay.addWidget(header_row)
        
        # Timer label
        self.timer_lbl = QLabel("Time Remaining: --:--")
        self.timer_lbl.setStyleSheet("font-weight: bold; color: #dc3545; font-size: 16px; background-color: #F8DD70;")
        outer_lay.addWidget(self.timer_lbl)

        # Scroll area for questions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: #F8DD70; border: none; }")
        content = QWidget()
        content.setStyleSheet("background-color: #F8DD70;")
        self.q_container = QVBoxLayout(content)
        self.q_container.setSpacing(15)
        self.answer_widgets = []

        for i, q in enumerate(self.current_exam_data["questions"]):
            box = QWidget()
            box.setStyleSheet("""
                QWidget {
                    background-color: #fffbe6;
                    border: 2px solid #0B2C5D;
                    border-radius: 6px;
                    padding: 10px;
                }
            """)
            b_lay = QVBoxLayout(box)
            b_lay.setContentsMargins(10, 10, 10, 10)
            
            q_label = QLabel(f"<b>Question {i+1}:</b> {q['question']}")
            q_label.setStyleSheet("background-color: #fffbe6; color: #0B2C5D; font-size: 15px; font-weight: normal; border: none;")
            q_label.setWordWrap(True)
            b_lay.addWidget(q_label)

            if q["type"] == "mcq":
                grp = QButtonGroup(box)
                self.answer_widgets.append(grp)
                options = q.get("options") or []
                for idx, txt in enumerate(options):
                    rb = QRadioButton(txt)
                    rb.setStyleSheet("background-color: #fffbe6; color: #0B2C5D; font-size: 14px; border: none;")
                    grp.addButton(rb, idx)
                    b_lay.addWidget(rb)
            
            elif q["type"] == "tf":
                grp = QButtonGroup(box)
                self.answer_widgets.append(grp)
                t_rb = QRadioButton("True")
                t_rb.setStyleSheet("background-color: #fffbe6; color: #0B2C5D; font-size: 14px; border: none;")
                grp.addButton(t_rb, 1)
                f_rb = QRadioButton("False")
                f_rb.setStyleSheet("background-color: #fffbe6; color: #0B2C5D; font-size: 14px; border: none;")
                grp.addButton(f_rb, 0)
                b_lay.addWidget(t_rb)
                b_lay.addWidget(f_rb)

            elif q["type"] == "text":
                le = QLineEdit()
                le.setPlaceholderText("Answer here...")
                le.setStyleSheet("background-color: #ffffff; color: #0B2C5D; font-size: 14px; border: 1px solid #0B2C5D; border-radius: 4px; padding: 6px;")
                self.answer_widgets.append(le)
                b_lay.addWidget(le)

            self.q_container.addWidget(box)

        scroll.setWidget(content)
        outer_lay.addWidget(scroll)
        outer_lay.addWidget(self.log_dock) 

        # Submit button
        submit = QPushButton("SUBMIT EXAM")
        submit.setStyleSheet(make_btn_style("#28a745", "white") + "font-size: 16px; padding: 10px;")
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

   

    def eventFilter(self, obj, event):
        """Unified Cheat Detection: Handles Alt-Tab and Copy/Paste without duplicates"""
        if self.exam_active:
            
            # 1. DETECT TAB SWITCHING (Global Application Focus Loss)
            if event.type() == QEvent.Type.ApplicationDeactivate:
                self.log_cheat_event("Window focus lost (Alt+Tab / Tab Switched)")
                return False

            # 2. DETECT COPY/PASTE KEYSTROKES
            if event.type() == QEvent.Type.KeyPress:
                # FIX 1: Ignore auto-repeat (stops logging if key is held down)
                if event.isAutoRepeat():
                    return False

                if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                    key = event.key()
                    if key in (Qt.Key.Key_C, Qt.Key.Key_V):
                        
                        # FIX 2: Only log if the target object is a widget 
                        # This prevents the "Application" and "Widget" from both logging the same press.
                        if obj.isWidgetType():
                            action = "Copy" if key == Qt.Key.Key_C else "Paste"
                            self.log_cheat_event(f"{action} action detected")
                        
                        return False # Return True here if you want to BLOCK the actual copy/paste
                        
        return super().eventFilter(obj, event)

    # REMOVED: changeEvent (It was causing duplicate logs with the logic above)

    def log_cheat_event(self, msg):
        now = datetime.now()
        rel = int((now - self.start_time).total_seconds()) if self.start_time else 0
        event_data = {
            "timestamp_relative_sec": rel,
            "event": msg
        }
        self.detections.append(event_data)
        self.detection_display.append(f"[{rel}s] {msg}")

    # ... [keep finalize_exam, start_exam, setup_exam_ui, update_timer_label as they are] ...

    def closeEvent(self, event):
        if self.exam_active:
            res = QMessageBox.question(self, "Quit?", "Exam is in progress. Quit and fail?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if res == QMessageBox.StandardButton.No:
                event.ignore()
                return
        try:
            QApplication.instance().quit()
        except Exception:
            event.accept()