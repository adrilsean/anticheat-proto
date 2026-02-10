import json
import os
import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QStackedWidget, QListWidget, 
                             QGroupBox, QRadioButton, QButtonGroup, QCheckBox, 
                             QSpinBox, QTextEdit, QComboBox, QTreeWidget, 
                             QTreeWidgetItem, QMessageBox, QFrame, QDialog, QApplication, QGridLayout, QTableWidget, QTableWidgetItem, QMenu, QGraphicsDropShadowEffect, QScrollArea)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor, QFont
from PyQt6.QtWidgets import QGraphicsDropShadowEffect

NU_BLUE = "#0B2C5D"
NU_HOVER = "#154c9e"

def get_data_path(subfolder):
    """Get the correct path for data folders (exams, logs, classes) in proctora_data directory"""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller bundle - use current working directory
        base_path = os.getcwd()
    else:
        # Running from source - use script directory
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, 'proctora_data', subfolder)

# Unified button appearance (colors may vary per-button)
BUTTON_RADIUS = 8
BUTTON_PADDING = "6px 12px"
BUTTON_FONT_SIZE = 14
def make_btn_style(bg_color, text_color="white"):
    return f"background-color: {bg_color}; color: {text_color}; border-radius: {BUTTON_RADIUS}px; padding: {BUTTON_PADDING}; font-size: {BUTTON_FONT_SIZE}px; font-weight: bold; border: none; font-family: Poppins;"

import socket
import network_logic
from PyQt6.QtCore import QThread
class RequestHandler(QThread):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.running = True
        self.daemon = True

    def stop(self):
        """Stop the request handler thread"""
        self.running = False

    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', network_logic.TCP_PORT))
        server.listen(5)
        server.settimeout(1)  # Add timeout to allow checking the running flag
        
        while self.running:
            try:
                conn, addr = server.accept()
            except socket.timeout:
                continue
            
            try:
                data = conn.recv(1024 * 50).decode('utf-8')
                if not data: continue
                req = json.loads(data)
                resp = {"status": "error"}

                # 1. LOGIN: Scans all rosters
                if req["type"] == "LOGIN":
                    for filename in os.listdir(get_data_path("classes")):
                        if filename.endswith(".json"):
                            with open(os.path.join(get_data_path("classes"), filename), "r", encoding="utf-8") as f:
                                class_data = json.load(f)
                                if any(s['name'] == req['name'] and s['password'] == req['password'] for s in class_data['students']):
                                    resp = {"status": "success", "classname": class_data["classname"]}
                                    break
                        if resp.get("status") == "success": break

                # 2. GET EXAM LIST
                elif req["type"] == "GET_EXAM_LIST":
                    path = os.path.join(get_data_path("classes"), f"{req['classname']}.json")
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            resp = {"status": "success", "exams": json.load(f).get("exams", [])}

                # 3. CHECK TAKEN: Verification logic
                elif req["type"] == "CHECK_TAKEN":
                    filename = f"{req['exam_name']}_{req['student_name']}.json"
                    if os.path.exists(os.path.join(get_data_path("logs"), filename)):
                        resp = {"status": "success", "taken": True}
                    else:
                        resp = {"status": "success", "taken": False}

                # 4. GET EXAM: Download content
                elif req["type"] == "GET_EXAM":
                    path = os.path.join(get_data_path("exams"), f"{req['exam_name']}.json")
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            resp = {"status": "success", "data": json.load(f)}

                # 5. SUBMIT LOG: Save results
                elif req["type"] == "SUBMIT_LOG":
                    os.makedirs(get_data_path("logs"), exist_ok=True)
                    filename = f"{req['exam_name']}_{req['student_name']}.json"
                    with open(os.path.join(get_data_path("logs"), filename), "w", encoding="utf-8") as f:
                        json.dump(req, f, indent=4)
                    resp = {"status": "success"}

                conn.send(json.dumps(resp).encode('utf-8'))
            except: pass
            finally:
                conn.close()
        
        server.close()
            
class AnimatedBubbleButton(QPushButton):
    def __init__(self, text, parent=None, color=NU_BLUE, radius=25, text_col="white", animate=True):
        super().__init__(text, parent)
        self.default_color = color
        self.hover_color = NU_HOVER if color == NU_BLUE else "#c5d9f7"
        self.radius = radius
        self.text_col = text_col
        self.animate = animate
        self.orig_geo = None
        
        # Add shadow effect for floating appearance
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(8)
        shadow.setXOffset(0)
        shadow.setYOffset(3)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
        
        # Set font to bold
        font = QFont("Poppins", 15, QFont.Weight.Bold)
        self.setFont(font)
        
        self.setStyleSheet(self._get_style(self.default_color))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(100)
        self._animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def _get_style(self, bg_color):
        return f"QPushButton {{ background-color: {bg_color}; color: {self.text_col}; border-radius: {self.radius}px; font-size: 15px; font-weight: bold; border: none; font-family: Poppins; }}"

    def enterEvent(self, event):
        self.setStyleSheet(self._get_style(self.hover_color))
        if self.animate:
            if not self.orig_geo: self.orig_geo = self.geometry()
            self._animation.setEndValue(QRect(self.orig_geo.x() - 8, self.orig_geo.y() - 3, self.orig_geo.width() + 16, self.orig_geo.height() + 6))
            self._animation.start()

    def leaveEvent(self, event):
        self.setStyleSheet(self._get_style(self.default_color))
        if self.animate and self.orig_geo:
            self._animation.setEndValue(self.orig_geo)
            self._animation.start()

