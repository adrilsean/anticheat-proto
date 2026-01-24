import tkinter as tk
from tkinter import messagebox, ttk
import json
import os

def teacher_app():
    os.makedirs("exams", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    root = tk.Tk()
    root.title("Teacher Panel")
    root.geometry("700x600")

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)

    # --- Frames ---
    landing_frame = tk.Frame(main_frame)
    landing_frame.pack(fill="both", expand=True)
    exam_frame = tk.Frame(main_frame)
    logs_frame = tk.Frame(main_frame)
    create_class_frame = tk.Frame(main_frame)
    manage_class_frame = tk.Frame(main_frame)


    # ===================== LANDING =====================
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
    def init_manage_class_frame():
        os.makedirs("classes", exist_ok=True)
        os.makedirs("exams", exist_ok=True)

        for widget in manage_class_frame.winfo_children():    
            widget.destroy()
            
        top_frame = tk.Frame(manage_class_frame)
        top_frame.pack(fill="x", pady=5)  # top horizontal frame
        tk.Button(top_frame, text="Back", command=lambda: [manage_class_frame.pack_forget(), landing_frame.pack(fill="both", expand=True)]).pack(side="left", padx=10)


        # --- Top: Class selection ---
        tk.Label(manage_class_frame, text="Select Class", font=("Arial", 12, "bold")).pack(pady=5)

        class_var = tk.StringVar()
        class_files = [f[:-5] if f.endswith(".json") else f for f in os.listdir("classes")]

        if not class_files:
            class_files = ["No classes available"]

        class_var.set(class_files[0])  # default selection
        class_dropdown = tk.OptionMenu(manage_class_frame, class_var, *class_files)
        class_dropdown.pack()


        # --- Middle: Split frame ---
        middle_frame = tk.Frame(manage_class_frame)
        middle_frame.pack(fill="both", expand=True, pady=10, padx=10)

        # Left: Students
        student_frame = tk.Frame(middle_frame)
        student_frame.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(student_frame, text="Students", font=("Arial", 12, "bold")).pack()
        student_listbox = tk.Listbox(student_frame, width=30)
        student_listbox.pack(fill="both", expand=True)

        # Right: Assigned exams
        assigned_exam_frame = tk.Frame(middle_frame)
        assigned_exam_frame.pack(side="left", fill="both", expand=True, padx=5)
        tk.Label(assigned_exam_frame, text="Assigned Exams", font=("Arial", 12, "bold")).pack()
        exam_listbox = tk.Listbox(assigned_exam_frame, width=30)
        exam_listbox.pack(fill="both", expand=True)

        current_class_data = {}

        # --- Helper: Load class ---
        def load_class(*args):
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

        # --- Button: Add Students ---
        def add_students():
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

            # Process button
            def process_import():
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

                # Append students
                current_class_data.setdefault("students", []).extend(new_students)

                # Save class
                filepath = f"classes/{class_var.get()}"
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(current_class_data, f, indent=4, ensure_ascii=False)

                msg = f"{len(new_students)} students added!"
                if duplicates:
                    msg += f"\nSkipped duplicates: {', '.join(duplicates)}"
                messagebox.showinfo("Saved", msg)
                popup.destroy()
                load_class()


            tk.Button(button_frame, text="Process", font=("Arial", 12, "bold"), width=15, command=process_import).pack()


       # --- Button: Assign Exam ---
        def assign_exam():
            if not class_var.get():
                messagebox.showerror("Error", "Select a class first.")
                return

            exams_files = [f for f in os.listdir("exams") if f.endswith(".json")]
            if not exams_files:
                messagebox.showwarning("No Exams", "No exams available to assign.")
                return

            # Create popup window with Listbox
            popup = tk.Toplevel(root)
            popup.title("Assign Exam")
            popup.geometry("300x400")

            tk.Label(popup, text="Double-click an exam to assign", font=("Arial", 12, "bold")).pack(pady=5)

            exam_listbox_popup = tk.Listbox(popup)
            exam_listbox_popup.pack(fill="both", expand=True, padx=10, pady=10)

           # Populate Listbox with exams
            for exam in exams_files:
                exam_name = exam[:-5] if exam.endswith(".json") else exam  # remove .json
                exam_listbox_popup.insert(tk.END, exam_name)

            # Double-click handler
            def on_double_click(event):
                selected_idx = exam_listbox_popup.curselection()
                if not selected_idx:
                    return
                exam_name = exam_listbox_popup.get(selected_idx[0])

                # Append exam if not already assigned
                current_class_data.setdefault("exams", [])
                if exam_name not in current_class_data["exams"]:
                    current_class_data["exams"].append(exam_name)
                    # Make sure to add .json back when saving, if your files are named with it
                    filename = class_var.get()
                    with open(f"classes/{filename}", "w", encoding="utf-8") as f:
                        json.dump(current_class_data, f, indent=4, ensure_ascii=False)
                    messagebox.showinfo("Assigned", f"Exam '{exam_name}' assigned!")
                    load_class()
                else:
                    messagebox.showinfo("Info", "Exam already assigned.")
                popup.destroy()

            exam_listbox_popup.bind("<Double-Button-1>", on_double_click)

        # --- Button: Delete Class ---
        def delete_class():
            if not class_var.get():
                messagebox.showerror("Error", "Select a class first.")
                return
            confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete '{class_var.get()}'?")
            if confirm:
                os.remove(f"classes/{class_var.get()}")
                class_var.set("")
                student_listbox.delete(0, tk.END)
                exam_listbox.delete(0, tk.END)
                messagebox.showinfo("Deleted", "Class deleted.")
                # Update dropdown
                menu = class_dropdown["menu"]
                menu.delete(0, "end")
                for f in os.listdir("classes"):
                    menu.add_command(label=f, command=lambda value=f: class_var.set(value))

        # --- Bottom Buttons ---
        bottom_frame = tk.Frame(manage_class_frame)
        bottom_frame.pack(fill="x", pady=10)
        tk.Button(bottom_frame, text="Add Students", width=20, command=add_students).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="Assign Exam", width=20, command=assign_exam).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="Delete Class", width=20, command=delete_class).pack(side="left", padx=5)


