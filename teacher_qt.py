import json
import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QStackedWidget, QListWidget, 
                             QGroupBox, QRadioButton, QButtonGroup, QCheckBox, 
                             QSpinBox, QTextEdit, QComboBox, QTreeWidget, 
                             QTreeWidgetItem, QMessageBox, QFrame, QDialog, QApplication, QGridLayout)
from PyQt6.QtCore import Qt, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor, QFont

NU_BLUE = "#0B2C5D"
NU_HOVER = "#154c9e"

# Unified button appearance (colors may vary per-button)
BUTTON_RADIUS = 8
BUTTON_PADDING = "6px 12px"
BUTTON_FONT_SIZE = 14
def make_btn_style(bg_color, text_color="white"):
    return f"background-color: {bg_color}; color: {text_color}; border-radius: {BUTTON_RADIUS}px; padding: {BUTTON_PADDING}; font-size: {BUTTON_FONT_SIZE}px; font-weight: bold; border: none;"

import socket
import network_logic
from PyQt6.QtCore import QThread
class RequestHandler(QThread):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def run(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', network_logic.TCP_PORT))
        server.listen(5)
        
        while True:
            conn, addr = server.accept()
            try:
                data = conn.recv(1024 * 50).decode('utf-8')
                if not data: continue
                req = json.loads(data)
                resp = {"status": "error"}

                # 1. LOGIN: Scans all rosters
                if req["type"] == "LOGIN":
                    for filename in os.listdir("classes"):
                        if filename.endswith(".json"):
                            with open(f"classes/{filename}", "r", encoding="utf-8") as f:
                                class_data = json.load(f)
                                if any(s['name'] == req['name'] and s['password'] == req['password'] for s in class_data['students']):
                                    resp = {"status": "success", "classname": class_data["classname"]}
                                    break
                        if resp.get("status") == "success": break

                # 2. GET EXAM LIST
                elif req["type"] == "GET_EXAM_LIST":
                    path = f"classes/{req['classname']}.json"
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            resp = {"status": "success", "exams": json.load(f).get("exams", [])}

                # 3. CHECK TAKEN: Verification logic
                elif req["type"] == "CHECK_TAKEN":
                    filename = f"{req['exam_name']}_{req['student_name']}.json"
                    if os.path.exists(f"logs/{filename}"):
                        resp = {"status": "success", "taken": True}
                    else:
                        resp = {"status": "success", "taken": False}

                # 4. GET EXAM: Download content
                elif req["type"] == "GET_EXAM":
                    path = f"exams/{req['exam_name']}.json"
                    if os.path.exists(path):
                        with open(path, "r", encoding="utf-8") as f:
                            resp = {"status": "success", "data": json.load(f)}

                # 5. SUBMIT LOG: Save results
                elif req["type"] == "SUBMIT_LOG":
                    os.makedirs("logs", exist_ok=True)
                    filename = f"{req['exam_name']}_{req['student_name']}.json"
                    with open(f"logs/{filename}", "w", encoding="utf-8") as f:
                        json.dump(req, f, indent=4)
                    resp = {"status": "success"}

                conn.send(json.dumps(resp).encode('utf-8'))
            except: pass
            finally:
                conn.close()
            
class AnimatedBubbleButton(QPushButton):
    def __init__(self, text, parent=None, color=NU_BLUE, radius=25, text_col="white"):
        super().__init__(text, parent)
        self.default_color = color
        self.hover_color = NU_HOVER if color == NU_BLUE else "#c5d9f7"
        self.radius = radius
        self.text_col = text_col
        self.orig_geo = None
        self.setStyleSheet(self._get_style(self.default_color))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._animation = QPropertyAnimation(self, b"geometry")
        self._animation.setDuration(100)
        self._animation.setEasingCurve(QEasingCurve.Type.OutQuad)

    def _get_style(self, bg_color):
        return f"QPushButton {{ background-color: {bg_color}; color: {self.text_col}; border-radius: {self.radius}px; font-size: 15px; font-weight: bold; border: none; }}"

    def enterEvent(self, event):
        if not self.orig_geo: self.orig_geo = self.geometry()
        self.setStyleSheet(self._get_style(self.hover_color))
        self._animation.setEndValue(QRect(self.orig_geo.x() - 8, self.orig_geo.y() - 3, self.orig_geo.width() + 16, self.orig_geo.height() + 6))
        self._animation.start()

    def leaveEvent(self, event):
        self.setStyleSheet(self._get_style(self.default_color))
        if self.orig_geo:
            self._animation.setEndValue(self.orig_geo)
            self._animation.start()

class TeacherWindow(QMainWindow):
    def __init__(self, page_key, portal):
        super().__init__()
        self.portal = portal
        self.setWindowTitle(f"Teacher Panel - {page_key.replace('_', ' ').upper()}")
        self.setFixedSize(900, 600)
        
        os.makedirs("exams", exist_ok=True)
        os.makedirs("classes", exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        self.central = QStackedWidget()
        self.setCentralWidget(self.central)
        
        self.current_questions = []
        self.editing_index = None
        self.current_class_data = {}

        if page_key == "exam": self.setup_exam_builder()
        elif page_key == "logs": self.setup_logs()
        elif page_key == "create_class": self.setup_create_class()
        elif page_key == "manage_class": self.setup_manage_class()

    def setup_exam_builder(self):
        page = QWidget()
        main_layout = QHBoxLayout(page)
        
        # ===================== LEFT COLUMN: INPUT AREA =====================
        left = QVBoxLayout()
        left.setSpacing(10)
        
        left.addWidget(QLabel("<b>Exam Name:</b>"))
        self.ex_name_in = QLineEdit()
        self.ex_name_in.setPlaceholderText("e.g., Midterm Quiz 1")
        left.addWidget(self.ex_name_in)
        
        self.q_edit_label = QLabel("New Question (1)")
        self.q_edit_label.setStyleSheet("color: #0B2C5D; font-weight: bold; font-size: 14px;")
        left.addWidget(self.q_edit_label)
        
        left.addWidget(QLabel("Question Text:"))
        self.q_text_in = QLineEdit()
        left.addWidget(self.q_text_in)
        
        # TYPE SELECTION
        self.type_grp = QButtonGroup(self)
        type_lay = QHBoxLayout()
        for i, t in enumerate(["multiple choice", "text", "tf"]):
            rb = QRadioButton(t.upper())
            self.type_grp.addButton(rb, i)
            type_lay.addWidget(rb)
            if i == 0: rb.setChecked(True)
        left.addLayout(type_lay)
        
        # ANSWER STACK (Fixed height to keep the input area compact)
        self.ans_stack = QStackedWidget()
        self.ans_stack.setFixedHeight(160) 
        
        # 1. MCQ UI (4 vertical rows)
        mcq_w = QWidget(); mcq_v = QVBoxLayout(mcq_w)
        self.mcq_ins = []; self.mcq_sel = QButtonGroup(self)
        for i in range(4):
            opt_hbox = QHBoxLayout()
            rb = QRadioButton(); self.mcq_sel.addButton(rb, i)
            inp = QLineEdit(); inp.setPlaceholderText(f"Option {i+1}")
            self.mcq_ins.append(inp)
            opt_hbox.addWidget(rb); opt_hbox.addWidget(inp)
            mcq_v.addLayout(opt_hbox)
        mcq_v.addStretch()
        self.ans_stack.addWidget(mcq_w)
        
        # 2. TEXT UI
        txt_w = QWidget(); txt_l = QVBoxLayout(txt_w)
        self.txt_ans = QLineEdit(); self.txt_ans.setPlaceholderText("Type correct answer...")
        txt_l.addWidget(self.txt_ans); txt_l.addStretch()
        self.ans_stack.addWidget(txt_w)
        
        # 3. TF UI
        tf_w = QWidget(); tf_l = QVBoxLayout(tf_w)
        tf_h = QHBoxLayout()
        self.tf_sel = QButtonGroup(self)
        t_rb = QRadioButton("TRUE"); f_rb = QRadioButton("FALSE")
        self.tf_sel.addButton(t_rb, 1); self.tf_sel.addButton(f_rb, 0)
        tf_h.addWidget(t_rb); tf_h.addWidget(f_rb); tf_h.addStretch()
        tf_l.addLayout(tf_h); tf_l.addStretch()
        self.ans_stack.addWidget(tf_w)
        
        left.addWidget(self.ans_stack)
        self.type_grp.buttonClicked.connect(lambda: self.ans_stack.setCurrentIndex(self.type_grp.checkedId()))

        # THE SPACER: Pushes buttons below to the bottom
        left.addStretch(1) 

        # ACTION BUTTONS (Stuck to Bottom)
        add_q_btn = AnimatedBubbleButton("ADD / UPDATE QUESTION", color="#28a745")
        add_q_btn.clicked.connect(self.save_question_to_list)
        left.addWidget(add_q_btn)
        
        clear_q_btn = AnimatedBubbleButton("CLEAR CURRENT FIELDS", color="#6c757d")
        clear_q_btn.clicked.connect(self.clear_question_fields)
        left.addWidget(clear_q_btn)

        main_layout.addLayout(left, 2)
        
        # ===================== RIGHT COLUMN: STRETCHED LIST =====================
        right = QVBoxLayout()
        
        right.addWidget(QLabel("<b>Questions List:</b>"))
        self.q_list_disp = QListWidget()
        self.q_list_disp.itemDoubleClicked.connect(self.load_q_for_edit)
        # THE FIX: By default, QListWidget tries to expand. 
        # Adding it to the layout without a spacer below it allows it to stretch.
        right.addWidget(self.q_list_disp, stretch=1) 
        
        # SETTINGS GROUP (Compact)
        settings_box = QGroupBox("Exam Settings")
        set_lay = QVBoxLayout(settings_box)
        
        self.shuf_check = QCheckBox("Shuffle Questions")
        set_lay.addWidget(self.shuf_check)
        
        dur_h = QHBoxLayout()
        self.dur_check = QCheckBox("Limit (mins):")
        self.dur_val = QSpinBox(); self.dur_val.setValue(60)
        dur_h.addWidget(self.dur_check); dur_h.addWidget(self.dur_val)
        set_lay.addLayout(dur_h)
        
        self.detection_check = QCheckBox("Show Detections"); self.detection_check.setChecked(True)
        set_lay.addWidget(self.detection_check)
        self.score_check = QCheckBox("Show Score"); self.score_check.setChecked(True)
        set_lay.addWidget(self.score_check)
        
        right.addWidget(settings_box)

        # BUTTONS AT BOTTOM
        final_save = AnimatedBubbleButton("SAVE FULL EXAM")
        final_save.clicked.connect(self.save_entire_exam)
        right.addWidget(final_save)
        
        reset_exam_btn = AnimatedBubbleButton("RESET FULL EXAM", color="#dc3545")
        reset_exam_btn.clicked.connect(self.reset_full_exam)
        right.addWidget(reset_exam_btn)

        main_layout.addLayout(right, 1)
        self.central.addWidget(page)

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
        
        os.makedirs("exams", exist_ok=True)
        with open(f"exams/{name}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        QMessageBox.information(self, "Success", f"Exam '{name}' Saved Successfully!")
        self.close()

# ===================== 4. ENHANCED LOGS VIEWER =====================
    def setup_logs(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        # 4.1 Filter Header
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Class:"))
        self.log_class_filter = QComboBox()
        # This connection was causing the error - ensure the method name matches exactly
        self.log_class_filter.currentTextChanged.connect(self.on_log_class_selected)
        filter_row.addWidget(self.log_class_filter, 1)

        filter_row.addWidget(QLabel("Exam:"))
        self.log_exam_filter = QComboBox()
        self.log_exam_filter.currentTextChanged.connect(self.refresh_log_tree)
        filter_row.addWidget(self.log_exam_filter, 1)

        self.show_only_taken = QCheckBox("Show Only Completed")
        self.show_only_taken.stateChanged.connect(self.refresh_log_tree)
        filter_row.addWidget(self.show_only_taken)
        
        layout.addLayout(filter_row)

        # 4.2 Main Content Area
        content_split = QHBoxLayout()
        
        self.log_tree = QTreeWidget()
        self.log_tree.setRootIsDecorated(False) # Hides the expansion arrow space
        self.log_tree.setIndentation(0)
        self.log_tree.setHeaderLabels(["Status", "Student", "Score"])
        # Set fixed widths for better alignment
        self.log_tree.setColumnWidth(0, 130)
        self.log_tree.setColumnWidth(1, 150)
        self.log_tree.setFixedWidth(380)
        
        # Use Monospace font for perfect status alignment
        self.log_tree.itemClicked.connect(self.display_log_details)
        content_split.addWidget(self.log_tree)
        
        self.log_detail = QTextEdit()
        self.log_detail.setReadOnly(True)
        self.log_detail.setPlaceholderText("Select a student to view report...")
        content_split.addWidget(self.log_detail)
        
        layout.addLayout(content_split)

        # 4.3 Footer Buttons
        btn_frame = QHBoxLayout()
        
        # NEW: Copy scores button for Excel
        copy_btn = QPushButton("📋 COPY SCORES FOR EXCEL")
        copy_btn.setStyleSheet(make_btn_style("#28a745", "white"))
        copy_btn.clicked.connect(self.copy_scores_to_clipboard)
        btn_frame.addWidget(copy_btn)

        refresh_btn = QPushButton("REFRESH LIST")
        refresh_btn.setStyleSheet(make_btn_style(NU_BLUE, "white"))
        refresh_btn.clicked.connect(self.init_log_filters)
        btn_frame.addWidget(refresh_btn)
        
        back_btn = AnimatedBubbleButton("BACK", color="#E7F0FE", text_col=NU_BLUE, radius=15)
        back_btn.clicked.connect(self.close)
        btn_frame.addWidget(back_btn)
        
        layout.addLayout(btn_frame)
        self.central.addWidget(page)
        self.init_log_filters()

    def init_log_filters(self):
        """Initializes the class filter dropdown"""
        self.log_class_filter.clear()
        if not os.path.exists("classes"): return
        classes = [f[:-5] for f in os.listdir("classes") if f.endswith(".json")]
        if classes:
            self.log_class_filter.addItems(sorted(classes))

    def on_log_class_selected(self, class_name):
        """Updates the exam filter when a class is chosen"""
        self.log_exam_filter.clear()
        path = f"classes/{class_name}.json"
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
        if os.path.exists(f"classes/{c_name}.json"):
            with open(f"classes/{c_name}.json", "r", encoding="utf-8") as f:
                master_students = json.load(f).get("students", [])

        for s_obj in master_students:
            s_name = s_obj["name"]
            log_path = f"logs/{e_name}_{s_name}.json"
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
        
    # ===================== 5. CREATE CLASS (FIXED) =====================
    def setup_create_class(self):
        page = QWidget(); layout = QVBoxLayout(page)
        layout.addWidget(QLabel("<b>CREATE NEW CLASS</b>", alignment=Qt.AlignmentFlag.AlignCenter))
        
        layout.addWidget(QLabel("Class Name:"))
        self.new_class_name = QLineEdit()
        layout.addWidget(self.new_class_name)

        layout.addWidget(QLabel("Paste Student Names & Passwords (Name [TAB] Password):"))
        self.student_input_text = QTextEdit()
        self.student_input_text.setPlaceholderText("John Doe\tpass123\nJane Smith\tpass456")
        layout.addWidget(self.student_input_text)

        save_btn = AnimatedBubbleButton("PROCESS & SAVE CLASS", color="#28a745")
        save_btn.clicked.connect(self.save_new_class)
        layout.addWidget(save_btn)

        back_btn = AnimatedBubbleButton("BACK", color="#E7F0FE", text_col=NU_BLUE)
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)
        self.central.addWidget(page)

    def save_new_class(self):
        name = self.new_class_name.text().strip()
        content = self.student_input_text.toPlainText().strip()
        
        if not name or not content:
            QMessageBox.warning(self, "Error", "Fill in both Class Name and Student Data.")
            return

        students = []
        # 1. Split into a list and remove empty lines immediately
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
                i += 1  # Move to next line
            
            # CASE B: Vertical format (Your specific list)
            # Line i is "adril", Line i+1 is "123"
            else:
                if i + 1 < len(raw_lines):
                    s_name = line
                    s_pass = raw_lines[i+1]
                    students.append({
                        "name": s_name, 
                        "password": s_pass
                    })
                    i += 2  # Jump 2 lines (we used the name and the pass)
                else:
                    # Single name at the end with no password
                    i += 1

        if not students:
            QMessageBox.warning(self, "Error", "Could not detect Name/Password pairs.")
            return

        # Matches your reference structure (classname, students list, exams list)
        data = {
            "classname": name, 
            "students": students, 
            "exams": []
        }
        
        # Save to the classes folder
        os.makedirs("classes", exist_ok=True)
        filepath = f"classes/{name}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        QMessageBox.information(self, "Success", f"Class '{name}' created with {len(students)} students.")
        self.close()

        if not students:
            QMessageBox.warning(self, "Error", "Could not detect Name/Password pairs.")
            return

        # Matches the reference structure
        data = {"classname": name, "students": students, "exams": []}
        
        os.makedirs("classes", exist_ok=True)
        with open(f"classes/{name}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        QMessageBox.information(self, "Success", f"Class '{name}' created with {len(students)} students.")
        self.close()
            
    # ===================== 6. MANAGE CLASS (FIXED) =====================
    def setup_manage_class(self):
        page = QWidget(); layout = QVBoxLayout(page)
        
        # Class Selection Header
        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Select Class:"))
        self.class_picker = QComboBox()
        self.refresh_class_list()
        self.class_picker.currentTextChanged.connect(self.load_selected_class_data)
        top_row.addWidget(self.class_picker, 1)
        layout.addLayout(top_row)

        # Lists Display
        lists_layout = QHBoxLayout()
        
        # Students List
        s_lay = QVBoxLayout(); s_lay.addWidget(QLabel("Students:"))
        self.manage_student_list = QListWidget()
        s_lay.addWidget(self.manage_student_list)
        lists_layout.addLayout(s_lay)

        # Exams List
        e_lay = QVBoxLayout(); e_lay.addWidget(QLabel("Assigned Exams:"))
        self.manage_exam_list = QListWidget()
        e_lay.addWidget(self.manage_exam_list)
        lists_layout.addLayout(e_lay)
        
        layout.addLayout(lists_layout)

        # Management Buttons
        btn_row = QHBoxLayout()
        add_s_btn = AnimatedBubbleButton("Add Students", radius=15); add_s_btn.clicked.connect(self.popup_add_students)
        assign_e_btn = AnimatedBubbleButton("Assign Exam", radius=15); assign_e_btn.clicked.connect(self.popup_assign_exam)
        del_c_btn = AnimatedBubbleButton("Delete Class", color="#dc3545", radius=15); del_c_btn.clicked.connect(self.delete_current_class)
        
        btn_row.addWidget(add_s_btn); btn_row.addWidget(assign_e_btn); btn_row.addWidget(del_c_btn)
        layout.addLayout(btn_row)

        back_btn = AnimatedBubbleButton("BACK", color="#E7F0FE", text_col=NU_BLUE)
        back_btn.clicked.connect(self.close)
        layout.addWidget(back_btn)
        
        self.central.addWidget(page)
        self.load_selected_class_data()

    def refresh_class_list(self):
        self.class_picker.clear()
        classes = [f[:-5] for f in os.listdir("classes") if f.endswith(".json")]
        if not classes: self.class_picker.addItem("No classes found")
        else: self.class_picker.addItems(classes)

    def load_selected_class_data(self):
        c_name = self.class_picker.currentText()
        path = f"classes/{c_name}.json"
        self.manage_student_list.clear()
        self.manage_exam_list.clear()
        
        if os.path.exists(path):
            with open(path, "r") as f:
                self.current_class_data = json.load(f)
                for s in self.current_class_data.get("students", []):
                    self.manage_student_list.addItem(s["name"])
                for e in self.current_class_data.get("exams", []):
                    self.manage_exam_list.addItem(e)

    def popup_add_students(self):
            dialog = QDialog(self)
            dialog.setWindowTitle("Import Students")
            lay = QVBoxLayout(dialog)
            
            # Updated placeholder to guide the user
            text = QTextEdit()
            text.setPlaceholderText("Paste from Excel (Side-by-Side) or Vertical List (Name line, Password line)")
            lay.addWidget(text)
            
            btn = QPushButton("Import")
            btn.setStyleSheet(make_btn_style(NU_BLUE, "white"))
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
                    with open(f"classes/{class_name}.json", "w", encoding="utf-8") as f:
                        json.dump(self.current_class_data, f, indent=4, ensure_ascii=False)
                    
                    QMessageBox.information(dialog, "Success", f"Added {len(new_students)} students.")
                    dialog.accept()
                    self.load_selected_class_data()
                except Exception as e:
                    QMessageBox.critical(dialog, "Save Error", f"Failed to save: {str(e)}")

            btn.clicked.connect(process)
            dialog.exec()

    def popup_assign_exam(self):
        exams = [f[:-5] for f in os.listdir("exams") if f.endswith(".json")]
        if not exams:
            QMessageBox.warning(self, "Error", "No exams found to assign.")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle("Assign Exam")
        lay = QVBoxLayout(dialog); listw = QListWidget(); listw.addItems(exams); lay.addWidget(listw)
        
        def assign():
            exam_name = listw.currentItem().text()
            if exam_name not in self.current_class_data.get("exams", []):
                self.current_class_data.setdefault("exams", []).append(exam_name)
                with open(f"classes/{self.class_picker.currentText()}.json", "w") as f:
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
            os.remove(f"classes/{c_name}.json")
            self.refresh_class_list()
            self.load_selected_class_data()

    def closeEvent(self, event):
        self.portal.show()
        event.accept()