class IconSquareButton(QPushButton):
    """Square button with large icon on top and small text below for the teacher menu"""
    def __init__(self, text, icon_char="📋", parent=None, color=NU_BLUE, text_color="white", size=120):
        super().__init__(parent)
        self.default_color = color
        self.hover_color = NU_HOVER if color == NU_BLUE else "#c5d9f7"
        self.text_color = text_color
        self.size = size
        
        # Set fixed square size
        self.setFixedSize(size, size)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Add shadow effect for floating appearance
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 100))
        self.setGraphicsEffect(shadow)
        
        # Create a layout for the button content with separate icon and text
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(1)
        
        # Icon label (large - 32px)
        icon_label = QLabel(icon_char)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_font = QFont("Poppins", 40)
        icon_label.setFont(icon_font)
        icon_label.setStyleSheet(f"color: {self.text_color}; background: transparent; border: none;")
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Text label (small - 8px) - NOW BOLD
        text_label = QLabel(text)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_font = QFont("Poppins", 12)
        text_font.setBold(True)
        text_label.setFont(text_font)
        text_label.setStyleSheet(f"color: {self.text_color}; background: transparent; border: none;")
        text_label.setWordWrap(True)
        layout.addWidget(text_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self._update_style(self.default_color)
    
    def _update_style(self, bg_color):
        """Update button style"""
        style = f"""
            QPushButton {{
                background-color: {bg_color};
                border: none;
                border-radius: 6px;
                padding: 2px;
            }}
            QPushButton:hover {{
                background-color: {self.hover_color};
            }}
        """
        self.setStyleSheet(style)
    
    def enterEvent(self, event):
        self._update_style(self.hover_color)
    
    def leaveEvent(self, event):
        self._update_style(self.default_color)

class TeacherWindow(QWidget):
    def __init__(self, page_key, portal):
        super().__init__(portal)
        self.portal = portal
        self.setFixedSize(900, 600)
        self.setGeometry(0, 0, 900, 600)
        
        os.makedirs(get_data_path("exams"), exist_ok=True)
        os.makedirs(get_data_path("classes"), exist_ok=True)
        os.makedirs(get_data_path("logs"), exist_ok=True)

        self.stack = QStackedWidget()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.stack)
        
        self.current_questions = []
        self.editing_index = None
        self.current_class_data = {}

        if page_key == "exam": self.setup_exam_builder()
        elif page_key == "logs": self.setup_logs()
        elif page_key == "create_class": self.setup_create_class()
        elif page_key == "manage_class": self.setup_manage_class()

    def setup_exam_builder(self):
        page = QWidget()
        page.setStyleSheet("background-color: #F8DD70;")
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(15)
        
        # Header row with back button
        header_row = QWidget()
        header_row.setStyleSheet("background-color: #F8DD70;")
        header_layout = QHBoxLayout(header_row)
        back_btn = AnimatedBubbleButton("← Back", radius=8, animate=False)
        back_btn.setFixedSize(90, 34)
        back_btn.clicked.connect(self.return_to_teacher_menu)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        title = QLabel("Generate Exam")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B2C5D; background-color: #F8DD70;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addStretch()
        placeholder = QWidget()
        placeholder.setFixedSize(90, 34)
        header_layout.addWidget(placeholder)
        header_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(header_row)
        
        # Main content in horizontal layout with container widgets
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        
        # ===================== LEFT COLUMN: INPUT AREA =====================
        left_container = QWidget()
        left_container.setStyleSheet("background-color: #ffffff; border-radius: 6px;")
        left = QVBoxLayout(left_container)
        left.setContentsMargins(15, 15, 15, 15)
        left.setSpacing(12)
        
        # Exam Name - Single Row
        exam_row = QHBoxLayout()
        exam_row.setSpacing(10)
        exam_label = QLabel("<b style='font-size: 13px;'>Exam Name:</b>")
        exam_label.setFixedWidth(100)
        exam_row.addWidget(exam_label)
        self.ex_name_in = QLineEdit()
        self.ex_name_in.setPlaceholderText("e.g., Midterm Quiz 1")
        self.ex_name_in.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; padding: 4px;")
        exam_row.addWidget(self.ex_name_in)
        left.addLayout(exam_row)
        left.addSpacing(10)
        
        self.q_edit_label = QLabel("New Question")
        self.q_edit_label.setStyleSheet("color: #0B2C5D; font-weight: bold; font-size: 13px;")
        left.addWidget(self.q_edit_label)
        
        q_label = QLabel("<b style='font-size: 11px;'>Question Text</b>")
        left.addWidget(q_label)
        self.q_text_in = QLineEdit()
        self.q_text_in.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; padding: 4px;")
        left.addWidget(self.q_text_in)
        left.addSpacing(10)
        
        # TYPE SELECTION
        type_header = QLabel("<b style='font-size: 11px;'>Answer Type</b>")
        left.addWidget(type_header)
        self.type_grp = QButtonGroup(self)
        type_lay = QHBoxLayout()
        type_lay.setSpacing(15)
        for i, t in enumerate(["multiple choice", "text", "true or false"]):
            rb = QRadioButton(t.upper())
            rb_font = QFont("Poppins", 9)
            rb.setFont(rb_font)
            self.type_grp.addButton(rb, i)
            type_lay.addWidget(rb)
            if i == 0: rb.setChecked(True)
        left.addLayout(type_lay)
        left.addSpacing(12)
        
        answers_header = QLabel("<b style='font-size: 11px;'>Correct Answer</b>")
        left.addWidget(answers_header)
        
        # ANSWER STACK (Fixed height to keep the input area compact)
        self.ans_stack = QStackedWidget()
        self.ans_stack.setFixedHeight(160) 
        
        # 1. MCQ UI (4 vertical rows)
        mcq_w = QWidget(); mcq_v = QVBoxLayout(mcq_w)
        mcq_v.setSpacing(6)
        self.mcq_ins = []; self.mcq_sel = QButtonGroup(self)
        for i in range(4):
            opt_hbox = QHBoxLayout()
            opt_hbox.setSpacing(8)
            rb = QRadioButton(); self.mcq_sel.addButton(rb, i)
            inp = QLineEdit(); inp.setPlaceholderText(f"Option {i+1}")
            inp.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; padding: 4px;")
            inp_font = QFont("Poppins", 9)
            inp.setFont(inp_font)
            self.mcq_ins.append(inp)
            opt_hbox.addWidget(rb); opt_hbox.addWidget(inp)
            mcq_v.addLayout(opt_hbox)
        mcq_v.addStretch()
        self.ans_stack.addWidget(mcq_w)
        
        # 2. TEXT UI
        txt_w = QWidget(); txt_l = QVBoxLayout(txt_w)
        self.txt_ans = QLineEdit(); self.txt_ans.setPlaceholderText("Type correct answer...")
        self.txt_ans.setStyleSheet("background-color: #ffffff; border: 1px solid #cccccc; border-radius: 4px; padding: 4px;")
        txt_l.addWidget(self.txt_ans); txt_l.addStretch()
        self.ans_stack.addWidget(txt_w)
        
        # 3. TF UI
        tf_w = QWidget(); tf_l = QVBoxLayout(tf_w)
        self.tf_sel = QButtonGroup(self)
        t_rb = QRadioButton("TRUE"); f_rb = QRadioButton("FALSE")
        self.tf_sel.addButton(t_rb, 1); self.tf_sel.addButton(f_rb, 0)
        tf_l.addWidget(t_rb)
        tf_l.addWidget(f_rb)
        tf_l.addStretch()
        self.ans_stack.addWidget(tf_w)
        
        left.addWidget(self.ans_stack)
        self.type_grp.buttonClicked.connect(lambda: self.ans_stack.setCurrentIndex(self.type_grp.checkedId()))

        # THE SPACER: Pushes buttons below to the bottom
        left.addStretch(1) 

        # ACTION BUTTONS (Stuck to Bottom) - Single Row (Clear left, Add right)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        clear_q_btn = AnimatedBubbleButton("Clear Current Fields", color="#6c757d", radius=8, animate=False)
        clear_q_btn.setMinimumHeight(42)
        clear_q_btn.clicked.connect(self.clear_question_fields)
        btn_row.addWidget(clear_q_btn)
        
        add_q_btn = AnimatedBubbleButton("Add / Update Question", color="#28a745", radius=8, animate=False)
        add_q_btn.setMinimumHeight(42)
        add_q_btn.clicked.connect(self.save_question_to_list)
        btn_row.addWidget(add_q_btn)
        
        left.addLayout(btn_row)

        main_layout.addWidget(left_container, 2)
        
        # ===================== RIGHT COLUMN: STRETCHED LIST =====================
        right_container = QWidget()
        right_container.setStyleSheet("background-color: #ffffff; border-radius: 6px;")
        right = QVBoxLayout(right_container)
        right.setContentsMargins(15, 15, 15, 15)
        right.setSpacing(12)
        
        list_header = QLabel("<b style='font-size: 13px;'>Questions List</b>")
        right.addWidget(list_header)
        self.q_list_disp = QListWidget()
        self.q_list_disp.setStyleSheet("background-color: #ffffff; border-radius: 4px;")
        self.q_list_disp.itemDoubleClicked.connect(self.load_q_for_edit)
        # THE FIX: By default, QListWidget tries to expand. 
        # Adding it to the layout without a spacer below it allows it to stretch.
        right.addWidget(self.q_list_disp, stretch=1) 
        
        # SETTINGS GROUP (Compact)
        settings_box = QGroupBox("Exam Settings")
        settings_box.setStyleSheet("""
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
        """)
        settings_box_font = QFont("Poppins", 11)
        settings_box_font.setBold(True)
        settings_box.setFont(settings_box_font)
        set_lay = QVBoxLayout(settings_box)
        set_lay.setSpacing(8)
        
        self.shuf_check = QCheckBox("Shuffle Questions")
        set_lay.addWidget(self.shuf_check)
        
        dur_h = QHBoxLayout()
        self.dur_check = QCheckBox("Time Limit (minutes):")
        self.dur_val = QSpinBox(); self.dur_val.setValue(60)
        dur_h.addWidget(self.dur_check); dur_h.addWidget(self.dur_val)
        set_lay.addLayout(dur_h)
        
        self.detection_check = QCheckBox("Show Detections"); self.detection_check.setChecked(True)
        set_lay.addWidget(self.detection_check)
        self.score_check = QCheckBox("Show Score"); self.score_check.setChecked(True)
        set_lay.addWidget(self.score_check)
        
        right.addWidget(settings_box)

        # BUTTONS AT BOTTOM
        final_save = AnimatedBubbleButton("Save Full Exam", animate=False, radius=8)
        final_save.setMinimumHeight(42)
        final_save.clicked.connect(self.save_entire_exam)
        right.addWidget(final_save)
        

        main_layout.addWidget(right_container, 1)
        outer_layout.addLayout(main_layout)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    # ================= VALIDATION & LOGIC =================

    def update_indicator(self):
        """Ref 6.1: Show current status"""
        total = len(self.current_questions)
        if self.editing_index is None:
            self.q_edit_label.setText(f"New Question ({total + 1})")
        else:
            self.q_edit_label.setText(f"Editing Question {self.editing_index + 1} / {total}")

    def clear_question_fields(self):
        """Ref 6.3: Reset all input fields"""
        self.q_text_in.clear()
        self.txt_ans.clear()
        
        # Reset MCQ
        for inp in self.mcq_ins:
            inp.clear()
        self.mcq_sel.setExclusive(False)
        for btn in self.mcq_sel.buttons(): btn.setChecked(False)
        self.mcq_sel.setExclusive(True)
        
        # Reset TF
        self.tf_sel.setExclusive(False)
        for btn in self.tf_sel.buttons(): btn.setChecked(False)
        self.tf_sel.setExclusive(True)
        
        self.editing_index = None
        self.update_indicator()

    def save_question_to_list(self):
        """Ref 6.6: Add or Update Question with strict validation"""
        q_text = self.q_text_in.text().strip()
        q_type = ["mcq", "text", "tf"][self.type_grp.checkedId()]
        
        # Validation: Text
        if not q_text:
            QMessageBox.warning(self, "Error", "Enter the question text.")
            return

        q_data = {"question": q_text, "type": q_type}

        # Validation: Type Specific
        if q_type == "mcq":
            choices = [e.text().strip() for e in self.mcq_ins]
            ans = self.mcq_sel.checkedId()
            if any(not c for c in choices) or ans == -1:
                QMessageBox.warning(self, "Error", "Fill all choices and select the correct answer.")
                return
            q_data.update({"options": choices, "answer_index": ans})
        
        elif q_type == "text":
            ans_text = self.txt_ans.text().strip()
            if not ans_text:
                QMessageBox.warning(self, "Error", "Enter the correct answer text.")
                return
            q_data["answer_text"] = ans_text
            
        elif q_type == "tf":
            ans = self.tf_sel.checkedId()
            if ans == -1:
                QMessageBox.warning(self, "Error", "Select True or False.")
                return
            q_data["correct_tf"] = (ans == 1)

        # Save Logic
        if self.editing_index is not None:
            self.current_questions[self.editing_index] = q_data
        else: 
            self.current_questions.append(q_data)

        self.refresh_q_list()
        self.clear_question_fields()

    def refresh_q_list(self):
        """Ref 6.2: Update Listbox"""
        self.q_list_disp.clear()
        for i, q in enumerate(self.current_questions, 1):
            self.q_list_disp.addItem(f"{i}. {q['question'][:40]}...")

    def load_q_for_edit(self, item):
        """Ref 6.4: Load existing data into fields"""
        idx = self.q_list_disp.currentRow()
        self.editing_index = idx
        q = self.current_questions[idx]
        
        self.q_text_in.setText(q["question"])
        type_idx = ["mcq", "text", "tf"].index(q["type"])
        self.type_grp.button(type_idx).setChecked(True)
        self.ans_stack.setCurrentIndex(type_idx)
        
        if q["type"] == "mcq":
            for i, opt in enumerate(q.get("options", [])): 
                self.mcq_ins[i].setText(opt)
            if q.get("answer_index") != -1: 
                self.mcq_sel.button(q["answer_index"]).setChecked(True)
        elif q["type"] == "text": 
            self.txt_ans.setText(q.get("answer_text", ""))
        elif q["type"] == "tf": 
            self.tf_sel.button(1 if q["correct_tf"] else 0).setChecked(True)
        
        self.update_indicator()

    def reset_full_exam(self):
        """Ref 6.8: Clear entire exam data"""
        confirm = QMessageBox.question(self, "Reset", "Clear the entire exam and all questions?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.current_questions.clear()
            self.ex_name_in.clear()
            self.refresh_q_list()
            self.clear_question_fields()

    def save_entire_exam(self):
        name = self.ex_name_in.text().strip()
        if not name or not self.current_questions:
            QMessageBox.warning(self, "Error", "Enter exam name and add at least one question.")
            return
            
        data = {
            "exam_name": name, 
            "questions": self.current_questions,
            "settings": {
                "shuffle": self.shuf_check.isChecked(),
                "duration": self.dur_val.value() if self.dur_check.isChecked() else None,
                "duration_enabled": self.dur_check.isChecked(),
                "show_detections": self.detection_check.isChecked(),
                "show_score": self.score_check.isChecked()
            }
        }
        
        os.makedirs(get_data_path("exams"), exist_ok=True)
        with open(os.path.join(get_data_path("exams"), f"{name}.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        QMessageBox.information(self, "Success", f"Exam '{name}' Saved Successfully!")
        self.return_to_teacher_menu()

# ===================== 4. ENHANCED LOGS VIEWER =====================
    def setup_logs(self):
        page = QWidget()
        page.setStyleSheet("background-color: #F8DD70;")
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(15)
        
        # Header row with back button
        header_row = QWidget()
        header_row.setStyleSheet("background-color: #F8DD70;")
        header_layout = QHBoxLayout(header_row)
        back_btn = AnimatedBubbleButton("← Back", radius=8, animate=False)
        back_btn.setFixedSize(90, 34)
        back_btn.clicked.connect(self.return_to_teacher_menu)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        title = QLabel("View Exam Logs")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B2C5D; background-color: #F8DD70;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addStretch()
        placeholder = QWidget()
        placeholder.setFixedSize(90, 34)
        header_layout.addWidget(placeholder)
        header_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(header_row)
        
        layout = QVBoxLayout()
        
        # 4.1 Filter Header
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Class:"))
        self.log_class_filter = QComboBox()
        self.log_class_filter.setStyleSheet("background-color: #ffffff; border-radius: 4px; padding: 2px;")
        # This connection was causing the error - ensure the method name matches exactly
        self.log_class_filter.currentTextChanged.connect(self.on_log_class_selected)
        filter_row.addWidget(self.log_class_filter, 1)

        filter_row.addWidget(QLabel("Exam:"))
        self.log_exam_filter = QComboBox()
        self.log_exam_filter.setStyleSheet("background-color: #ffffff; border-radius: 4px; padding: 2px;")
        self.log_exam_filter.currentTextChanged.connect(self.refresh_log_tree)
        filter_row.addWidget(self.log_exam_filter, 1)

        self.show_only_taken = QCheckBox("Show Only Completed")
        self.show_only_taken.stateChanged.connect(self.refresh_log_tree)
        filter_row.addWidget(self.show_only_taken)
        
        layout.addLayout(filter_row)

        # 4.2 Main Content Area
        content_split = QHBoxLayout()
        
        self.log_tree = QTreeWidget()
        self.log_tree.setStyleSheet("background-color: #ffffff; border-radius: 4px;")
        self.log_tree.setRootIsDecorated(False) # Hides the expansion arrow space
        self.log_tree.setIndentation(0)
        self.log_tree.setHeaderLabels(["Status", "Student", "Score"])
        # Set fixed widths for better alignment
        self.log_tree.setColumnWidth(0, 130)
        self.log_tree.setColumnWidth(1, 150)
        self.log_tree.setFixedWidth(380)
        
        # Use Monospace font for perfect status alignment
        self.log_tree.itemClicked.connect(self.display_log_details)
        self.log_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.log_tree.customContextMenuRequested.connect(self.on_log_tree_context_menu)
        content_split.addWidget(self.log_tree)
        
        self.log_detail = QTextEdit()
        self.log_detail.setStyleSheet("background-color: #ffffff; border-radius: 4px; padding: 4px;")
        self.log_detail.setReadOnly(True)
        self.log_detail.setPlaceholderText("Select a student to view report...")
        content_split.addWidget(self.log_detail)
        
        layout.addLayout(content_split)

        # 4.3 Footer Buttons
        btn_frame = QHBoxLayout()
        
        # Copy scores button for Excel
        copy_btn = AnimatedBubbleButton("📋 Copy Scores For Excel", color="#28a745", radius=8, animate=False)
        copy_btn.setMinimumHeight(42)
        copy_btn.clicked.connect(self.copy_scores_to_clipboard)
        btn_frame.addWidget(copy_btn)

        refresh_btn = AnimatedBubbleButton("Refresh List", color=NU_BLUE, radius=8, animate=False)
        refresh_btn.setMinimumHeight(42)
        refresh_btn.clicked.connect(self.init_log_filters)
        btn_frame.addWidget(refresh_btn)
        
        layout.addLayout(btn_frame)
        outer_layout.addLayout(layout)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        self.init_log_filters()

    def init_log_filters(self):
        """Initializes the class filter dropdown"""
        self.log_class_filter.clear()
        if not os.path.exists(get_data_path("classes")): return
        classes = [f[:-5] for f in os.listdir(get_data_path("classes")) if f.endswith(".json")]
        if classes:
            self.log_class_filter.addItems(sorted(classes))

    def on_log_class_selected(self, class_name):
        """Updates the exam filter when a class is chosen"""
        self.log_exam_filter.clear()
        path = os.path.join(get_data_path("classes"), f"{class_name}.json")
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                exams = data.get("exams", [])
                self.log_exam_filter.addItems(exams)

    def refresh_log_tree(self):
        """Displays all students in order and highlights status"""
        self.log_tree.clear()
        c_name = self.log_class_filter.currentText()
        e_name = self.log_exam_filter.currentText()
        if not c_name or not e_name: return

        master_students = []
        if os.path.exists(os.path.join(get_data_path("classes"), f"{c_name}.json")):
            with open(os.path.join(get_data_path("classes"), f"{c_name}.json"), "r", encoding="utf-8") as f:
                master_students = json.load(f).get("students", [])

        for s_obj in master_students:
            s_name = s_obj["name"]
            log_path = os.path.join(get_data_path("logs"), f"{e_name}_{s_name}.json")
            log_data = None
            
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    log_data = json.load(f)

            if self.show_only_taken.isChecked() and not log_data:
                continue

            status = "✓ COMPLETED" if log_data else "○ PENDING  "
            score = str(log_data.get("score", "-")) if log_data else "-"
            
            item = QTreeWidgetItem([status, s_name, score])
            item.setTextAlignment(2, Qt.AlignmentFlag.AlignCenter)
            
            if log_data:
                item.setForeground(0, QColor("darkgreen"))
                item.setData(0, Qt.ItemDataRole.UserRole, log_data)
            else:
                item.setForeground(0, QColor("gray"))
            
            self.log_tree.addTopLevelItem(item)

    def copy_scores_to_clipboard(self):
        """Copies only the scores column for easy pasting into an existing Excel column"""
        output = ""
        
        for i in range(self.log_tree.topLevelItemCount()):
            it = self.log_tree.topLevelItem(i)
            # Column index 2 is the 'Score' column in your TreeWidget
            score = it.text(2)
            output += f"{score}\n"
        
        QApplication.clipboard().setText(output)
        QMessageBox.information(self, "Excel Copy", "Scores column copied to clipboard!")

    def display_log_details(self, item):
        self.selected_log_item = item  # Track the selected item for deletion
        d = item.data(0, Qt.ItemDataRole.UserRole)
        if not d:
            self.log_detail.setHtml("<h3 style='color:gray;'>No data submitted yet.</h3>")
            return
        
        # Build Report HTML
        html = f"<h2>Report: {d.get('student_name')}</h2>"
        html += f"<b>Score:</b> {d.get('score')} / {len(d.get('answers', []))}<br/>"
        html += f"<b>Duration:</b> {int(d.get('duration_taken_sec', 0)) // 60}m {int(d.get('duration_taken_sec', 0)) % 60}s<br/>"
        html += "<hr/><b>Anti-Cheat Events:</b><br/>"
        
        for det in d.get("detections", []):
            html += f"<font color='red'>[{det.get('timestamp_relative_sec')}s] {det.get('event')}</font><br/>"
            
        self.log_detail.setHtml(html)
        
    def on_log_tree_context_menu(self, position):
        """Show context menu for log tree right-click"""
        item = self.log_tree.itemAt(position)
        if item is None:
            return
        
        # Check if this item has log data (no data means pending exam)
        log_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not log_data:
            QMessageBox.information(self, "No Attempt", "This student has not attempted the exam yet.")
            return
        
        # Create context menu with proper styling
        context_menu = QMenu(self)
        context_menu.setStyleSheet("QMenu { color: #000000; background-color: #ffffff; } QMenu::item:selected { background-color: #0B2C5D; color: #ffffff; }")
        delete_action = context_menu.addAction("🗑️ Delete This Attempt")
        
        # Show menu and handle selection
        action = context_menu.exec(self.log_tree.mapToGlobal(position))
        if action == delete_action:
            self.delete_exam_attempt(item)

    def delete_exam_attempt(self, item):
        """Delete the exam attempt for a student"""
        student_name = item.text(1)  # Column 1 is Student name
        exam_name = self.log_exam_filter.currentText()
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self, 
            "Delete Exam Attempt", 
            f"Are you sure you want to delete the exam attempt for {student_name}?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm != QMessageBox.StandardButton.Yes:
            return
        
        try:
            # Remove the log file
            log_path = os.path.join(get_data_path("logs"), f"{exam_name}_{student_name}.json")
            if os.path.exists(log_path):
                os.remove(log_path)
            
            # Also remove from class data if it exists
            class_name = self.log_class_filter.currentText()
            class_path = os.path.join(get_data_path("classes"), f"{class_name}.json")
            if os.path.exists(class_path):
                with open(class_path, "r", encoding="utf-8") as f:
                    class_data = json.load(f)
                
                # Find and update the student's exam status
                for student in class_data.get("students", []):
                    if student["name"] == student_name:
                        if "exam_statuses" in student:
                            if exam_name in student["exam_statuses"]:
                                student["exam_statuses"][exam_name] = "pending"
                        break
                
                # Save updated class data
                with open(class_path, "w", encoding="utf-8") as f:
                    json.dump(class_data, f, indent=2, ensure_ascii=False)
            
            # Refresh the log tree
            self.refresh_log_tree()
            self.log_detail.clear()
            
            QMessageBox.information(self, "Success", f"Exam attempt for {student_name} has been deleted.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete exam attempt:\n{str(e)}")
        
        
    # ===================== 5. CREATE CLASS (FIXED) =====================
    def setup_create_class(self):
        page = QWidget()
        page.setStyleSheet("background-color: #F8DD70;")
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(15)
        
        # Header row with back button
        header_row = QWidget()
        header_row.setStyleSheet("background-color: #F8DD70;")
        header_layout = QHBoxLayout(header_row)
        back_btn = AnimatedBubbleButton("← Back", radius=8, animate=False)
        back_btn.setFixedSize(90, 34)
        back_btn.clicked.connect(self.return_to_teacher_menu)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        title = QLabel("Create New Class")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B2C5D; background-color: #F8DD70;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addStretch()
        placeholder = QWidget()
        placeholder.setFixedSize(90, 34)
        header_layout.addWidget(placeholder)
        header_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(header_row)
        
        # Main content: Left (Form) + Right (Preview Table)
        content_layout = QHBoxLayout()
        
        # ===== LEFT SIDE: FORM =====
        layout = QVBoxLayout()        
        layout.addWidget(QLabel("Class Name:"))
        self.new_class_name = QLineEdit()
        self.new_class_name.setStyleSheet("background-color: #ffffff; border-radius: 4px; padding: 6px;")
        layout.addWidget(self.new_class_name)

        layout.addWidget(QLabel("Paste Student Names & Passwords (Name [TAB] Password):"))
        self.student_input_text = QTextEdit()
        self.student_input_text.setPlaceholderText("John Doe\tpass123\nJane Smith\tpass456")
        self.student_input_text.setStyleSheet("background-color: #ffffff; border-radius: 4px; padding: 4px;")
        self.student_input_text.textChanged.connect(self.update_student_preview_table)
        layout.addWidget(self.student_input_text)

        save_btn = AnimatedBubbleButton("Save Class", color="#28a745", animate=False, radius=8)
        save_btn.setMinimumHeight(42)
        save_btn.clicked.connect(self.save_new_class)
        layout.addWidget(save_btn)

        left_widget = QWidget()
        left_widget.setLayout(layout)
        content_layout.addWidget(left_widget, 1)
        
        # ===== RIGHT SIDE: PREVIEW TABLE =====
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("<b>Preview</b>", alignment=Qt.AlignmentFlag.AlignCenter))
        
        self.student_preview_table = QTableWidget()
        self.student_preview_table.setColumnCount(2)
        self.student_preview_table.setHorizontalHeaderLabels(["Username", "Password"])
        self.student_preview_table.setStyleSheet("background-color: #ffffff; border-radius: 4px;")
        self.student_preview_table.horizontalHeader().setStretchLastSection(True)
        self.student_preview_table.setColumnWidth(0, 200)
        right_layout.addWidget(self.student_preview_table)
        
        right_widget = QWidget()
        right_widget.setLayout(right_layout)
        content_layout.addWidget(right_widget, 1)
        
        outer_layout.addLayout(content_layout)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)

    def parse_student_input(self, content):
        """Helper: Parse student input (tab-separated or vertical format)"""
        students = []
        if not content:
            return students
        
        raw_lines = [line.strip() for line in content.splitlines() if line.strip()]
        i = 0
        
        while i < len(raw_lines):
            line = raw_lines[i]
            
            # CASE A: Side-by-Side (Standard Excel Tab format)
            if "\t" in line:
                parts = line.split("\t")
                if len(parts) >= 2:
                    students.append({
                        "name": parts[0].strip(), 
                        "password": parts[1].strip()
                    })
                i += 1
            
            # CASE B: Vertical format (name, then password)
            else:
                if i + 1 < len(raw_lines):
                    students.append({
                        "name": line, 
                        "password": raw_lines[i+1]
                    })
                    i += 2
                else:
                    i += 1
        
        return students

    def update_student_preview_table(self):
        """Parse student input and display in real-time preview table"""
        content = self.student_input_text.toPlainText().strip()
        students = self.parse_student_input(content)
        
        # Update table
        self.student_preview_table.setRowCount(len(students))
        for row, student in enumerate(students):
            username_item = QTableWidgetItem(student.get("name", ""))
            password_item = QTableWidgetItem(student.get("password", ""))
            username_item.setFlags(username_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            password_item.setFlags(password_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.student_preview_table.setItem(row, 0, username_item)
            self.student_preview_table.setItem(row, 1, password_item)

    def save_new_class(self):
        name = self.new_class_name.text().strip()
        content = self.student_input_text.toPlainText().strip()
        
        if not name or not content:
            QMessageBox.warning(self, "Error", "Fill in both Class Name and Student Data.")
            return

        students = self.parse_student_input(content)
        
        if not students:
            QMessageBox.warning(self, "Error", "Could not detect Name/Password pairs.")
            return

        data = {
            "classname": name, 
            "students": students, 
            "exams": []
        }
        
        os.makedirs(get_data_path("classes"), exist_ok=True)
        filepath = os.path.join(get_data_path("classes"), f"{name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        QMessageBox.information(self, "Success", f"Class '{name}' created with {len(students)} students.")
        self.return_to_teacher_menu()
            
    # ===================== 6. MANAGE CLASS (FIXED) =====================
    def setup_manage_class(self):
        page = QWidget()
        page.setStyleSheet("background-color: #F8DD70;")
        outer_layout = QVBoxLayout(page)
        outer_layout.setContentsMargins(20, 20, 20, 20)
        outer_layout.setSpacing(15)
        
        # Header row with back button
        header_row = QWidget()
        header_row.setStyleSheet("background-color: #F8DD70;")
        header_layout = QHBoxLayout(header_row)
        back_btn = AnimatedBubbleButton("← Back", radius=8, animate=False)
        back_btn.setFixedSize(90, 34)
        back_btn.clicked.connect(self.return_to_teacher_menu)
        header_layout.addWidget(back_btn)
        header_layout.addStretch()
        title = QLabel("Manage Classes")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #0B2C5D; background-color: #F8DD70;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)
        header_layout.addStretch()
        placeholder = QWidget()
        placeholder.setFixedSize(90, 34)
        header_layout.addWidget(placeholder)
        header_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(header_row)
        
        # Main content layout - Left (2 columns) and Right (1 column)
        main_content = QHBoxLayout()
        
        # ===== LEFT SIDE: Class Selection, Students, Assigned Exams =====
        left_container = QVBoxLayout()
        
        # Class Selection Header
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Select Class:"))
        self.class_picker = QComboBox()
        self.class_picker.setStyleSheet("background-color: #ffffff; border-radius: 4px; padding: 2px;")
        self.refresh_class_list()
        self.class_picker.currentTextChanged.connect(self.load_selected_class_data)
        top_row.addWidget(self.class_picker, 1)
        left_container.addLayout(top_row)

        # Lists Display (2 columns)
        lists_layout = QHBoxLayout()
        
        # Students List (Table with Name and Password columns) - BIGGEST
        s_lay = QVBoxLayout(); s_lay.addWidget(QLabel("Students:"))
        self.manage_student_list = QTableWidget()
        self.manage_student_list.setColumnCount(2)
        self.manage_student_list.setHorizontalHeaderLabels(["Name", "Password"])
        self.manage_student_list.setStyleSheet("background-color: #ffffff; border-radius: 4px;")
        self.manage_student_list.horizontalHeader().setStretchLastSection(True)
        self.manage_student_list.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.manage_student_list.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        s_lay.addWidget(self.manage_student_list)
        lists_layout.addLayout(s_lay, 2)

        # Assigned Exams List - SAME WIDTH AS AVAILABLE
        e_lay = QVBoxLayout(); e_lay.addWidget(QLabel("Assigned Exams:"))
        self.manage_exam_container = QWidget()
        self.manage_exam_layout = QVBoxLayout(self.manage_exam_container)
        self.manage_exam_layout.setContentsMargins(0, 0, 0, 0)
        self.manage_exam_layout.setSpacing(4)
        
        exam_scroll_area = QScrollArea()
        exam_scroll_area.setWidget(self.manage_exam_container)
        exam_scroll_area.setWidgetResizable(True)
        exam_scroll_area.setStyleSheet("background-color: #ffffff; border-radius: 4px;")
        e_lay.addWidget(exam_scroll_area)
        lists_layout.addLayout(e_lay, 1)
        
        left_container.addLayout(lists_layout)
        
        # Management Buttons (only for left-side actions: Add Students, Delete Class)
        btn_row = QHBoxLayout()
        add_s_btn = AnimatedBubbleButton("Add Students", radius=8, animate=False); add_s_btn.clicked.connect(self.popup_add_students)
        add_s_btn.setMinimumHeight(42)
        del_c_btn = AnimatedBubbleButton("Delete Class", color="#dc3545", radius=8, animate=False); del_c_btn.clicked.connect(self.delete_current_class)
        del_c_btn.setMinimumHeight(42)
        
        btn_row.addWidget(add_s_btn); btn_row.addWidget(del_c_btn)
        left_container.addLayout(btn_row)
        
        main_content.addLayout(left_container, 3)
        
        # ===== RIGHT SIDE: Available Exams with Assign Buttons - SAME WIDTH AS ASSIGNED =====
        a_lay = QVBoxLayout()
        avail_label = QLabel("Available Exams:")
        avail_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #0B2C5D;")
        a_lay.addWidget(avail_label)
        self.available_exams_container = QWidget()
        self.available_exams_layout = QVBoxLayout(self.available_exams_container)
        self.available_exams_layout.setContentsMargins(0, 0, 0, 0)
        self.available_exams_layout.setSpacing(6)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.available_exams_container)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: #ffffff; border-radius: 4px;")
        a_lay.addWidget(scroll_area)
        main_content.addLayout(a_lay, 1)
        
        outer_layout.addLayout(main_content)
        
        # Populate available exams on first load
        self.refresh_available_exams()
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        self.load_selected_class_data()

    def refresh_class_list(self):
        self.class_picker.clear()
        classes_dir = get_data_path("classes")
        if not os.path.exists(classes_dir):
            self.class_picker.addItem("No classes found")
        else:
            classes = [f[:-5] for f in os.listdir(classes_dir) if f.endswith(".json")]
            if not classes:
                self.class_picker.addItem("No classes found")
            else:
                self.class_picker.addItems(classes)

    def load_selected_class_data(self):
        c_name = self.class_picker.currentText()
        path = os.path.join(get_data_path("classes"), f"{c_name}.json")
        self.manage_student_list.setRowCount(0)
        
        # Clear assigned exams layout
        while self.manage_exam_layout.count():
            item = self.manage_exam_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        if os.path.exists(path):
            with open(path, "r") as f:
                self.current_class_data = json.load(f)
                students = self.current_class_data.get("students", [])
                self.manage_student_list.setRowCount(len(students))
                for row, s in enumerate(students):
                    name_item = QTableWidgetItem(s["name"])
                    password_item = QTableWidgetItem(s.get("password", "N/A"))
                    self.manage_student_list.setItem(row, 0, name_item)
                    self.manage_student_list.setItem(row, 1, password_item)
                
                for e in self.current_class_data.get("exams", []):
                    self.add_assigned_exam_row(e)
        
        # Add stretch to push items to top
        self.manage_exam_layout.addStretch()
        
        # Refresh the available exams list
        self.refresh_available_exams()
    
    def add_assigned_exam_row(self, exam_name):
        """Add an assigned exam with a delete button"""
        exam_row = QHBoxLayout()
        exam_row.setContentsMargins(6, 4, 6, 4)
        exam_row.setSpacing(8)
        
        # Exam name label
        exam_label = QLabel(exam_name)
        exam_label.setStyleSheet("color: #0B2C5D; font-weight: 500;")
        exam_row.addWidget(exam_label, 1)
        
        # Delete button (X)
        del_btn = AnimatedBubbleButton("✕", color="#dc3545", radius=6, animate=False)
        del_btn.setFixedSize(32, 28)
        del_btn.setToolTip(f"Delete exam '{exam_name}' from class")
        del_btn.clicked.connect(lambda checked, e=exam_name: self.unassign_exam(e))
        exam_row.addWidget(del_btn)
        
        # Create a container widget for the row
        row_widget = QWidget()
        row_widget.setLayout(exam_row)
        row_widget.setStyleSheet("background-color: #f0f0f0; border-radius: 4px; padding: 2px;")
        
        self.manage_exam_layout.addWidget(row_widget)

    def popup_add_students(self):
            dialog = QDialog(self)
            dialog.setWindowTitle("Import Students")
            lay = QVBoxLayout(dialog)
            
            # Updated placeholder to guide the user
            text = QTextEdit()
            text.setStyleSheet("background-color: #ffffff; border-radius: 4px; padding: 4px;")
            text.setPlaceholderText("Paste from Excel (Side-by-Side) or Vertical List (Name line, Password line)")
            lay.addWidget(text)
            
            btn = QPushButton("Import")
            btn.setStyleSheet(make_btn_style(NU_BLUE, "white") + " border-radius: 8px;")
            lay.addWidget(btn)
            
            def process():
                content = text.toPlainText().strip()
                if not content:
                    return
                
                # 1. Clean up the input: remove blank lines and extra spaces
                raw_lines = [line.strip() for line in content.splitlines() if line.strip()]
                new_students = []
                
                i = 0
                while i < len(raw_lines):
                    line = raw_lines[i]
                    
                    # CASE A: Standard Excel Tab (Side-by-Side)
                    if "\t" in line:
                        parts = line.split("\t")
                        if len(parts) >= 2:
                            new_students.append({
                                "name": parts[0].strip(), 
                                "password": parts[1].strip()
                            })
                        i += 1  # Move to next line
                    
                    # CASE B: Your Vertical Format (Name line followed by Password line)
                    else:
                        if i + 1 < len(raw_lines):
                            s_name = line
                            s_pass = raw_lines[i+1]
                            new_students.append({
                                "name": s_name, 
                                "password": s_pass
                            })
                            i += 2  # Jump 2 lines (used both Name and Pass)
                        else:
                            # Skip a single trailing line with no pair
                            i += 1

                if not new_students:
                    QMessageBox.warning(dialog, "Error", "No valid Name/Password pairs detected.")
                    return

                # Add to the current class data
                self.current_class_data["students"].extend(new_students)
                
                # Save back to the JSON file
                class_name = self.class_picker.currentText()
                try:
                    with open(os.path.join(get_data_path("classes"), f"{class_name}.json"), "w", encoding="utf-8") as f:
                        json.dump(self.current_class_data, f, indent=4, ensure_ascii=False)
                    
                    QMessageBox.information(dialog, "Success", f"Added {len(new_students)} students.")
                    dialog.accept()
                    self.load_selected_class_data()
                except Exception as e:
                    QMessageBox.critical(dialog, "Save Error", f"Failed to save: {str(e)}")

            btn.clicked.connect(process)
            dialog.exec()

    def popup_assign_exam(self):
        exams = [f[:-5] for f in os.listdir(get_data_path("exams")) if f.endswith(".json")]
        if not exams:
            QMessageBox.warning(self, "Error", "No exams found to assign.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Assign Exam")
        lay = QVBoxLayout(dialog); listw = QListWidget(); listw.setStyleSheet("background-color: #ffffff; border-radius: 4px;"); listw.addItems(exams); lay.addWidget(listw)
        
        def assign():
            exam_name = listw.currentItem().text()
            if exam_name not in self.current_class_data.get("exams", []):
                self.current_class_data.setdefault("exams", []).append(exam_name)
                with open(os.path.join(get_data_path("classes"), f"{self.class_picker.currentText()}.json"), "w") as f:
                    json.dump(self.current_class_data, f, indent=4)
                self.load_selected_class_data()
            dialog.accept()

        listw.itemDoubleClicked.connect(assign)
        dialog.exec()

    def delete_current_class(self):
        c_name = self.class_picker.currentText()
        if c_name == "No classes found": return
        
        ans = QMessageBox.question(self, "Confirm", f"Delete class '{c_name}'?")
        if ans == QMessageBox.StandardButton.Yes:
            os.remove(os.path.join(get_data_path("classes"), f"{c_name}.json"))
            self.refresh_class_list()
            self.load_selected_class_data()



    def unassign_exam(self, exam_name):
        """Remove an exam from the class"""
        if exam_name in self.current_class_data.get("exams", []):
            self.current_class_data["exams"].remove(exam_name)
            
            try:
                class_name = self.class_picker.currentText()
                if class_name != "No classes found":
                    with open(os.path.join(get_data_path("classes"), f"{class_name}.json"), "w", encoding="utf-8") as f:
                        json.dump(self.current_class_data, f, indent=4, ensure_ascii=False)
                    
                    QMessageBox.information(self, "Success", f"Exam '{exam_name}' unassigned successfully!")
                    self.load_selected_class_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to unassign exam: {str(e)}")

    def refresh_available_exams(self):
        """Load all available exams and display them with assign buttons"""
        # Clear the layout
        while self.available_exams_layout.count():
            item = self.available_exams_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        
        # Get all exams from the exams folder
        if not os.path.exists(get_data_path("exams")):
            os.makedirs(get_data_path("exams"), exist_ok=True)
        
        exams = sorted([f[:-5] for f in os.listdir(get_data_path("exams")) if f.endswith(".json")])
        
        if not exams:
            no_exams_label = QLabel("No exams available")
            no_exams_label.setStyleSheet("color: #999999; font-style: italic;")
            self.available_exams_layout.addWidget(no_exams_label)
        else:
            for exam_name in exams:
                # Create a horizontal layout for each exam row
                exam_row = QHBoxLayout()
                exam_row.setContentsMargins(6, 4, 6, 4)
                exam_row.setSpacing(6)
                
                # Exam name label
                exam_label = QLabel(exam_name)
                exam_label.setStyleSheet("color: #0B2C5D; font-weight: 500;")
                exam_row.addWidget(exam_label, 1)
                
                # Assign button (simple +)
                assign_btn = AnimatedBubbleButton("+", color="#28a745", radius=6, animate=False)
                assign_btn.setFixedSize(36, 28)
                assign_btn.setToolTip(f"Assign exam '{exam_name}' to class")
                assign_btn.clicked.connect(lambda checked, e=exam_name: self.assign_exam_from_available(e))
                exam_row.addWidget(assign_btn)
                
                # Delete button
                del_btn = AnimatedBubbleButton("🗑", color="#dc3545", radius=6, animate=False)
                del_btn.setFixedSize(36, 28)
                del_btn.setToolTip(f"Delete exam '{exam_name}'")
                del_btn.clicked.connect(lambda checked, e=exam_name: self.delete_exam(e))
                exam_row.addWidget(del_btn)
                
                # Create a container widget for the row
                row_widget = QWidget()
                row_widget.setLayout(exam_row)
                row_widget.setStyleSheet("background-color: #f0f0f0; border-radius: 4px; padding: 2px;")
                
                self.available_exams_layout.addWidget(row_widget)
        
        # Add stretch at the bottom to push items to the top
        self.available_exams_layout.addStretch()

    def assign_exam_from_available(self, exam_name):
        """Assign an exam to the current class"""
        class_name = self.class_picker.currentText()
        if class_name == "No classes found":
            QMessageBox.warning(self, "Error", "Please select a valid class first.")
            return
        
        if exam_name in self.current_class_data.get("exams", []):
            QMessageBox.information(self, "Info", f"Exam '{exam_name}' is already assigned to this class.")
            return
        
        try:
            self.current_class_data.setdefault("exams", []).append(exam_name)
            with open(os.path.join(get_data_path("classes"), f"{class_name}.json"), "w", encoding="utf-8") as f:
                json.dump(self.current_class_data, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Success", f"Exam '{exam_name}' assigned successfully!")
            self.load_selected_class_data()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to assign exam: {str(e)}")

    def delete_exam(self, exam_name):
        """Delete an exam file permanently"""
        ans = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to permanently delete the exam '{exam_name}'?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if ans == QMessageBox.StandardButton.Yes:
            try:
                exam_path = os.path.join(get_data_path("exams"), f"{exam_name}.json")
                if os.path.exists(exam_path):
                    os.remove(exam_path)
                    QMessageBox.information(self, "Success", f"Exam '{exam_name}' deleted successfully!")
                    self.refresh_available_exams()
                    # Also refresh the assign exam dialog if it's open
                    self.load_selected_class_data()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete exam: {str(e)}")

    def return_to_teacher_menu(self):
        """Return to main portal and show the teacher menu page"""
        try:
            self.portal.show_teacher_page()
        except Exception:
            try:
                self.portal.show()
            except Exception:
                pass

    def closeEvent(self, event):
        self.portal.show()
        event.accept()