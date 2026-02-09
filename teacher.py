import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

def teacher_app():
    # 1. SETUP - Initialize directories and root window
    os.makedirs("exams", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    root = tk.Tk()
    root.title("Teacher Panel")
    root.geometry("700x600")

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)

    # 2. FRAME DECLARATIONS - Create five main frames for different screens
    landing_frame = tk.Frame(main_frame)
    landing_frame.pack(fill="both", expand=True)
    exam_frame = tk.Frame(main_frame)
    logs_frame = tk.Frame(main_frame)
    create_class_frame = tk.Frame(main_frame)
    manage_class_frame = tk.Frame(main_frame)

    # ===================== LANDING SCREEN =====================
    # 3. LANDING FRAME - Main menu with navigation buttons
    tk.Label(landing_frame, text="Teacher Options", font=("Arial", 14, "bold")).pack(pady=20)
    tk.Button(landing_frame, text="Generate Exam", width=20,
              command=lambda: [landing_frame.pack_forget(), exam_frame.pack(fill="both", expand=True), init_exam_frame()]).pack(pady=5)
    tk.Button(landing_frame, text="View Exam Logs", width=20,
              command=lambda: [landing_frame.pack_forget(), logs_frame.pack(fill="both", expand=True), init_logs_frame()]).pack(pady=5)
    tk.Button(landing_frame, text="Create New Class", width=25,
         command=lambda:[landing_frame.pack_forget(), create_class_frame.pack(fill="both", expand=True), init_create_class_frame()]).pack(pady=5)
    tk.Button(landing_frame, text="Manage Classes", width=25,
         command=lambda: [landing_frame.pack_forget(), manage_class_frame.pack(fill="both", expand=True), init_manage_class_frame()]).pack(pady=5)
    
    # ===================== MANAGE CLASS FRAME =====================
    # 4. MANAGE CLASS SCREEN - Edit classes, add students, assign exams, delete classes
    def init_manage_class_frame():
        """Initialize manage class interface with class selection and student/exam management"""
        os.makedirs("classes", exist_ok=True)
        os.makedirs("exams", exist_ok=True)

        # 4.1 CLEAR WIDGETS - Destroy existing widgets in frame
        for widget in manage_class_frame.winfo_children():    
            widget.destroy()
            
        # 4.2 TOP FRAME - Back button
        top_frame = tk.Frame(manage_class_frame)
        top_frame.pack(fill="x", pady=5)
        tk.Button(top_frame, text="Back", command=lambda: [manage_class_frame.pack_forget(), landing_frame.pack(fill="both", expand=True)]).pack(side="left", padx=10)

        # 4.3 CLASS SELECTION - Dropdown to select class
        tk.Label(manage_class_frame, text="Select Class", font=("Arial", 12, "bold")).pack(pady=5)

        class_var = tk.StringVar()
        class_files = [f[:-5] if f.endswith(".json") else f for f in os.listdir("classes")]

        if not class_files:
            class_files = ["No classes available"]

        class_var.set(class_files[0])  # default selection
        class_dropdown = tk.OptionMenu(manage_class_frame, class_var, *class_files)
        class_dropdown.pack()

        # 4.4 MIDDLE SPLIT FRAME - Students and assigned exams side by side
        middle_frame = tk.Frame(manage_class_frame)
        middle_frame.pack(fill="both", expand=True, pady=10, padx=10)

        # Left: Students listbox
        student_frame = tk.Frame(middle_frame)
        student_frame.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(student_frame, text="Students", font=("Arial", 12, "bold")).pack()
        student_listbox = tk.Listbox(student_frame, width=30)
        student_listbox.pack(fill="both", expand=True)

        # Right: Assigned exams listbox
        assigned_exam_frame = tk.Frame(middle_frame)
        assigned_exam_frame.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(assigned_exam_frame, text="Assigned Exams", font=("Arial", 12, "bold")).pack()
        exam_listbox = tk.Listbox(assigned_exam_frame, width=30)
        exam_listbox.pack(fill="both", expand=True)

        current_class_data = {}

        # 4.5 LOAD CLASS - Populate students and exams when class is selected
        def load_class(*args):
            """Load class data and populate listboxes"""
            nonlocal current_class_data
            filename = f"classes/{class_var.get()}.json"
            if not os.path.exists(filename):
                return
            with open(filename, "r", encoding="utf-8") as f:
                current_class_data = json.load(f)

            # Populate student list
            student_listbox.delete(0, tk.END)
            for s in current_class_data.get("students", []):
                student_listbox.insert(tk.END, s["name"])

            # Populate exam list
            exam_listbox.delete(0, tk.END)
            for e in current_class_data.get("exams", []):
                exam_name = e[:-5] if e.endswith(".json") else e
                exam_listbox.insert(tk.END, exam_name)

        class_var.trace("w", load_class)

        # 4.6 ADD STUDENTS - Import new students from text input
        def add_students():
            """Open popup to import students via paste"""
            if not class_var.get() or class_var.get() == "No classes available":
                messagebox.showerror("Error", "Select a valid class first.")
                return

            popup = tk.Toplevel(root)
            popup.title("Import Students")
            popup.geometry("500x600")

            tk.Label(popup, text="Paste students (Name\tPassword)", font=("Arial", 12, "bold")).pack(pady=5)
            text = tk.Text(popup, wrap="none")
            text.pack(fill="both", expand=True, padx=10, pady=(0,5))

            button_frame = tk.Frame(popup)
            button_frame.pack(side="bottom", pady=5)

            # 4.6.1 PROCESS IMPORT - Parse and add new students
            def process_import():
                """Parse student data and add to class"""
                content = text.get("1.0", tk.END).strip()
                if not content:
                    messagebox.showerror("Error", "Paste student data first.")
                    return

                existing_names = {s["name"] for s in current_class_data.get("students", [])}
                new_students = []
                duplicates = []

                for line in content.splitlines():
                    parts = line.split("\t")
                    if len(parts) != 2:
                        continue
                    name, password = parts
                    name = name.strip()
                    if name in existing_names:
                        duplicates.append(name)
                        continue
                    new_students.append({"name": name, "password": password.strip()})
                    existing_names.add(name)

                if not new_students:
                    messagebox.showerror("Error", "No new valid students to add.")
                    return

                # Append students to class data
                current_class_data.setdefault("students", []).extend(new_students)

                # Save class file
                filepath = f"classes/{class_var.get()}.json"
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(current_class_data, f, indent=4, ensure_ascii=False)

                msg = f"{len(new_students)} students added!"
                if duplicates:
                    msg += f"\nSkipped duplicates: {', '.join(duplicates)}"
                messagebox.showinfo("Saved", msg)
                popup.destroy()
                load_class()

            tk.Button(button_frame, text="Process", font=("Arial", 12, "bold"), width=15, command=process_import).pack()

        # 4.7 ASSIGN EXAM - Assign exam to class via double-click
        def assign_exam():
            """Open popup to select and assign exam to class"""
            if not class_var.get() or class_var.get() == "No classes available":
                messagebox.showerror("Error", "Select a valid class first.")
                return

            exams_files = [f for f in os.listdir("exams") if f.endswith(".json")]
            if not exams_files:
                messagebox.showwarning("No Exams", "No exams available to assign.")
                return

            popup = tk.Toplevel(root)
            popup.title("Assign Exam")
            popup.geometry("300x400")

            tk.Label(
                popup,
                text="Double-click an exam to assign",
                font=("Arial", 12, "bold")
            ).pack(pady=5)

            exam_listbox_popup = tk.Listbox(popup)
            exam_listbox_popup.pack(fill="both", expand=True, padx=10, pady=10)

            # Show exams without .json extension
            for exam in exams_files:
                exam_listbox_popup.insert(tk.END, exam[:-5])

            # 4.7.1 ON DOUBLE CLICK - Handle exam assignment
            def on_double_click(event):
                """Assign selected exam to class"""
                selected_idx = exam_listbox_popup.curselection()
                if not selected_idx:
                    return

                exam_name = exam_listbox_popup.get(selected_idx[0])

                current_class_data.setdefault("exams", [])

                if exam_name not in current_class_data["exams"]:
                    current_class_data["exams"].append(exam_name)

                    # Save class file
                    filepath = f"classes/{class_var.get()}.json"
                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(current_class_data, f, indent=4, ensure_ascii=False)

                    messagebox.showinfo("Assigned", f"Exam '{exam_name}' assigned!")
                    load_class()
                else:
                    messagebox.showinfo("Info", "Exam already assigned.")

                popup.destroy()

            exam_listbox_popup.bind("<Double-Button-1>", on_double_click)

        # 4.8 DELETE CLASS - Remove class and update dropdown
        def delete_class():
            """Delete selected class file and update UI"""
            if not class_var.get():
                messagebox.showerror("Error", "Select a class first.")
                return
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{class_var.get()}'?")
            if confirm:
                os.remove(f"classes/{class_var.get()}.json")
                class_var.set("")
                student_listbox.delete(0, tk.END)
                exam_listbox.delete(0, tk.END)
                messagebox.showinfo("Deleted", "Class deleted.")
                # Update dropdown menu
                menu = class_dropdown["menu"]
                menu.delete(0, "end")
                for f in os.listdir("classes"):
                    menu.add_command(label=f, command=lambda value=f: class_var.set(value))

        # 4.9 BOTTOM BUTTONS - Add Students, Assign Exam, Delete Class
        bottom_frame = tk.Frame(manage_class_frame)
        bottom_frame.pack(fill="x", pady=10)
        tk.Button(bottom_frame, text="Add Students", width=20, command=add_students).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="Assign Exam", width=20, command=assign_exam).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="Delete Class", width=20, command=delete_class).pack(side="left", padx=5)

    # ===================== CREATE CLASS FRAME =====================
    # 5. CREATE CLASS SCREEN - Create new class and import students
    def init_create_class_frame():
        """Initialize create class interface"""
        # 5.1 CLEAR WIDGETS - Destroy existing widgets in frame
        for widget in create_class_frame.winfo_children():
            widget.destroy()

        # 5.2 TOP FRAME - Back button
        top_frame = tk.Frame(create_class_frame)
        top_frame.pack(fill="x", pady=5)
        tk.Button(top_frame, text="Back", command=lambda: [create_class_frame.pack_forget(), landing_frame.pack(fill="both", expand=True)]).pack(side="left")
        tk.Label(create_class_frame, text="Create New Class", font=("Arial", 14, "bold")).pack(pady=10)

        # 5.3 CLASS NAME ENTRY - Input field for class name
        tk.Label(create_class_frame, text="Class Name:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10,2))
        class_name_entry = tk.Entry(create_class_frame, width=40, font=("Arial", 12))
        class_name_entry.pack(anchor="w", padx=10)

        # 5.4 STUDENT DATA TEXTBOX - Paste student names and passwords
        tk.Label(create_class_frame, text="Paste Student Names & Passwords (Two Columns: Name\tPassword):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10,2))
        input_text = tk.Text(create_class_frame, width=80, height=20, font=("Courier", 11))
        input_text.pack(padx=10, pady=5)

        # 5.5 SAVE CLASS - Process and save class to file
        def save_class():
            """Validate and save class with students"""
            classname = class_name_entry.get().strip()
            if not classname:
                messagebox.showerror("Error", "Enter a class name.")
                return

            content = input_text.get("1.0", tk.END).strip()
            if not content:
                messagebox.showerror("Error", "Paste student data in the textbox.")
                return

            students = []
            for line in content.splitlines():
                parts = line.split("\t")  # Expect tab-separated
                if len(parts) != 2:
                    continue
                name, password = parts
                students.append({"name": name.strip(), "password": password.strip()})

            if not students:
                messagebox.showerror("Error", "No valid student data found.")
                return

            os.makedirs("classes", exist_ok=True)
            filepath = f"classes/{classname}.json"

            # Create class data structure with empty exams list
            class_data = {
                "classname": classname,
                "students": students,
                "exams": []
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(class_data, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Saved", f"Class '{classname}' saved with {len(students)} students!")
            class_name_entry.delete(0, tk.END)
            input_text.delete("1.0", tk.END)

        tk.Button(create_class_frame, text="Process & Save Class", font=("Arial", 12, "bold"), width=25, command=save_class).pack(pady=10)

    # ===================== EXAM GENERATION FRAME =====================
    # 6. EXAM GENERATION SCREEN - Create exams with questions and settings
    def init_exam_frame():
        """Initialize exam generation interface"""
        exam = {"exam_name": "", "questions": []}
        current_question_index = None

        # 6.1 UPDATE INDICATOR - Show current question status
        def update_indicator():
            """Display which question is being edited"""
            total = len(exam["questions"])
            if current_question_index is None:
                indicator.config(text=f"New Question ({total + 1})")
            else:
                indicator.config(text=f"Editing Question {current_question_index + 1} / {total}")

        # 6.2 REFRESH LIST - Update questions listbox
        def refresh_list():
            """Populate questions listbox with preview text"""
            qlist.delete(0, tk.END)
            for i, q in enumerate(exam["questions"], 1):
                qlist.insert(tk.END, f"{i}. {q['question'][:30]}")

        # 6.3 CLEAR FIELDS - Reset all input fields
        def clear_fields():
            """Clear all question input fields"""
            question_entry.delete(0, tk.END)
            
            # Clear MCQ entries and uncheck radios
            for e in mcq_entries:
                e.delete(0, tk.END)
            mcq_correct.set(-1)
            
            # Clear text answer
            text_answer.delete(0, tk.END)
            
            # Clear True/False selection
            tf_var.set(-1)
            
        # 6.4 LOAD QUESTION - Load existing question for editing
        def load_question(idx):
            """Load question data into edit fields"""
            nonlocal current_question_index
            current_question_index = idx
            q = exam["questions"][idx]
            question_entry.delete(0, tk.END)
            question_entry.insert(0, q["question"])
            answer_type.set(q.get("type", "mcq"))
            update_answer_fields(q)
            update_indicator()

        # 6.5 UPDATE ANSWER FIELDS - Show/hide answer type specific fields
        def update_answer_fields(q=None):
            """Display appropriate answer fields based on question type"""
            mcq_frame.pack_forget()
            text_frame.pack_forget()
            tf_frame.pack_forget()

            atype = answer_type.get()
            if atype == "mcq":
                mcq_frame.pack(anchor="w", pady=5)
                if q:
                    for i in range(4):
                        mcq_entries[i].delete(0, tk.END)
                        mcq_entries[i].insert(0, q["choices"][i])
                    mcq_correct.set(q.get("answer", -1))
            elif atype == "text":
                text_frame.pack(anchor="w", pady=5)
                if q:
                    text_answer.delete(0, tk.END)
                    text_answer.insert(0, q.get("answer_text", ""))
            elif atype == "tf":
                tf_frame.pack(anchor="w", pady=5)
                if q:
                    tf_var.set(q.get("answer", -1))

        # 6.6 ADD OR UPDATE QUESTION - Save question to exam
        def add_or_update():
            """Validate and add/update question"""
            nonlocal current_question_index
            qtext = question_entry.get().strip()
            atype = answer_type.get()
            data = {"question": qtext, "type": atype}

            if not qtext:
                messagebox.showerror("Error", "Enter the question text.")
                return

            if atype == "mcq":
                choices = [e.get().strip() for e in mcq_entries]
                ans = mcq_correct.get()
                if any(not c for c in choices) or ans == -1:
                    messagebox.showerror("Error", "Fill all choices and select the correct answer.")
                    return
                data.update({"choices": choices, "answer": ans})
            elif atype == "text":
                data["answer_text"] = text_answer.get().strip()
            elif atype == "tf":
                ans = tf_var.get()
                if ans not in (0,1):
                    messagebox.showerror("Error", "Select True or False.")
                    return
                data["answer"] = ans

            if current_question_index is None:
                exam["questions"].append(data)
            else:
                exam["questions"][current_question_index] = data

            refresh_list()
            clear_fields()
            current_question_index = None
            update_indicator()

        # 6.7 ON SELECT - Load question when clicked in list
        def on_select(event):
            """Load question when selected from listbox"""
            if qlist.curselection():
                load_question(qlist.curselection()[0])

        # 6.8 RESET ALL - Clear entire exam
        def reset_all():
            """Clear all exam data"""
            nonlocal current_question_index
            exam["exam_name"] = ""
            exam["questions"].clear()
            current_question_index = None
            exam_name.delete(0, tk.END)
            clear_fields()
            qlist.delete(0, tk.END)
            update_indicator()

        # 6.9 SAVE EXAM - Save exam with settings to file
        def save_exam():
            """Validate and save exam to JSON file"""
            name = exam_name.get().strip()
            if not name or not exam["questions"]:
                messagebox.showerror("Error", "Enter exam name and add at least one question.")
                return

            exam["exam_name"] = name

            # Save exam settings
            exam["settings"] = {
                "duration_enabled": duration_check_var.get(),
                "duration": duration_var.get() if duration_check_var.get() else None,
                "shuffle": shuffle_var.get(),
                "show_detections": detection_var.get(),
                "show_score": score_var.get()
            }

            # Write exam to file
            with open(f"exams/{name}.json", "w", encoding="utf-8") as f:
                json.dump(exam, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Saved", f"Exam '{name}' saved successfully!")
            reset_all()

        # 6.10 WIDGETS SETUP - Clear and initialize exam frame widgets
        for widget in exam_frame.winfo_children():
            widget.destroy()
        top_frame = tk.Frame(exam_frame)
        top_frame.pack(fill="x", pady=5)
        tk.Button(top_frame, text="Back", command=lambda:[exam_frame.pack_forget(), landing_frame.pack(fill="both", expand=True)]).pack(side="left")

        main = tk.Frame(exam_frame)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # 6.11 LEFT FRAME - Question creation section
        left = tk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="Exam Name").pack(anchor="w")
        exam_name = tk.Entry(left, width=50)
        exam_name.pack(anchor="w")
        indicator = tk.Label(left, text="New Question (1)", font=("Arial", 10, "bold"))
        indicator.pack(anchor="w", pady=5)

        # Question input
        tk.Label(left, text="Question", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10,2))
        question_entry = tk.Entry(left, width=60)
        question_entry.pack(anchor="w")

        # Answer type selector
        tk.Label(left, text="Answer Type", font=("Arial", 12, "bold")).pack(anchor="w", pady=(10,2))
        types_frame = tk.Frame(left)
        types_frame.pack(anchor="w", pady=5)
        answer_type = tk.StringVar(value="mcq")
        tk.Radiobutton(types_frame, text="Multiple Choice", variable=answer_type, value="mcq", command=lambda: update_answer_fields()).pack(side="left")
        tk.Radiobutton(types_frame, text="Text", variable=answer_type, value="text", command=lambda: update_answer_fields()).pack(side="left", padx=10)
        tk.Radiobutton(types_frame, text="True/False", variable=answer_type, value="tf", command=lambda: update_answer_fields()).pack(side="left")

        # 6.12 ANSWER SECTIONS - MCQ, Text, True/False input fields
        mcq_frame = tk.Frame(left)
        tk.Label(mcq_frame, text="Choices & Correct Answer", font=("Arial", 12, "bold")).pack(anchor="w")
        mcq_entries = []
        mcq_correct = tk.IntVar(value=-1)
        for i in range(4):
            f = tk.Frame(mcq_frame)
            f.pack(anchor="w")
            tk.Radiobutton(f, variable=mcq_correct, value=i).pack(side="left")
            e = tk.Entry(f, width=45)
            e.pack(side="left")
            mcq_entries.append(e)

        text_frame = tk.Frame(left)
        tk.Label(text_frame, text="Answer Text", font=("Arial", 12, "bold")).pack(anchor="w")
        text_answer = tk.Entry(text_frame, width=50)
        text_answer.pack(anchor="w")

        tf_frame = tk.Frame(left)
        tk.Label(tf_frame, text="Select Correct Answer", font=("Arial", 12, "bold")).pack(anchor="w")
        tf_var = tk.IntVar(value=-1)
        tk.Radiobutton(tf_frame, text="True", variable=tf_var, value=1).pack(anchor="w")
        tk.Radiobutton(tf_frame, text="False", variable=tf_var, value=0).pack(anchor="w")

        # 6.13 BOTTOM BUTTONS - Add question and save exam
        bottom_frame = tk.Frame(left)
        bottom_frame.pack(side="bottom", fill="x", pady=10)
        tk.Button(bottom_frame, text="Add / Update Question", command=add_or_update).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="Save Exam", command=save_exam).pack(side="left", padx=5)

        update_answer_fields()

        # 6.14 RIGHT FRAME - Questions list and exam settings
        right = tk.Frame(main)
        right.pack(side="right", fill="y")

        # Questions list
        tk.Label(right, text="Questions", font=("Arial", 12, "bold")).pack()
        qlist = tk.Listbox(right, width=30)
        qlist.pack(fill="y", expand=True)
        qlist.bind("<<ListboxSelect>>", on_select)

        # 6.15 EXAM SETTINGS - Duration, shuffle, detections, score display
        settings_frame = tk.LabelFrame(right, text="Exam Settings", padx=10, pady=10)
        settings_frame.pack(fill="x", pady=10)

        # Duration checkbox + entry
        duration_check_var = tk.BooleanVar(value=False)
        tk.Checkbutton(settings_frame, text="Time Duration (mins)", variable=duration_check_var,
                    command=lambda: duration_entry.config(state="normal" if duration_check_var.get() else "disabled")).grid(row=0, column=0, sticky="w")

        duration_var = tk.IntVar(value=60)
        duration_entry = tk.Entry(settings_frame, textvariable=duration_var, width=5, state="disabled")
        duration_entry.grid(row=0, column=1, sticky="w", padx=5)

        # Shuffle questions
        shuffle_var = tk.BooleanVar(value=False)
        tk.Checkbutton(settings_frame, text="Shuffle Questions", variable=shuffle_var).grid(row=1, column=0, columnspan=2, sticky="w")

        # Show detections
        detection_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, text="Show Detections to Student", variable=detection_var).grid(row=2, column=0, columnspan=2, sticky="w")

        # Show score immediately
        score_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, text="Show Score Immediately", variable=score_var).grid(row=3, column=0, columnspan=2, sticky="w")

    # ===================== LOGS FRAME =====================
    # 7. EXAM LOGS SCREEN - View and analyze exam results
    def init_logs_frame():
        """Initialize exam logs viewing interface"""
        # 7.1 CLEAR WIDGETS - Destroy existing widgets in frame
        for widget in logs_frame.winfo_children():
            widget.destroy()

        # 7.2 TOP FRAME - Back button and title
        top_frame = tk.Frame(logs_frame)
        top_frame.pack(fill="x", pady=5)

        tk.Button(top_frame, text="Back", command=lambda: [logs_frame.pack_forget(), landing_frame.pack(fill="both", expand=True)]).pack(side="left")
        tk.Label(logs_frame, text="Exam Logs", font=("Arial", 14, "bold")).pack(pady=10)

        # 7.3 FILTER DROPDOWNS - Select class and exam
        filter_frame = tk.Frame(logs_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(filter_frame, text="Class:").pack(side="left", padx=(0,5))
        class_cb = ttk.Combobox(filter_frame, state="readonly", width=25)
        class_cb.pack(side="left", padx=5)

        tk.Label(filter_frame, text="Exam:").pack(side="left", padx=(20,5))
        exam_cb = ttk.Combobox(filter_frame, state="readonly", width=25)
        exam_cb.pack(side="left", padx=5)

        # 7.4 MAIN CONTENT AREA - Students treeview and log display
        content_frame = tk.Frame(logs_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # 7.5 STUDENTS LIST - Treeview showing student names and scores
        student_tree = ttk.Treeview(
            content_frame,
            columns=("name", "score"),
            show="headings",
            height=18
        )
        student_tree.heading("name", text="Student")
        student_tree.heading("score", text="Score")
        student_tree.column("name", width=200, anchor="w")
        student_tree.column("score", width=80, anchor="center")
        student_tree.pack(side="left", padx=(0,10), pady=5, fill="y")

        # 7.6 LOG DISPLAY - Text area showing detailed exam log
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        tk.Label(right_frame, text="Log Details", font=("Arial", 11, "bold")).pack(anchor="w")
        log_display = tk.Text(right_frame, wrap="word")
        log_display.pack(fill="both", expand=True)

        # 7.7 LOAD CLASSES - Read all class files and populate dropdown
        class_files = [f for f in os.listdir("classes") if f.endswith(".json")]
        classes = {}
        for f in class_files:
            with open(f"classes/{f}", "r", encoding="utf-8") as cf:
                data = json.load(cf)
                classname = data.get("classname", f[:-5])
                classes[classname] = data.get("exams", [])
        class_cb['values'] = sorted(classes.keys())

        # 7.8 HANDLERS - Event handlers for dropdown selections
        student_log_map = {}

        # 7.8.1 ON CLASS SELECT - Load exams for selected class
        def on_class_select(event=None):
            """Populate exam dropdown when class is selected"""
            exam_cb.set('')
            student_tree.delete(*student_tree.get_children())
            log_display.delete("1.0", tk.END)
            student_log_map.clear()

            selected_class = class_cb.get()
            if not selected_class:
                exam_cb['values'] = []
                return

            exams = classes.get(selected_class, [])
            exam_cb['values'] = [
                ex[:-5] if ex.endswith(".json") else ex
                for ex in exams
            ]

        # 7.8.2 ON EXAM SELECT - Load students for selected exam
        def on_exam_select(event=None):
            """Populate student list when exam is selected"""
            student_tree.delete(*student_tree.get_children())
            log_display.delete("1.0", tk.END)
            student_log_map.clear()

            selected_class = class_cb.get()
            selected_exam = exam_cb.get()

            if not selected_class or not selected_exam:
                return

            if not os.path.exists("logs"):
                return

            log_files = [f for f in os.listdir("logs") if f.endswith(".json")]

            # Find matching logs for selected class and exam
            for lf in log_files:
                path = os.path.join("logs", lf)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    continue

                if (
                    data.get("exam_name") == selected_exam and
                    data.get("class_name") == selected_class
                ):
                    student = data.get("student_name")
                    score = data.get("score", "")
                    if student:
                        student_log_map[student] = lf
                        student_tree.insert("", "end", values=(student, score))

        # 7.8.3 ON STUDENT SELECT - Display detailed log for selected student
        def on_student_select(event):
            """Show full exam details when student is selected"""
            sel = student_tree.selection()
            if not sel:
                return

            selected_student = student_tree.item(sel[0], "values")[0]
            selected_class = class_cb.get()
            selected_exam = exam_cb.get()

            log_file = None

            # Find log file for selected student
            for lf in os.listdir("logs"):
                if not lf.endswith(".json"):
                    continue

                with open(f"logs/{lf}", "r", encoding="utf-8") as f:
                    data = json.load(f)

                if (
                    data.get("student_name") == selected_student and
                    data.get("class_name") == selected_class and
                    data.get("exam_name") == selected_exam
                ):
                    log_file = f"logs/{lf}"
                    break

            if not log_file:
                log_display.insert(tk.END, "Log file not found.\n")
                return

            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 7.8.3.1 DISPLAY BASIC INFO - Student, class, exam, score
            log_display.delete("1.0", tk.END)
            log_display.insert(tk.END, f"Student: {data.get('student_name')}\n")
            log_display.insert(tk.END, f"Class: {data.get('class_name')}\n")
            log_display.insert(tk.END, f"Exam: {data.get('exam_name')}\n")
            log_display.insert(tk.END, f"Score: {data.get('score')} / {len(data.get('answers', []))}\n")
            log_display.insert(tk.END, f"Wrong Questions: {data.get('wrong_questions')}\n\n")

            # 7.8.3.2 DISPLAY TIMING - Start, finish, and duration
            log_display.insert(tk.END, f"Started At: {data.get('started_at')}\n")
            log_display.insert(tk.END, f"Finished At: {data.get('finished_at')}\n")
            duration = data.get("duration_taken_sec")
            if duration is not None:
                mins, secs = divmod(int(duration), 60)
                log_display.insert(tk.END, f"Duration Taken: {mins}m {secs}s\n\n")

            # 7.8.3.3 DISPLAY DETECTIONS - Anti-cheat events with timestamps
            detections = data.get("detections", [])
            if detections:
                log_display.insert(tk.END, "Detections:\n")
                for d in detections:
                    mins, secs = divmod(int(d.get("timestamp_relative_sec", 0)), 60)
                    log_display.insert(
                        tk.END,
                        f"[{mins}m {secs}s | {d.get('timestamp_earth')}] {d.get('event')}\n"
                    )
            else:
                log_display.insert(tk.END, "No detections recorded.\n")

        # 7.9 BINDINGS - Attach event handlers
        class_cb.bind("<<ComboboxSelected>>", on_class_select)
        exam_cb.bind("<<ComboboxSelected>>", on_exam_select)
        student_tree.bind("<Double-1>", on_student_select)

    # 8. MAIN LOOP - Start Tkinter event loop
    landing_frame.pack(fill="both", expand=True)
    root.mainloop()