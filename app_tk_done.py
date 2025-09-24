from __future__ import annotations

import re
import tkinter as tk
from tkinter import ttk, messagebox

from db_done import DB

#email format

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_valid_email(email: str) -> bool:
    """check if the argument is a valid email format
    Args:
        email (str): email

    Returns:
        bool: True if valid
    """
    return bool(EMAIL_RE.fullmatch((email or "").strip()))


def nonempty(*strings: str) -> bool:
    """Check if there are empty characters after trimming whitespaces

    Args:
        *strings (str): pointer to string

    Returns:
        bool: True if no empty characters after trimming and false otherwise
    """
    return all((s or "").strip() != "" for s in strings)


#App

class App:
    """Main Tkinter window for the website

    Attributes:
        root (tk.Tk): The root Tkinter window.
        db (DB): Database connection for 'school.db'.
        notebook (ttk.Notebook): Main tab container for the different sections. 
        students_tab (ttk.Frame): Students tab      
        instructors_tab (ttk.Frame): Instructors tab 
        courses_tab (ttk.Frame): Courses tab 
        enroll_tab (ttk.Frame): Enrollment tab 
        _status_var (tk.StringVar): Status bar text variable.
        stu_tree (ttk.Treeview): Table of students 
        ins_tree (ttk.Treeview): Table of Instructors
        crs_tree (ttk.Treeview): Table of courses
        enr_tree (ttk.Treeview): Table of enrollments
    """
    def __init__(self, root: tk.Tk) -> None:
        """Initialize the application components.

        Args:
            root (tk.Tk): Pre-created Tkinter root window.
        """
        self.root = root
        self.db = DB("school.db")
 
        self._init_window()
        self._init_styles()
 
        self._init_notebook()
 
        self._build_students_tab()
 
        self._build_instructors_tab()
 
 
        self._build_courses_tab()
 
 
        self._build_enroll_tab()
        self._wire_shortcuts()
 
        self._set_status("Ready")

 
    def _init_window(self) -> None:
        """Sets  size, title, creates _status_var, minimum size and status Label, and packs it.

        """
        self.root.title("School Manager - Tkinter")
 
        self.root.geometry("1100x720")
 
        self.root.minsize(900, 620)

        self._status_var = tk.StringVar(value="")
 
        self._status = ttk.Label(self.root, textvariable=self._status_var, anchor="w")
 
        self._status.pack(side="bottom", fill="x")


    def _init_styles(self) -> None:
        """Initializes the styles for the application."""
        style = ttk.Style(self.root)


        try:

            style.theme_use("clam")

        except tk.TclError:

            pass

        style.configure("TLabel", padding=(2, 2))

        style.configure("TEntry", padding=(2, 2))

        style.configure("TButton", padding=(4, 6))

        style.configure("Treeview", rowheight=26)



    def _init_notebook(self) -> None:
        """Create and pack the Notebook container for the different tabs."""
        self.nb = ttk.Notebook(self.root)



        self.nb.pack(fill="both", expand=True)


    def _set_status(self, text: str, ms: int | None = None) -> None:
        """Set the status bar text and clear it after the given number of milliseconds

        Args:
            text (str): The message to display.
            ms (int | None): If given the number of milliseconds to delay before clearing the status bar.
        """
        self._status_var.set(text)

        if ms:

            self.root.after(ms, lambda: self._status_var.set(""))





    def _confirm(self, text: str, title: str = "Please Confirm") -> bool:
        """Show a confirmation dialog

        Args:
            text (str): The message to display.
            title (str, optional): The title of the dialog and its default value is "Please Confirm".

        Returns:
            bool: True if user selected yes, False otherwise.
        """
        return messagebox.askyesno(title, text)




    #Students



    def _build_students_tab(self) -> None:
        """Create the students tab :form fields, action buttons, and data table
        """

        self.tab_students = ttk.Frame(self.nb, padding=10)

        self.nb.add(self.tab_students, text="Students")

        self.sid = tk.IntVar(value=0)

        self.sname = tk.StringVar(value="")
        self.sage = tk.IntVar(value=0)

        self.semail = tk.StringVar(value="")


        frm = ttk.Frame(self.tab_students)

        frm.grid(row=0, column=0, sticky="nsew")

        self.tab_students.grid_rowconfigure(1, weight=1)

        self.tab_students.grid_columnconfigure(0, weight=1)

        for r, (lbl, var) in enumerate([

            ("ID", self.sid),

            ("Name", self.sname),

            ("Age", self.sage),
            ("Email", self.semail),

        ]):

            ttk.Label(frm, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=4)

            if isinstance(var, tk.IntVar):

                ttk.Entry(frm, textvariable=var).grid(row=r, column=1, sticky="ew", padx=6, pady=4)

            else:
                ttk.Entry(frm, textvariable=var).grid(row=r, column=1, sticky="ew", padx=6, pady=4)

       
        frm.grid_columnconfigure(1, weight=1)



        btns = ttk.Frame(frm)

        btns.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 2))

        ttk.Button(btns, text="Save Student", command=self.add_student).pack(side="left", padx=(0, 6))

        ttk.Button(btns, text="Clear", command=self._clear_student_form).pack(side="left")



        # table

        self.stu_tree = ttk.Treeview(self.tab_students, columns=("id", "name", "age", "email"), show="headings", height=12)
        for i, h in enumerate(("ID", "Name", "Age", "Email")):
    
            self.stu_tree.heading(i, text=h)

            self.stu_tree.column(i, width=150 if i in (0, 2) else 250, anchor="w")

        self.stu_tree.grid(row=1, column=0, sticky="nsew", padx=2, pady=6)

        ttk.Scrollbar(self.tab_students, orient="vertical", command=self.stu_tree.yview).grid(row=1, column=1, sticky="ns")
    
        self.stu_tree.configure(yscrollcommand=lambda *a: self.tab_students.grid_slaves(row=1, column=1)[0].set(*a))



    
        self.refresh_students()


    def _clear_student_form(self) -> None:
        """Clear the student form (ID, Name, Age, Email) and notify the user via status bar"""
        self.sid.set(0); self.sname.set(""); self.sage.set(0); self.semail.set("")

        self._set_status("Student form cleared", 2000)


    def add_student(self) -> None:
        """Add or update a student in the database

        Behavior:
        - Requires a valid email address and name.
        - Verifies the format of emails.
        - Updates the user interface upon success and calls DB.upsert_student.

        Raises:
        Displays a message box about database errors or validation failure.

        """
        name, email = self.sname.get().strip(), self.semail.get().strip()

        if not nonempty(name, email):

            messagebox.showwarning("Warning", "Name and Email are required.")

            return

        if not is_valid_email(email):


            messagebox.showwarning("Warning", "Please enter a valid email address.")


            return

        try:

            self.db.upsert_student(int(self.sid.get()), name, int(self.sage.get()), email)

            self.refresh_students()

            self._set_status("Student saved", 2500)

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def refresh_students(self) -> None:
        """Load and display all students in the database
        Raises:
        Displays a message box about database errors
        
        """
        try:

            rows = self.db.list_students()
        except Exception as e:

            messagebox.showerror("Error", str(e))
            return

        for r in self.stu_tree.get_children():

            self.stu_tree.delete(r)

        for row in rows:

            self.stu_tree.insert("", "end", values=row)


    #Instructors 

    def _build_instructors_tab(self) -> None:
        """
        Build the instructors tab: form fields, action buttons and data table.
        """
        self.tab_instructors = ttk.Frame(self.nb, padding=10)

        self.nb.add(self.tab_instructors, text="Instructors")

        self.iid = tk.IntVar(value=0)

        self.iname = tk.StringVar(value="")

        self.iage = tk.IntVar(value=0)
        self.iemail = tk.StringVar(value="")

        frm = ttk.Frame(self.tab_instructors)

        frm.grid(row=0, column=0, sticky="nsew")
        self.tab_instructors.grid_rowconfigure(1, weight=1)

        self.tab_instructors.grid_columnconfigure(0, weight=1)

        for r, (lbl, var) in enumerate([
            ("ID", self.iid),
            ("Name", self.iname),

            ("Age", self.iage),
            ("Email", self.iemail),

        ]):

            ttk.Label(frm, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=4)

            ttk.Entry(frm, textvariable=var).grid(row=r, column=1, sticky="ew", padx=6, pady=4)
        frm.grid_columnconfigure(1, weight=1)

        btns = ttk.Frame(frm)
        btns.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(6, 2))

        ttk.Button(btns, text="Save Instructor", command=self.add_instructor).pack(side="left", padx=(0, 6))
    
        ttk.Button(btns, text="Clear", command=self._clear_instructor_form).pack(side="left")



        self.ins_tree = ttk.Treeview(self.tab_instructors, columns=("id", "name", "age", "email"), show="headings", height=12)

        for i, h in enumerate(("ID", "Name", "Age", "Email")):

            self.ins_tree.heading(i, text=h)

            self.ins_tree.column(i, width=150 if i in (0, 2) else 250, anchor="w")

        self.ins_tree.grid(row=1, column=0, sticky="nsew", padx=2, pady=6)

        ttk.Scrollbar(self.tab_instructors, orient="vertical", command=self.ins_tree.yview).grid(row=1, column=1, sticky="ns")

        self.ins_tree.configure(yscrollcommand=lambda *a: self.tab_instructors.grid_slaves(row=1, column=1)[0].set(*a))


        self.refresh_instructors()


    def _clear_instructor_form(self) -> None:
        """Clear the student form (ID, Name, Age, Email) and notify the user via status bar"""
        self.iid.set(0); self.iname.set(""); self.iage.set(0); self.iemail.set("")
        self._set_status("Instructor form cleared", 2000)

    def add_instructor(self) -> None:
        """Add or update a student in the database

        Behavior:
        - Requires a valid email address and name.
        - Verifies the format of emails.
        - Updates the user interface upon success and calls DB.upsert_student.

        Raises:
        Displays a message box about database errors or validation failure.

        """
        name, email = self.iname.get().strip(), self.iemail.get().strip()


        if not nonempty(name, email):

            messagebox.showwarning("Warning", "Name and Email are required.")

            return
        if not is_valid_email(email):

            messagebox.showwarning("Warning", "Please enter a valid email address.")
            return

        try:

            self.db.upsert_instructor(int(self.iid.get()), name, int(self.iage.get()), email)

            self.refresh_instructors()





            self._set_status("Instructor saved", 2500)
        except Exception as e:

            messagebox.showerror("Error", str(e))

    def refresh_instructors(self) -> None:
        """Refresh the list of instructors in the database and display them in the treeview"""
        try:

            rows = self.db.list_instructors()

        except Exception as e:

            messagebox.showerror("Error", str(e))

            return
        for r in self.ins_tree.get_children():




            self.ins_tree.delete(r)

        for row in rows:

            self.ins_tree.insert("", "end", values=row)


    #Courses



    def _build_courses_tab(self) -> None:
        """Create the courses tab ui. Includes features buttons to assign instructors and save courses, as well as fields for the course name and optional instructor ID.

        

        """
        self.tab_courses = ttk.Frame(self.nb, padding=10)

        self.nb.add(self.tab_courses, text="Courses")


        self.cid = tk.IntVar(value=0)

        self.cname = tk.StringVar(value="")
        self.cinstr = tk.IntVar(value=0)  # 0 = no instructor


        frm = ttk.Frame(self.tab_courses)

        frm.grid(row=0, column=0, sticky="nsew")

        self.tab_courses.grid_rowconfigure(1, weight=1)
        self.tab_courses.grid_columnconfigure(0, weight=1)



        for r, (lbl, var) in enumerate([

            ("Course ID", self.cid),

            ("Course Name", self.cname),
            ("Instructor ID (optional)", self.cinstr),

        ]):

            ttk.Label(frm, text=lbl).grid(row=r, column=0, sticky="w", padx=6, pady=4)

            ttk.Entry(frm, textvariable=var).grid(row=r, column=1, sticky="ew", padx=6, pady=4)

        frm.grid_columnconfigure(1, weight=1)



        btns = ttk.Frame(frm)

        btns.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(6, 2))
        ttk.Button(btns, text="Save Course", command=self.save_course).pack(side="left", padx=(0, 6))

        ttk.Button(btns, text="Assign Instructor", command=self.assign_instr).pack(side="left")



        self.crs_tree = ttk.Treeview(self.tab_courses, columns=("id", "name", "instr_name", "instr_email"), show="headings", height=12)

        for i, h in enumerate(("Course ID", "Name", "Instructor Name", "Instructor Email")):

            self.crs_tree.heading(i, text=h)

            self.crs_tree.column(i, width=180 if i in (0, 2, 3) else 260, anchor="w")

        self.crs_tree.grid(row=1, column=0, sticky="nsew", padx=2, pady=6)

        ttk.Scrollbar(self.tab_courses, orient="vertical", command=self.crs_tree.yview).grid(row=1, column=1, sticky="ns")

        self.crs_tree.configure(yscrollcommand=lambda *a: self.tab_courses.grid_slaves(row=1, column=1)[0].set(*a))



        self.refresh_courses()



    def save_course(self) -> None:
        """Save a course to the database
        
        Behavior:
        - Requires a valid course name.
        - Updates the user interface upon success and calls DB.upsert_course.

        Raises:
        Displays a message box about database errors or validation failure.

        """
        name = self.cname.get().strip()

        if not nonempty(name):

            messagebox.showwarning("Warning", "Course name is required.")

            return

        instr = int(self.cinstr.get()) if self.cinstr.get() != 0 else None

        try:
            self.db.upsert_course(int(self.cid.get()), name, instr)
            self.refresh_courses()

            self._set_status("Course saved", 2500)

        except Exception as e:

            messagebox.showerror("Error", str(e))



    def assign_instr(self) -> None:
        """
        Assign an instructor to a course

        Behavior:
        - Requires a valid instructor ID.
        - Updates the user interface upon success and calls DB.assign_instructor.

        Raises:
        Displays a message box about database errors or validation failure.
        """
        if self.cinstr.get() == 0:

            messagebox.showwarning("Warning", "Enter an Instructor ID to assign (or leave 0 for none).")

            return

        if not self._confirm("Assign this instructor to the course?"):

            return

        try:

            self.db.assign_instructor(int(self.cid.get()), int(self.cinstr.get()))

            self.refresh_courses()
            self._set_status("Instructor assigned", 2500)

        except Exception as e:

            messagebox.showerror("Error", str(e))


    def refresh_courses(self) -> None:
        """
        Load and display all courses in the database
        Raises:
        Displays a message box about database errors
        """
        try:

            rows = self.db.list_courses()

        except Exception as e:
            messagebox.showerror("Error", str(e))
            return
        for r in self.crs_tree.get_children():

            self.crs_tree.delete(r)

        for row in rows:

            self.crs_tree.insert("", "end", values=row)



    #  Enroll

    def _build_enroll_tab(self) -> None:
        """
        Build the enroll tab 

        Behavior:
        - Creates the tab frame, entry fields, and buttons needed for the tab.


        """
        self.tab_enroll = ttk.Frame(self.nb, padding=10)

        self.nb.add(self.tab_enroll, text="Enroll")


        self.esid = tk.IntVar(value=0)
        self.ecid = tk.IntVar(value=0)

        frm = ttk.Frame(self.tab_enroll)

        frm.grid(row=0, column=0, sticky="nsew")

        self.tab_enroll.grid_rowconfigure(1, weight=1)
        self.tab_enroll.grid_columnconfigure(0, weight=1)

        ttk.Label(frm, text="Student ID").grid(row=0, column=0, sticky="w", padx=6, pady=4)

        ttk.Entry(frm, textvariable=self.esid).grid(row=0, column=1, sticky="ew", padx=6, pady=4)

        ttk.Label(frm, text="Course ID").grid(row=1, column=0, sticky="w", padx=6, pady=4)

        ttk.Entry(frm, textvariable=self.ecid).grid(row=1, column=1, sticky="ew", padx=6, pady=4)
      
      
        frm.grid_columnconfigure(1, weight=1)


        btns = ttk.Frame(frm)

        btns.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(6, 2))

        ttk.Button(btns, text="Enroll", command=self.enroll).pack(side="left", padx=(0, 6))
        ttk.Button(btns, text="Show Course Enrollments", command=self.show_course_enrollments).pack(side="left")


        self.enr_tree = ttk.Treeview(self.tab_enroll, columns=("sid", "name", "email"), show="headings", height=12)

        for i, h in enumerate(("Student ID", "Name", "Email")):

            self.enr_tree.heading(i, text=h)
            self.enr_tree.column(i, width=200 if i != 1 else 300, anchor="w")

        self.enr_tree.grid(row=1, column=0, sticky="nsew", padx=2, pady=6)

        ttk.Scrollbar(self.tab_enroll, orient="vertical", command=self.enr_tree.yview).grid(row=1, column=1, sticky="ns")

        self.enr_tree.configure(yscrollcommand=lambda *a: self.tab_enroll.grid_slaves(row=1, column=1)[0].set(*a))


    def enroll(self) -> None:
        """Enroll a student in a course

        Behavior:
        - Requires a valid student ID and course ID.
        - Updates the user interface upon success and calls DB.enroll.

        Raises:
        Displays a message box about database errors or validation failure.
        """
        try:

            sid, cid = int(self.esid.get()), int(self.ecid.get())

            if sid <= 0 or cid <= 0:

                messagebox.showwarning("Warning", "Both IDs must be greater than 0.")
                return
            self.db.enroll(sid, cid)

            self._set_status("Enrollment added", 2500)

            self.show_course_enrollments()

        except Exception as e:

            messagebox.showerror("Error", str(e))



    def show_course_enrollments(self) -> None:
        """List all students enrolled in a course

        Behavior:
        - Requires a valid course ID.
        - Updates the user interface upon success and calls DB.list_enrollments.

        Raises:
        Displays a message box about database errors or validation failure.
        """

        try:
            cid = int(self.ecid.get())

            if cid <= 0:


                messagebox.showwarning("Warning", "Enter a Course ID to list enrollments.")
                return

            rows = self.db.list_enrollments(cid)

        except Exception as e:

            messagebox.showerror("Error", str(e))


            return
        for r in self.enr_tree.get_children():
            self.enr_tree.delete(r)

        for row in rows:

            self.enr_tree.insert("", "end", values=row)



    #Shortcuts


    def _wire_shortcuts(self) -> None:
        # Ctrl+S to save current tab, F5 to refresh
        """
        Wire up keyboard shortcuts for saving and refreshing the current tab
        """
        self.root.bind_all("<Control-s>", lambda e: self._save_current_tab())
        self.root.bind_all("<F5>", lambda e: self._refresh_current_tab())

    def _save_current_tab(self) -> None:
        """
        Save the current tab
        
        Mapping:
            0 = Students
            1 = Instructors
            2 = Courses
            3 = Enroll
        """
        i = self.nb.index(self.nb.select())

        if i == 0:   # Students
            self.add_student()

        elif i == 1: # Instructors
            self.add_instructor()

        elif i == 2: # Courses

            self.save_course()

        elif i == 3: # Enroll

            self.enroll()

    def _refresh_current_tab(self) -> None:
        """Do the appropriate refresh for the current tab

        Mapping:
            0 = Students
            1 = Instructors
            2 = Courses
            3 = Enroll
        """
        i = self.nb.index(self.nb.select())

        if i == 0:

            self.refresh_students()
        elif i == 1:

            self.refresh_instructors()
        elif i == 2:

            self.refresh_courses()
        elif i == 3:

            self.show_course_enrollments()



#main

if __name__ == "__main__":
    root = tk.Tk()

    app = App(root)

    root.mainloop()
