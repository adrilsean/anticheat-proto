import tkinter as tk
from teacher import teacher_app
from student import student_app



# ===================== LANDING =====================
def show_teacher():
    landing.destroy()
    teacher_app()
def show_student():
    landing.destroy()
    student_app()
landing = tk.Tk()
landing.title("Exam System")
landing.geometry("300x200")

tk.Label(landing, text="Select Role", font=("Arial", 14, "bold")).pack(pady=20)
tk.Button(landing, text="Teacher", width=20, command=show_teacher).pack(pady=5)
tk.Button(landing, text="Student", width=20, command=show_student).pack(pady=5)

landing.mainloop()