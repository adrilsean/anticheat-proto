import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
from datetime import datetime
import random

def student_app():
    root = tk.Tk()
    root.title("Exam System - Student")
    root.geometry("800x600")
    root.resizable(False, False)

    os.makedirs("exams", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    # ===================== GLOBAL VARS =====================
    student_name = ""
    student_class = ""
    current_exam = {}
    student_classes = []
    answer_vars = []
    detection_events = []
    exam_settings = {}
    timer_id = None
    remaining_seconds = 0
    exam_start_time = None

    # ===================== DETECTION LOG =====================
    detection_frame = tk.Frame(root, bd=1, relief="sunken")
    detection_frame.pack(side="bottom", fill="x")

    tk.Label(detection_frame, text="Detection Log (Prototype)", font=("Arial", 9, "bold")).pack(anchor="w")
    detection_box = tk.Text(detection_frame, height=5, font=("Courier", 9), state="disabled")
    detection_box.pack(fill="x")

    def show_detection(msg):
        nonlocal exam_start_time
        now = datetime.now()
        ts_relative = 0
        if exam_start_time:
            ts_relative = int((now - exam_start_time).total_seconds())  # seconds into exam
        ts_earth = now.strftime("%Y-%m-%d %H:%M:%S")

        detection_box.config(state="normal")
        detection_box.insert("end", f"[{ts_relative}s] {msg}\n")
        detection_box.see("end")
        detection_box.config(state="disabled")

        detection_events.append({
            "timestamp_earth": ts_earth,
            "timestamp_relative_sec": ts_relative,
            "event": msg
        })

    # --- GLOBAL COPY/PASTE DETECTION ---
    def detect_copy_paste(event):
        keysym = event.keysym.lower()
        if keysym == "c":
            show_detection("Copy detected")
        elif keysym == "v":
            show_detection("Paste detected")
        return None

    root.bind_all("<Control-c>", detect_copy_paste)
    root.bind_all("<Control-v>", detect_copy_paste)
    root.bind_all("<Shift-Insert>", lambda e: show_detection("Paste detected"))

    # ===================== FOCUS DETECTION =====================
    last_focus = True
    def check_focus():
        nonlocal last_focus
        if not root.focus_displayof():
            if last_focus:
                show_detection("Window focus lost")
                last_focus = False
        else:
            last_focus = True
        root.after(300, check_focus)

    check_focus()
    
    def get_taken_exams(student_name):
        taken_exams = set()
        for log_file in os.listdir("logs"):
            if log_file.endswith(".json"):
                with open(f"logs/{log_file}", "r", encoding="utf-8") as f:
                    log_data = json.load(f)
                    if log_data.get("student_name") == student_name:
                        taken_exams.add(log_data.get("exam_name"))
        return taken_exams

    # ===================== FRAMES =====================
    login_frame = tk.Frame(root)
    list_frame = tk.Frame(root)
    welcome_frame = tk.Frame(root)
    exam_frame = tk.Frame(root)
    summary_frame = tk.Frame(root)

    def clear_frames():
        for f in (login_frame, list_frame, welcome_frame, exam_frame, summary_frame):
            f.pack_forget()
            for w in f.winfo_children():
                w.destroy()

    # ------------------- STUDENT LOGIN -------------------
    clear_frames()
    login_frame.pack(fill="both", expand=True)

    tk.Label(login_frame, text="Student Login", font=("Arial", 14, "bold")).pack(pady=20)

    tk.Label(login_frame, text="Student Name:", font=("Arial", 12)).pack(pady=(10,2))
    name_entry = tk.Entry(login_frame, font=("Arial", 12), width=30)
    name_entry.pack()

    tk.Label(login_frame, text="Password:", font=("Arial", 12)).pack(pady=(10,2))
    password_entry = tk.Entry(login_frame, font=("Arial", 12), show="*", width=30)
    password_entry.pack()

    # ------------------- EXAM DASHBOARD -------------------
    def show_exam_dashboard(student_name, student_classes):
        clear_frames()
        list_frame.pack(fill="both", expand=True)

        tk.Label(list_frame, text=f"Welcome {student_name}", font=("Arial", 14, "bold")).pack(pady=10)
        tk.Label(list_frame, text="Select your class:", font=("Arial", 12)).pack(pady=5)

        class_var = tk.StringVar()
        class_options = [c[0] for c in student_classes]  # class names
        class_dropdown = ttk.Combobox(list_frame, textvariable=class_var, values=class_options, state="readonly")
        class_dropdown.pack(pady=5)
        class_dropdown.current(0)

        # Treeview for assigned exams
        tree = ttk.Treeview(list_frame, columns=("exam",), height=10, show="tree")
        tree.pack(pady=10, fill="x")

        tree.tag_configure("taken", background="lightgray", foreground="red")
        tree.tag_configure("available", background="white", foreground="green")

        taken_exams = get_taken_exams(student_name)

        def update_exam_list(*args):
            # Clear existing rows
            for item in tree.get_children():
                tree.delete(item)

            # Get selected class and its exams
            selected_class = class_var.get()
            for classname, exams in student_classes:
                if classname == selected_class:
                    for exam in exams:
                        exam_name = exam[:-5] if exam.endswith(".json") else exam
                        display_text = f"{exam_name}  ({classname})"
                        if exam_name in taken_exams:
                            tree.insert("", tk.END, text=display_text, tags=("taken",))
                        else:
                            tree.insert("", tk.END, text=display_text, tags=("available",))
                    break

        # Update exams whenever dropdown changes
        class_var.trace_add("write", update_exam_list)
        update_exam_list()  # initialize list

        # Double-click to load exam
        def load_selected_exam(event):
            selected = tree.focus()
            if not selected:
                return
            exam_display = tree.item(selected, "text")
            exam_name = exam_display.split("  (")[0]

            if exam_name in taken_exams:
                messagebox.showinfo("Exam Already Taken", "You have already taken this exam!")
                return

            load_exam(exam_name)

        tree.bind("<Double-1>", load_selected_exam)

    # ------------------- LOGIN FUNCTION -------------------
    def submit_login():
        nonlocal student_name
        name_input = name_entry.get().strip()
        password_input = password_entry.get().strip()

        if not name_input or not password_input:
            messagebox.showerror("Error", "Both fields are required.")
            return

        # Find all classes this student belongs to
        for class_file in os.listdir("classes"):
            if class_file.endswith(".json"):
                with open(f"classes/{class_file}", "r", encoding="utf-8") as f:
                    class_data = json.load(f)
                for s in class_data.get("students", []):
                    if s["name"] == name_input:
                        student_classes.append((class_data["classname"], class_data.get("exams", [])))

        if not student_classes:
            messagebox.showerror("Error", "Invalid name or password.")
            return

        student_name = name_input
        show_exam_dashboard(student_name, student_classes)  # show dashboard immediately

    tk.Button(login_frame, text="Login", width=20, command=submit_login).pack(pady=20)

    # ===================== LOAD EXAM =====================
    def load_exam(exam_name):
        nonlocal current_exam, answer_vars, detection_events, exam_settings
        with open(f"exams/{exam_name}.json", "r", encoding="utf-8") as f:
            current_exam = json.load(f)

        exam_settings = current_exam.get("settings", {})
        duration = exam_settings.get("duration", 0)
        enable_duration = exam_settings.get("duration_enabled", False)
        shuffle_questions = exam_settings.get("shuffle", False)
        show_detection_flag = exam_settings.get("show_detections", True)
        show_score_flag = exam_settings.get("show_score", True)

        if shuffle_questions:
            random.shuffle(current_exam["questions"])

        # Prepare answer variables
        answer_vars.clear()
        for q in current_exam["questions"]:
            if q.get("type") in ("mcq", "tf"):
                answer_vars.append(tk.IntVar(value=-1))
            else:  # text
                answer_vars.append(tk.StringVar(value=""))

        detection_events.clear()
        clear_frames()
        welcome_frame.pack(fill="both", expand=True)

        tk.Label(welcome_frame, text=f"Exam: {exam_name}", font=("Arial", 14, "bold")).pack(pady=20)

        info_text = "⚠ Anti-cheat enabled\n- Window switching\n- Copy / Paste"
        if enable_duration and duration > 0:
            info_text += f"\n⏱ Time Limit: {duration} minutes"
        tk.Label(welcome_frame, text=info_text, font=("Arial", 12), justify="left").pack(pady=10)

        # Show/hide detection log
        if show_detection_flag:
            detection_frame.pack(side="bottom", fill="x")
        else:
            detection_frame.pack_forget()

        tk.Button(welcome_frame, text="Start Exam", width=20, command=show_exam).pack(pady=20)

        # Save flags for exam screen
        welcome_frame.show_score_flag = show_score_flag
        welcome_frame.enable_duration = enable_duration

    # ===================== SHOW EXAM =====================
    def show_exam():
        nonlocal remaining_seconds, timer_id, exam_start_time
        clear_frames()
        exam_frame.pack(fill="both", expand=True)

        # Record start time (Earth time)
        exam_start_time = datetime.now()

        duration = exam_settings.get("duration", 0)
        enable_duration = exam_settings.get("duration_enabled", False)
        remaining_seconds = duration * 60 if enable_duration else 0

        # Timer label and countdown (only visual)
        timer_label = None
        if enable_duration and duration > 0:
            timer_label = tk.Label(exam_frame, text=f"Time Left: {duration:02d}:00", font=("Arial", 12, "bold"))
            timer_label.pack(pady=5)

        def countdown():
            nonlocal remaining_seconds, timer_label, timer_id
            if timer_label and timer_label.winfo_exists():
                if remaining_seconds > 0:
                    mins, secs = divmod(remaining_seconds, 60)
                    timer_label.config(text=f"Time Left: {mins:02d}:{secs:02d}")
                    remaining_seconds -= 1
                    timer_id = root.after(1000, countdown)
                else:
                    show_detection("Time's up!")
                    finish_exam()

        if enable_duration and duration > 0:
            countdown()

        # --- Exam Questions ---
        canvas = tk.Canvas(exam_frame)
        scrollbar = tk.Scrollbar(exam_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * int(event.delta / 120), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        content = tk.Frame(canvas)
        canvas.create_window((400, 0), window=content, anchor="n")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        for qi, q in enumerate(current_exam["questions"]):
            q_block = tk.Frame(content)
            q_block.pack(pady=15, fill="x")

            tk.Label(
                q_block,
                text=f"{qi + 1}. {q['question']}",
                font=("Arial", 12, "bold"),
                wraplength=700,
                justify="left"
            ).pack(anchor="w")

            if q.get("type") == "mcq":
                for ci, choice in enumerate(q["choices"]):
                    tk.Radiobutton(
                        q_block,
                        text=choice,
                        variable=answer_vars[qi],
                        value=ci,
                        wraplength=680,
                        justify="left"
                    ).pack(anchor="w", padx=20)
            elif q.get("type") == "tf":
                tk.Radiobutton(q_block, text="True", variable=answer_vars[qi], value=1).pack(anchor="w", padx=20)
                tk.Radiobutton(q_block, text="False", variable=answer_vars[qi], value=0).pack(anchor="w", padx=20)
            elif q.get("type") == "text":
                ans_entry = tk.Entry(q_block, width=50, textvariable=answer_vars[qi])
                ans_entry.pack(anchor="w", padx=20)

        tk.Button(content, text="Finish Exam", width=25, command=finish_exam).pack(pady=30)

    # ===================== FINISH & SUMMARY =====================
    def finish_exam():
        nonlocal timer_id, exam_start_time
        if timer_id:
            root.after_cancel(timer_id)
            timer_id = None
        show_summary()

    def show_summary():
        clear_frames()
        summary_frame.pack(fill="both", expand=True)

        score = 0
        wrong = []
        answers = []

        for i, q in enumerate(current_exam["questions"]):
            var = answer_vars[i]
            a = var.get() if isinstance(var, (tk.IntVar, tk.StringVar)) else None
            if isinstance(var, tk.StringVar):
                a = a.strip()
            answers.append(a)

            if isinstance(a, int) and a == q.get("answer"):
                score += 1
            elif isinstance(a, str) and a == q.get("answer_text", ""):
                score += 1
            else:
                wrong.append(i + 1)

        finished_at = datetime.now()
        duration_taken = (finished_at - exam_start_time).total_seconds() if exam_start_time else 0

        log_data = {
            "exam_name": current_exam["exam_name"],
            "student_name": student_name,
            "class_name": student_class,
            "answers": answers,
            "wrong_questions": wrong,
            "score": score,
            "detections": detection_events,
            "started_at": exam_start_time.strftime("%Y-%m-%d %H:%M:%S") if exam_start_time else None,
            "finished_at": finished_at.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_taken_sec": duration_taken
        }

        with open(f"logs/{current_exam['exam_name']}_{student_name}.json", "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=4)

        # Show score if teacher enabled
        if getattr(welcome_frame, "show_score_flag", True):
            tk.Label(
                summary_frame,
                text=f"Exam Finished\nScore: {score} / {len(current_exam['questions'])}",
                font=("Arial", 14, "bold")
            ).pack(pady=40)
        else:
            tk.Label(summary_frame, text="Exam Finished", font=("Arial", 14, "bold")).pack(pady=40)

        tk.Button(
            summary_frame,
            text="Back to Exams",
            width=20,
            command=lambda: show_exam_dashboard(student_name, student_classes)
        ).pack()

    root.mainloop()