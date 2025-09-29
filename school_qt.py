# school_qt.py
"""
School Management System PyQt5 GUI.

Main window and tabs for Students, Instructors, Courses, and Records.
Handles CRUD, search/filter, JSON save/load, CSV export, and DB backup.
"""

import sys, csv, os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget,
    QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QMessageBox, QComboBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QLabel, QFileDialog, QDialog, QDialogButtonBox
)

# your validated models + DB adapter
from school import Student, Instructor, Course
from school_sqlite import SqliteSchoolDB


class SchoolManagementSystem(QMainWindow):
    """
        Main application window for the School Management System.

        :ivar db: SQLite-backed DB adapter used for all CRUD operations
        :vartype db: SqliteSchoolDB
        :ivar tabs: The root tab widget
        :vartype tabs: QTabWidget
        :ivar student_tab: Students tab (add/register)
        :vartype student_tab: QWidget
        :ivar instructor_tab: Instructors tab (add/assign)
        :vartype instructor_tab: QWidget
        :ivar course_tab: Courses tab (add)
        :vartype course_tab: QWidget
        :ivar records_tab: Records tab (tables, search, edit/delete)
        :vartype records_tab: QWidget 
        """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("School Management System")
        self.setGeometry(100, 100, 1000, 640)

        # SQLite-backed DB (expects methods listed below)
        self.db = SqliteSchoolDB("school.db")

        # ----- Tabs -----
        self.tabs = QTabWidget()
        self.student_tab = self._make_student_tab()
        self.instructor_tab = self._make_instructor_tab()
        self.course_tab = self._make_course_tab()
        self.records_tab = self._make_records_tab()

        self.tabs.addTab(self.student_tab, "Students")
        self.tabs.addTab(self.instructor_tab, "Instructors")
        self.tabs.addTab(self.course_tab, "Courses")
        self.tabs.addTab(self.records_tab, "Records")
        self.setCentralWidget(self.tabs)

        # ----- Menu: Save/Load/Export/Backup -----
        bar = self.menuBar().addMenu("Data")
        act_save = bar.addAction("Save (JSON)")
        act_load = bar.addAction("Load (JSON)")
        bar.addSeparator()
        act_export = bar.addAction("Export to CSV (3 files)")
        bar.addSeparator()
        act_backup = bar.addAction("Backup DB")

        act_save.triggered.connect(self.save_json)
        act_load.triggered.connect(self.load_json)
        act_export.triggered.connect(self.export_csv)
        act_backup.triggered.connect(self.backup_db)

        self.refresh_all_tables()

    # -----------------------------------
    # Students tab (add + registration)
    # -----------------------------------
    def _make_student_tab(self) -> QWidget:
        """Create the Students tab layout (add student + register in course).

        :return: Fully constructed widget for the Students tab
        :rtype: QWidget
        """

        w = QWidget()
        outer = QVBoxLayout(w)

        # Add student
        add_box = QGroupBox("Add Student")
        form = QFormLayout(add_box)
        self.stu_name = QLineEdit()
        self.stu_age = QLineEdit()
        self.stu_email = QLineEdit()
        self.stu_id = QLineEdit()
        form.addRow("Name:", self.stu_name)
        form.addRow("Age:", self.stu_age)
        form.addRow("Email:", self.stu_email)
        form.addRow("Student ID:", self.stu_id)
        btn_add = QPushButton("Add Student")
        btn_add.clicked.connect(self.add_student)
        form.addRow(btn_add)

        # Register student in course
        reg_box = QGroupBox("Register Student in Course")
        reg_layout = QFormLayout(reg_box)
        self.reg_student_combo = QComboBox()
        self.reg_course_combo  = QComboBox()
        self._refresh_reg_dropdowns()
        btn_reg = QPushButton("Register")
        btn_reg.clicked.connect(self.register_student_in_course)
        reg_layout.addRow("Student:", self.reg_student_combo)
        reg_layout.addRow("Course:", self.reg_course_combo)
        reg_layout.addRow(btn_reg)

        outer.addWidget(add_box)
        outer.addWidget(reg_box)
        outer.addStretch(1)
        return w

    def add_student(self):
        """Validate inputs and insert a new student.

        :raises ValueError: If any required field is empty or age is invalid
        :return: None
        :rtype: None
        """

        name = self.stu_name.text().strip()
        age_text = self.stu_age.text().strip()
        email = self.stu_email.text().strip()
        sid = self.stu_id.text().strip()
        if not all([name, age_text, email, sid]):
            raise ValueError("All student fields are required.")
        age = int(age_text)  # Student validates age/email again
        s = Student(name, age, email, sid)
        self.db.add_student(s)
        QMessageBox.information(self, "Success", f"Student {name} added.")
        self.stu_name.clear(); self.stu_age.clear(); self.stu_email.clear(); self.stu_id.clear()
        self._refresh_reg_dropdowns()
        self.refresh_students_table()

    def register_student_in_course(self):
        """
            Register the selected student into the selected course from the dropdowns.

            :raises ValueError: If registration fails in the DB layer
            :return: None
            :rtype: None
            """
        if not self.db.students or not self.db.courses:
            QMessageBox.warning(self, "Missing data", "Add at least one student and one course first.")
            return
        student = self.db.students[self.reg_student_combo.currentIndex()]
        course  = self.db.courses[self.reg_course_combo.currentIndex()]
        self.db.register_student_in_course(student.student_id, course.course_id)
        QMessageBox.information(self, "Registered", f"{student.name} → {course.course_name}")
        self.refresh_students_table()
        self.refresh_courses_table()

    # ---------------------------------------
    # Instructors tab (add + assignment)
    # ---------------------------------------
    def _make_instructor_tab(self) -> QWidget:
        """
            Create the Instructors tab (add instructor + assign to course).

            :return: Fully constructed widget for the Instructors tab
            :rtype: QWidget
            """
        w = QWidget()
        outer = QVBoxLayout(w)

        add_box = QGroupBox("Add Instructor")
        form = QFormLayout(add_box)
        self.ins_name = QLineEdit()
        self.ins_age = QLineEdit()
        self.ins_email = QLineEdit()
        self.ins_id = QLineEdit()
        self.ins_assigned = QLineEdit()
        form.addRow("Name:", self.ins_name)
        form.addRow("Age:", self.ins_age)
        form.addRow("Email:", self.ins_email)
        form.addRow("Instructor ID:", self.ins_id)
        form.addRow("Assigned Courses (IDs, comma-sep, optional):", self.ins_assigned)
        btn_add = QPushButton("Add Instructor")
        btn_add.clicked.connect(self.add_instructor)
        form.addRow(btn_add)

        assign_box = QGroupBox("Assign Instructor to Course")
        a_form = QFormLayout(assign_box)
        self.assign_inst_combo = QComboBox()
        self.assign_course_combo = QComboBox()
        self._refresh_assign_dropdowns()
        btn_assign = QPushButton("Assign")
        btn_assign.clicked.connect(self.assign_instructor_to_course)
        a_form.addRow("Instructor:", self.assign_inst_combo)
        a_form.addRow("Course:", self.assign_course_combo)
        a_form.addRow(btn_assign)

        outer.addWidget(add_box)
        outer.addWidget(assign_box)
        outer.addStretch(1)
        return w

    def add_instructor(self):
        """
            Validate inputs and insert a new instructor. Optional assigned courses
            are parsed from a comma-separated string of course IDs.

            :raises ValueError: If required fields are missing or age is invalid
            :return: None
            :rtype: None
            """
        name = self.ins_name.text().strip()
        age_text = self.ins_age.text().strip()
        email = self.ins_email.text().strip()
        iid = self.ins_id.text().strip()
        if not all([name, age_text, email, iid]):
            raise ValueError("All instructor fields (except 'Assigned') are required.")
        age = int(age_text)
        assigned = [c.strip() for c in self.ins_assigned.text().split(",") if c.strip()]
        inst = Instructor(name, age, email, iid, assigned)
        self.db.add_instructor(inst)
        QMessageBox.information(self, "Success", f"Instructor {name} added.")
        self.ins_name.clear(); self.ins_age.clear(); self.ins_email.clear()
        self.ins_id.clear(); self.ins_assigned.clear()
        self._refresh_assign_dropdowns()
        self.refresh_instructors_table()

    def assign_instructor_to_course(self):
        """
        Assign the selected instructor to the selected course. If the course already
        has a different instructor, ask for confirmation before overwriting.

        :return: None
        :rtype: None
        """
        if not self.db.instructors or not self.db.courses:
            QMessageBox.warning(self, "Missing data", "Add at least one instructor and one course first.")
            return
        instructor = self.db.instructors[self.assign_inst_combo.currentIndex()]
        course     = self.db.courses[self.assign_course_combo.currentIndex()]

        if course.instructor and course.instructor is not instructor:
            if QMessageBox.question(
                self, "Overwrite?",
                f"{course.course_name} currently taught by {course.instructor.name}. "
                f"Replace with {instructor.name}?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            ) != QMessageBox.Yes:
                return
        try:
            self.db.assign_instructor_to_course(instructor.instructor_id, course.course_id)
            QMessageBox.information(self, "Assigned", f"{instructor.name} → {course.course_name}")
            self.refresh_instructors_table()
            self.refresh_courses_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ----------------
    # Courses tab (add)
    # ----------------
    def _make_course_tab(self) -> QWidget:
        """
            Create the Courses tab (add a course, optional instructor by name).

            :return: Fully constructed widget for the Courses tab
            :rtype: QWidget
            """
        w = QWidget()
        outer = QVBoxLayout(w)

        add_box = QGroupBox("Add Course")
        form = QFormLayout(add_box)
        self.crs_id = QLineEdit()
        self.crs_name = QLineEdit()
        self.crs_instructor_name = QLineEdit()   # free text, optional
        form.addRow("Course ID:", self.crs_id)
        form.addRow("Course Name:", self.crs_name)
        form.addRow("Instructor Name:", self.crs_instructor_name)
        btn_add = QPushButton("Add Course")
        btn_add.clicked.connect(self.add_course)
        form.addRow(btn_add)

        outer.addWidget(add_box)
        outer.addStretch(1)
        return w

    def add_course(self):
        """
            Add a new course. If an instructor name is provided, it must match an
            existing instructor.

            :raises ValueError: If ID/Name are missing or instructor name not found
            :return: None
            :rtype: None
            """
        try:
            cid = self.crs_id.text().strip()
            cname = self.crs_name.text().strip()
            iname = self.crs_instructor_name.text().strip()
            if not cid or not cname:
                raise ValueError("Course ID and Name are required.")
            instructor = next((i for i in self.db.instructors if i.name == iname), None) if iname else None
            if iname and not instructor:
                raise ValueError(f"Instructor '{iname}' not found. Leave blank or add them first.")
            c = Course(cid, cname, instructor)
            self.db.add_course(c)
            QMessageBox.information(self, "Success", f"Course {cname} added.")
            self.crs_id.clear(); self.crs_name.clear(); self.crs_instructor_name.clear()
            self._refresh_reg_dropdowns(); self._refresh_assign_dropdowns()
            self.refresh_courses_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # -----------------------------------------
    # Records tab: tables + search + edit/delete
    # -----------------------------------------
    def _make_records_tab(self) -> QWidget:
        """
            Create the Records tab containing search controls and three tables
            (Students, Instructors, Courses) with edit/delete actions.

            :return: Fully constructed widget for the Records tab
            :rtype: QWidget
            """
        w = QWidget()
        outer = QVBoxLayout(w)

        # Search row
        sr = QHBoxLayout()
        self.entity_combo = QComboBox()
        self.entity_combo.addItems(["Students", "Instructors", "Courses"])
        self.field_combo = QComboBox()
        self._set_fields_for_entity("Students")
        self.entity_combo.currentTextChanged.connect(self._on_entity_changed)
        self.search_edit = QLineEdit(); self.search_edit.setPlaceholderText("Type to filter...")
        btn_search = QPushButton("Search"); btn_clear = QPushButton("Clear")
        btn_search.clicked.connect(self.perform_search); btn_clear.clicked.connect(self.clear_search)
        sr.addWidget(QLabel("Entity:")); sr.addWidget(self.entity_combo)
        sr.addWidget(QLabel("Field:")); sr.addWidget(self.field_combo)
        sr.addWidget(self.search_edit); sr.addWidget(btn_search); sr.addWidget(btn_clear)
        outer.addLayout(sr)

        # Students table + edit/delete
        outer.addWidget(QLabel("Students"))
        self.tbl_students = QTableWidget(0, 5)
        self.tbl_students.setHorizontalHeaderLabels(["ID", "Name", "Age", "Email", "Registered Courses"])
        outer.addWidget(self.tbl_students)
        sb = QHBoxLayout()
        bs_edit = QPushButton("Edit Selected Student")
        bs_del  = QPushButton("Delete Selected Student")
        bs_edit.clicked.connect(self.edit_selected_student)
        bs_del.clicked.connect(self.delete_selected_student)
        sb.addWidget(bs_edit); sb.addWidget(bs_del); sb.addStretch(1)
        outer.addLayout(sb)

        # Instructors table + edit/delete
        outer.addWidget(QLabel("Instructors"))
        self.tbl_instructors = QTableWidget(0, 5)
        self.tbl_instructors.setHorizontalHeaderLabels(["ID", "Name", "Age", "Email", "Assigned Courses"])
        outer.addWidget(self.tbl_instructors)
        ib = QHBoxLayout()
        bi_edit = QPushButton("Edit Selected Instructor")
        bi_del  = QPushButton("Delete Selected Instructor")
        bi_edit.clicked.connect(self.edit_selected_instructor)
        bi_del.clicked.connect(self.delete_selected_instructor)
        ib.addWidget(bi_edit); ib.addWidget(bi_del); ib.addStretch(1)
        outer.addLayout(ib)

        # Courses table + edit/delete
        outer.addWidget(QLabel("Courses"))
        self.tbl_courses = QTableWidget(0, 4)
        self.tbl_courses.setHorizontalHeaderLabels(["ID", "Name", "Instructor", "Enrolled Students"])
        outer.addWidget(self.tbl_courses)
        cb = QHBoxLayout()
        bc_edit = QPushButton("Edit Selected Course")
        bc_del  = QPushButton("Delete Selected Course")
        bc_edit.clicked.connect(self.edit_selected_course)
        bc_del.clicked.connect(self.delete_selected_course)
        cb.addWidget(bc_edit); cb.addWidget(bc_del); cb.addStretch(1)
        outer.addLayout(cb)

        return w

    # ----- search helpers -----
    def _on_entity_changed(self, text): 
        """
            Update the field dropdown whenever the entity (Students/Instructors/Courses)
            selection changes.

            :param text: Newly selected entity label
            :type text: str
            :return: None
            :rtype: None
            """
        self._set_fields_for_entity(text)
    def _set_fields_for_entity(self, entity):
        """
            Populate the field dropdown for a given entity.

            :param entity: One of "Students", "Instructors", or "Courses"
            :type entity: str
            :return: None
            :rtype: None
            """
        self.field_combo.clear()
        self.field_combo.addItems({
            "Students":    ["All", "ID", "Name", "Email", "Course"],
            "Instructors": ["All", "ID", "Name", "Email", "AssignedCourse"],
            "Courses":     ["All", "ID", "Name", "Instructor", "Student"],
        }[entity])

    # ----- refreshers -----
    def refresh_students_table(self, filtered=None):
        """
        Rebuild the Students table.

        :param filtered: Optional subset of students to display; if None, show all
        :type filtered: list[Student] | None
        :return: None
        :rtype: None
        """
        data = filtered if filtered is not None else self.db.students
        self.tbl_students.setRowCount(0)
        for s in data:
            row = self.tbl_students.rowCount(); self.tbl_students.insertRow(row)
            courses = ", ".join(getattr(s, "registered_courses", []))
            for col, val in enumerate([s.student_id, s.name, s.age, s._email, courses]):
                self.tbl_students.setItem(row, col, QTableWidgetItem(str(val)))

    def refresh_instructors_table(self, filtered=None):
        """
            Rebuild the Instructors table.

            :param filtered: Optional subset of instructors to display; if None, show all
            :type filtered: list[Instructor] | None
            :return: None
            :rtype: None
            """
        data = filtered if filtered is not None else self.db.instructors
        self.tbl_instructors.setRowCount(0)
        for i in data:
            row = self.tbl_instructors.rowCount(); self.tbl_instructors.insertRow(row)
            assigned = ", ".join(getattr(i, "assigned_courses", []))
            for col, val in enumerate([i.instructor_id, i.name, i.age, i._email, assigned]):
                self.tbl_instructors.setItem(row, col, QTableWidgetItem(str(val)))

    def refresh_courses_table(self, filtered=None):
        """
            Rebuild the Courses table.

            :param filtered: Optional subset of courses to display; if None, show all
            :type filtered: list[Course] | None
            :return: None
            :rtype: None
            """
        data = filtered if filtered is not None else self.db.courses
        self.tbl_courses.setRowCount(0)
        for c in data:
            row = self.tbl_courses.rowCount(); self.tbl_courses.insertRow(row)
            instructor_name = c.instructor.name if getattr(c, "instructor", None) else ""
            enrolled = ", ".join(s.name for s in getattr(c, "enrolled_students", []))
            for col, val in enumerate([c.course_id, c.course_name, instructor_name, enrolled]):
                self.tbl_courses.setItem(row, col, QTableWidgetItem(str(val)))

    def refresh_all_tables(self):
        """
            Refresh all tables (Students, Instructors, Courses).

            :return: None
            :rtype: None
            """
        self.refresh_students_table(); self.refresh_instructors_table(); self.refresh_courses_table()

    # ----- search -----
    def perform_search(self):
        """
            Filter the table for the selected entity (Students/Instructors/Courses)
            by the selected field using the query text. Updates the corresponding table.

            :return: None
            :rtype: None
            """
        entity = self.entity_combo.currentText()
        field  = self.field_combo.currentText()
        q = self.search_edit.text().strip().lower()

        if entity == "Students":
            filtered = []
            for s in self.db.students:
                courses = ", ".join(getattr(s, "registered_courses", []))
                row = [str(s.student_id), s.name, str(s.age), s._email, courses]
                hay = {
                    "All": " ".join(row).lower(),
                    "ID": str(s.student_id).lower(),
                    "Name": s.name.lower(),
                    "Email": s._email.lower(),
                    "Course": courses.lower(),
                }
                if q == "" or q in hay[field]: filtered.append(s)
            self.refresh_students_table(filtered)

        elif entity == "Instructors":
            filtered = []
            for i in self.db.instructors:
                assigned = ", ".join(getattr(i, "assigned_courses", []))
                row = [str(i.instructor_id), i.name, str(i.age), i._email, assigned]
                hay = {
                    "All": " ".join(row).lower(),
                    "ID": str(i.instructor_id).lower(),
                    "Name": i.name.lower(),
                    "Email": i._email.lower(),
                    "AssignedCourse": assigned.lower(),
                }
                if q == "" or q in hay[field]: filtered.append(i)
            self.refresh_instructors_table(filtered)

        else:
            filtered = []
            for c in self.db.courses:
                instr_name = c.instructor.name if getattr(c, "instructor", None) else ""
                students = ", ".join(s.name for s in getattr(c, "enrolled_students", []))
                row = [str(c.course_id), c.course_name, instr_name, students]
                hay = {
                    "All": " ".join(row).lower(),
                    "ID": str(c.course_id).lower(),
                    "Name": c.course_name.lower(),
                    "Instructor": instr_name.lower(),
                    "Student": students.lower(),
                }
                if q == "" or q in hay[field]: filtered.append(c)
            self.refresh_courses_table(filtered)

    def clear_search(self):
        """
        Clear the search box and restore unfiltered tables for all entities.

        :return: None
        :rtype: None
        """
        self.search_edit.clear()
        self.refresh_all_tables()

    # ----- selection helpers -----
    def _selected_student(self):
        """
            Return the currently selected student, or None if no row is selected.

            :return: Selected Student or None
            :rtype: Student | None
            """
        r = self.tbl_students.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Select", "Select a student row first."); return None
        sid = self.tbl_students.item(r, 0).text()
        return next((s for s in self.db.students if str(s.student_id) == sid), None)

    def _selected_instructor(self):
        """
        Return the currently selected instructor, or None if no row is selected.

        :return: Selected Instructor or None
        :rtype: Instructor | None
        """
        r = self.tbl_instructors.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Select", "Select an instructor row first."); return None
        iid = self.tbl_instructors.item(r, 0).text()
        return next((i for i in self.db.instructors if str(i.instructor_id) == iid), None)

    def _selected_course(self):
        """
        Return the currently selected course, or None if no row is selected.

        :return: Selected Course or None
        :rtype: Course | None
        """
        r = self.tbl_courses.currentRow()
        if r < 0:
            QMessageBox.warning(self, "Select", "Select a course row first."); return None
        cid = self.tbl_courses.item(r, 0).text()
        return next((c for c in self.db.courses if str(c.course_id) == cid), None)

    # ----- edit/delete (DB-backed) -----
    def edit_selected_student(self):
        """
            Edit the currently selected student via prompts (name, age, email, ID),
            update the database, then refresh related tables.

            :return: None
            :rtype: None
            """
        s = self._selected_student()
        if not s: return
        name = self._prompt("Edit Name", s.name);                 
        if name is None: return
        age  = self._prompt("Edit Age", str(s.age));               
        if age  is None: return
        email= self._prompt("Edit Email", s._email);               
        if email is None: return
        sid  = self._prompt("Edit Student ID", s.student_id);      
        if sid  is None: return
        try:
            self.db.update_student(
                s.student_id,
                name=name.strip(),
                age=int(age),
                email=email.strip(),
                new_id=(sid.strip() if sid.strip() != s.student_id else None)
            )
            self.refresh_students_table()
            self.refresh_courses_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_selected_student(self):
        """
        Delete the currently selected student after confirmation, then refresh
        related tables.

        :return: None
        :rtype: None
        """
        s = self._selected_student()
        if not s: return
        if QMessageBox.question(self, "Confirm", f"Delete {s.name}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                self.db.delete_student(s.student_id)
                self.refresh_students_table()
                self.refresh_courses_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def edit_selected_instructor(self):
        """
        Edit the currently selected instructor (name, age, email, ID), update
        the database, then refresh related tables.

        :return: None
        :rtype: None
        """
        i = self._selected_instructor()
        if not i: return
        name = self._prompt("Edit Name", i.name);                   
        if name is None: return
        age  = self._prompt("Edit Age", str(i.age));                 
        if age  is None: return
        email= self._prompt("Edit Email", i._email);                 
        if email is None: return
        iid  = self._prompt("Edit Instructor ID", i.instructor_id);  
        if iid  is None: return
        try:
            self.db.update_instructor(
                i.instructor_id,
                name=name.strip(),
                age=int(age),
                email=email.strip(),
                new_id=(iid.strip() if iid.strip() != i.instructor_id else None)
            )
            self.refresh_instructors_table()
            self.refresh_courses_table()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def delete_selected_instructor(self):
        """
            Delete the currently selected instructor after confirmation, then refresh
            related tables.

            :return: None
            :rtype: None
            """
        i = self._selected_instructor()
        if not i: return
        if QMessageBox.question(self, "Confirm", f"Delete {i.name}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                self.db.delete_instructor(i.instructor_id)   # courses should get SET NULL
                self.refresh_instructors_table()
                self.refresh_courses_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def edit_selected_course(self):
        """
        Edit the currently selected course (ID, name, optional instructor name),
        propagate changes through the DB layer, then refresh related tables.

        :raises ValueError: If a provided instructor name does not exist
        :return: None
        :rtype: None
        """
        c = self._selected_course()
        if not c: return
        old_id = c.course_id
        cid   = self._prompt("Edit Course ID", c.course_id);           
        if cid   is None: return
        cname = self._prompt("Edit Course Name", c.course_name);       
        if cname is None: return
        iname = self._prompt("Instructor Name (blank = none)", c.instructor.name 
        if c.instructor else "")
        if iname is None: return
        instr_id = None
        if iname.strip():
            instr = next((x for x in self.db.instructors if x.name == iname.strip()), None)
            if not instr:
                raise ValueError(f"Instructor '{iname}' not found.")
            instr_id = instr.instructor_id

        # Update name/instructor first
        self.db.update_course(old_id, name=cname.strip(), instructor_id=instr_id)
        # Then ID if changed (FK updates/registrations handled in DB layer)
        if cid.strip() and cid.strip() != old_id:
            self.db.update_course(old_id, new_id=cid.strip())

        self.refresh_courses_table()
        self.refresh_students_table()
        self.refresh_instructors_table()

    def delete_selected_course(self):
        """
        Delete the currently selected course after confirmation, then refresh
        related tables.

        :return: None
        :rtype: None
        """
        c = self._selected_course()
        if not c: return
        if QMessageBox.question(self, "Confirm", f"Delete {c.course_name}?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            try:
                self.db.delete_course(c.course_id)
                self.refresh_courses_table()
                self.refresh_students_table()
                self.refresh_instructors_table()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    # ----- Save/Load JSON -----
    def save_json(self):
        """
        Save the current database state to a JSON file.

        :return: None
        :rtype: None
        """ 
        path, _ = QFileDialog.getSaveFileName(self, "Save JSON", "school_data.json", "JSON (*.json)")
        if not path: return
        self.db.save_to_file(path)
        QMessageBox.information(self, "Saved", os.path.basename(path))

    def load_json(self):
        """
        Load a database state from a JSON file.

        :return: None
        :rtype: None
        """
        path, _ = QFileDialog.getOpenFileName(self, "Load JSON", "", "JSON (*.json)")
        if not path: return
        self.db.load_from_file(path)
        self._refresh_reg_dropdowns(); self._refresh_assign_dropdowns()
        self.refresh_all_tables()
        QMessageBox.information(self, "Loaded", os.path.basename(path))

    # ----- Export CSV -----
    def export_csv(self):
        """
        Export students, instructors, and courses to three CSV files:
        students.csv, instructors.csv, and courses.csv in the chosen folder.

        :return: None
        :rtype: None
        """
        folder = QFileDialog.getExistingDirectory(self, "Choose export folder")
        if not folder: return
        try:
            with open(os.path.join(folder, "students.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["ID","Name","Age","Email","RegisteredCourses"])
                for s in self.db.students:
                    w.writerow([s.student_id, s.name, s.age, s._email, "|".join(getattr(s,"registered_courses",[]))])
            with open(os.path.join(folder, "instructors.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["ID","Name","Age","Email","AssignedCourses"])
                for i in self.db.instructors:
                    w.writerow([i.instructor_id, i.name, i.age, i._email, "|".join(getattr(i,"assigned_courses",[]))])
            with open(os.path.join(folder, "courses.csv"), "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f); w.writerow(["ID","Name","Instructor","EnrolledStudents"])
                for c in self.db.courses:
                    instr = c.instructor.name if c.instructor else ""
                    enrolled = "|".join(s.name for s in getattr(c,"enrolled_students",[]))
                    w.writerow([c.course_id, c.course_name, instr, enrolled])
            QMessageBox.information(self, "Exported", f"CSV files saved to:\n{folder}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    # ----- DB Backup -----
    def backup_db(self):
        """
            Backup the SQLite database file to a user-chosen path.

            :return: None
            :rtype: None
            """
        path, _ = QFileDialog.getSaveFileName(self, "Backup SQLite DB", "school_backup.db", "SQLite DB (*.db)")
        if not path:
            return
        self.db.backup_to(path)  # expects SqliteSchoolDB.backup_to()
        QMessageBox.information(self, "Backup", f"Database backed up to:\n{path}")

    # ----- small helpers -----
    def _prompt(self, title, current):
        """
                Modal line-edit dialog used by edit actions.

                :param title: Dialog window title
                :type title: str
                :param current: Initial value placed in the line edit
                :type current: str
                :return: Edited text if user pressed OK, otherwise None
                :rtype: str | None
                """
        dlg = QDialog(self); dlg.setWindowTitle(title)
        lay = QVBoxLayout(dlg); edit = QLineEdit(); edit.setText(current); lay.addWidget(edit)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject); lay.addWidget(bb)
        if dlg.exec_() == QDialog.Accepted:
            return edit.text()
        return None

    # dropdown refresh
    def _refresh_reg_dropdowns(self):
        """
            Refresh the student and course dropdowns used in the registration section.

            :return: None
            :rtype: None
            """
        if hasattr(self, "reg_student_combo"):
            self.reg_student_combo.clear()
            self.reg_student_combo.addItems([f"{s.student_id} - {s.name}" for s in self.db.students])
        if hasattr(self, "reg_course_combo"):
            self.reg_course_combo.clear()
            self.reg_course_combo.addItems([f"{c.course_id} - {c.course_name}" for c in self.db.courses])

    def _refresh_assign_dropdowns(self):
        """
            Refresh the instructor and course dropdowns used in the assignment section.

            :return: None
            :rtype: None
            """
        if hasattr(self, "assign_inst_combo"):
            self.assign_inst_combo.clear()
            self.assign_inst_combo.addItems([f"{i.instructor_id} - {i.name}" for i in self.db.instructors])
        if hasattr(self, "assign_course_combo"):
            self.assign_course_combo.clear()
            self.assign_course_combo.addItems([f"{c.course_id} - {c.course_name}" for c in self.db.courses])


def main():
    """Create the QApplication, show the main window, and start the event loop."""
    app = QApplication(sys.argv)
    window = SchoolManagementSystem()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