# ===================== CREATE CLASS FRAME =====================
    def init_create_class_frame():
        for widget in create_class_frame.winfo_children():
            widget.destroy()

        top_frame = tk.Frame(create_class_frame)
        top_frame.pack(fill="x", pady=5)
        tk.Button(top_frame, text="Back", command=lambda: [create_class_frame.pack_forget(), landing_frame.pack(fill="both", expand=True)]).pack(side="left")
        tk.Label(create_class_frame, text="Create New Class", font=("Arial", 14, "bold")).pack(pady=10)

        # Class name entry
        tk.Label(create_class_frame, text="Class Name:", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10,2))
        class_name_entry = tk.Entry(create_class_frame, width=40, font=("Arial", 12))
        class_name_entry.pack(anchor="w", padx=10)

        # Textbox for Excel input
        tk.Label(create_class_frame, text="Paste Student Names & Passwords (Two Columns: Name\tPassword):", font=("Arial", 12)).pack(anchor="w", padx=10, pady=(10,2))
        input_text = tk.Text(create_class_frame, width=80, height=20, font=("Courier", 11))
        input_text.pack(padx=10, pady=5)

        # Save Button
        def save_class():
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

            # Save class with empty exams list
            class_data = {
                "classname": classname,
                "students": students,
                "exams": []   # <-- Initially empty list
            }

            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(class_data, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Saved", f"Class '{classname}' saved with {len(students)} students!")
            class_name_entry.delete(0, tk.END)
            input_text.delete("1.0", tk.END)

        tk.Button(create_class_frame, text="Process & Save Class", font=("Arial", 12, "bold"), width=25, command=save_class).pack(pady=10)



    # ===================== EXAM GENERATION =====================
    def init_exam_frame():
        exam = {"exam_name": "", "questions": []}
        current_question_index = None

        def update_indicator():
            total = len(exam["questions"])
            if current_question_index is None:
                indicator.config(text=f"New Question ({total + 1})")
            else:
                indicator.config(text=f"Editing Question {current_question_index + 1} / {total}")

        def refresh_list():
            qlist.delete(0, tk.END)
            for i, q in enumerate(exam["questions"], 1):
                qlist.insert(tk.END, f"{i}. {q['question'][:30]}")

        def clear_fields():
            question_entry.delete(0, tk.END)
            
            # Clear MCQ entries and uncheck radios
            for e in mcq_entries:
                e.delete(0, tk.END)
            mcq_correct.set(-1)
            
            # Clear text answer
            text_answer.delete(0, tk.END)
            
            # Clear True/False selection
            tf_var.set(-1)
            
        def load_question(idx):
            nonlocal current_question_index
            current_question_index = idx
            q = exam["questions"][idx]
            question_entry.delete(0, tk.END)
            question_entry.insert(0, q["question"])
            answer_type.set(q.get("type", "mcq"))
            update_answer_fields(q)
            update_indicator()

        def update_answer_fields(q=None):
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

        def add_or_update():
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

        def on_select(event):
            if qlist.curselection():
                load_question(qlist.curselection()[0])

        def reset_all():
            nonlocal current_question_index
            exam["exam_name"] = ""
            exam["questions"].clear()
            current_question_index = None
            exam_name.delete(0, tk.END)
            clear_fields()
            qlist.delete(0, tk.END)
            update_indicator()

        def save_exam():
            name = exam_name.get().strip()
            if not name or not exam["questions"]:
                messagebox.showerror("Error", "Enter exam name and add at least one question.")
                return

            exam["exam_name"] = name

            # --- Save settings ---
            exam["settings"] = {
                "duration_enabled": duration_check_var.get(),
                "duration": duration_var.get() if duration_check_var.get() else None,
                "shuffle": shuffle_var.get(),
                "show_detections": detection_var.get(),
                "show_score": score_var.get()
            }

            # --- Write to file ---
            with open(f"exams/{name}.json", "w", encoding="utf-8") as f:
                json.dump(exam, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Saved", f"Exam '{name}' saved successfully!")
            reset_all()


        # --- Widgets ---
        for widget in exam_frame.winfo_children():
            widget.destroy()
        top_frame = tk.Frame(exam_frame)
        top_frame.pack(fill="x", pady=5)
        tk.Button(top_frame, text="Back", command=lambda:[exam_frame.pack_forget(), landing_frame.pack(fill="both", expand=True)]).pack(side="left")

        main = tk.Frame(exam_frame)
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # Left frame
        left = tk.Frame(main)
        left.pack(side="left", fill="both", expand=True)

        tk.Label(left, text="Exam Name").pack(anchor="w")
        exam_name = tk.Entry(left, width=50)
        exam_name.pack(anchor="w")
        indicator = tk.Label(left, text="New Question (1)", font=("Arial", 10, "bold"))
        indicator.pack(anchor="w", pady=5)

        # Question section
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

        # --- Answer sections ---
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

        # --- Bottom buttons ---
        bottom_frame = tk.Frame(left)
        bottom_frame.pack(side="bottom", fill="x", pady=10)
        tk.Button(bottom_frame, text="Add / Update Question", command=add_or_update).pack(side="left", padx=5)
        tk.Button(bottom_frame, text="Save Exam", command=save_exam).pack(side="left", padx=5)

        update_answer_fields()

       # Right frame: Question list + Settings
        right = tk.Frame(main)
        right.pack(side="right", fill="y")

        # --- Questions list ---
        tk.Label(right, text="Questions", font=("Arial", 12, "bold")).pack()
        qlist = tk.Listbox(right, width=30)
        qlist.pack(fill="y", expand=True)
        qlist.bind("<<ListboxSelect>>", on_select)

        # --- Exam settings below questions ---
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


    # ---------------- LOGS FRAME ----------------
    def init_logs_frame():
        for widget in logs_frame.winfo_children():
            widget.destroy()

        # ---------------- Top Frame ----------------
        top_frame = tk.Frame(logs_frame)
        top_frame.pack(fill="x", pady=5)

        tk.Button(top_frame, text="Back", command=lambda: [logs_frame.pack_forget(), landing_frame.pack(fill="both", expand=True)]).pack(side="left")
        tk.Label(logs_frame, text="Exam Logs", font=("Arial", 14, "bold")).pack(pady=10)

        # ---------------- Dropdowns ----------------
        filter_frame = tk.Frame(logs_frame)
        filter_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(filter_frame, text="Class:").pack(side="left", padx=(0,5))
        class_cb = ttk.Combobox(filter_frame, state="readonly", width=25)
        class_cb.pack(side="left", padx=5)

        tk.Label(filter_frame, text="Exam:").pack(side="left", padx=(20,5))
        exam_cb = ttk.Combobox(filter_frame, state="readonly", width=25)
        exam_cb.pack(side="left", padx=5)

        # ---------------- Main Content Area ----------------
        content_frame = tk.Frame(logs_frame)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ---------------- Students List (Treeview, LEFT) ----------------
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

        # ---------------- Log Display (RIGHT) ----------------
        right_frame = tk.Frame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True)

        tk.Label(right_frame, text="Log Details", font=("Arial", 11, "bold")).pack(anchor="w")
        log_display = tk.Text(right_frame, wrap="word")
        log_display.pack(fill="both", expand=True)

        # ---------------- Load Classes ----------------
        class_files = [f for f in os.listdir("classes") if f.endswith(".json")]
        classes = {}
        for f in class_files:
            with open(f"classes/{f}", "r", encoding="utf-8") as cf:
                data = json.load(cf)
                classname = data.get("classname", f[:-5])
                classes[classname] = data.get("exams", [])
        class_cb['values'] = sorted(classes.keys())

        # ---------------- Handlers ----------------
        student_log_map = {}

        def on_class_select(event=None):
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

        def on_exam_select(event=None):
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
                        # map student -> exact log filename
                        student_log_map[student] = lf
                        student_tree.insert("", "end", values=(student, score))

        def on_student_select(event):
            sel = student_tree.selection()
            if not sel:
                return

            selected_student = student_tree.item(sel[0], "values")[0]
            selected_class = class_cb.get()
            selected_exam = exam_cb.get()

            log_file = None

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

            # ---------------- Basic Info ----------------
            log_display.delete("1.0", tk.END)
            log_display.insert(tk.END, f"Student: {data.get('student_name')}\n")
            log_display.insert(tk.END, f"Class: {data.get('class_name')}\n")
            log_display.insert(tk.END, f"Exam: {data.get('exam_name')}\n")
            log_display.insert(tk.END, f"Score: {data.get('score')} / {len(data.get('answers', []))}\n")
            log_display.insert(tk.END, f"Wrong Questions: {data.get('wrong_questions')}\n\n")

            # ---------------- Timing ----------------
            log_display.insert(tk.END, f"Started At: {data.get('started_at')}\n")
            log_display.insert(tk.END, f"Finished At: {data.get('finished_at')}\n")
            duration = data.get("duration_taken_sec")
            if duration is not None:
                mins, secs = divmod(int(duration), 60)
                log_display.insert(tk.END, f"Duration Taken: {mins}m {secs}s\n\n")

            # ---------------- Detections ----------------
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

        # ---------------- Bindings ----------------
        class_cb.bind("<<ComboboxSelected>>", on_class_select)
        exam_cb.bind("<<ComboboxSelected>>", on_exam_select)
        student_tree.bind("<Double-1>", on_student_select)


    landing_frame.pack(fill="both", expand=True)
    root.mainloop()
