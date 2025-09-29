# school_sqlite.py
import sqlite3, shutil, os
from typing import List, Optional
from school import Student, Instructor, Course  # your validated domain classes

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students(
  student_id TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  age        INTEGER NOT NULL,
  email      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS instructors(
  instructor_id TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  age           INTEGER NOT NULL,
  email         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses(
  course_id     TEXT PRIMARY KEY,
  course_name   TEXT NOT NULL,
  instructor_id TEXT NULL,
  FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id) ON DELETE SET NULL
);

-- join table for student registrations
CREATE TABLE IF NOT EXISTS registrations(
  student_id TEXT NOT NULL,
  course_id  TEXT NOT NULL,
  PRIMARY KEY(student_id, course_id),
  FOREIGN KEY(student_id) REFERENCES students(student_id) ON DELETE CASCADE,
  FOREIGN KEY(course_id)  REFERENCES courses(course_id)  ON DELETE CASCADE
);
"""

class SqliteSchoolDB:
    """
    A thin DB layer that mirrors your in-memory API:
      - add_student / add_instructor / add_course
      - properties students / instructors / courses (returns hydrated domain objects)
      - register_student_in_course
      - assign_instructor_to_course
      - update_* / delete_* helpers
      - backup_to(file_path)
    """
    def __init__(self, path: str = "school.db"):
        self.path = path
        self.con = sqlite3.connect(self.path)
        self.con.execute("PRAGMA foreign_keys = ON;")
        self._create_schema()

    def _create_schema(self):
        self.con.executescript(SCHEMA)
        self.con.commit()

    # ------------------------
    # Create
    # ------------------------
    def add_student(self, s: Student):
        self.con.execute(
            "INSERT INTO students(student_id,name,age,email) VALUES(?,?,?,?)",
            (s.student_id, s.name, s.age, s._email),
        )
        self.con.commit()

    def add_instructor(self, i: Instructor):
        self.con.execute(
            "INSERT INTO instructors(instructor_id,name,age,email) VALUES(?,?,?,?)",
            (i.instructor_id, i.name, i.age, i._email),
        )
        self.con.commit()

    def add_course(self, c: Course):
        instr_id = c.instructor.instructor_id if getattr(c, "instructor", None) else None
        self.con.execute(
            "INSERT INTO courses(course_id,course_name,instructor_id) VALUES(?,?,?)",
            (c.course_id, c.course_name, instr_id),
        )
        self.con.commit()

    # ------------------------
    # Read (lists)
    # ------------------------
    @property
    def students(self) -> List[Student]:
        cur = self.con.execute("SELECT student_id,name,age,email FROM students ORDER BY name")
        rows = cur.fetchall()
        # attach registered courses
        reg_map = {}
        for sid, cid in self.con.execute("SELECT student_id, course_id FROM registrations"):
            reg_map.setdefault(sid, []).append(cid)
        return [Student(name=r[1], age=r[2], email=r[3], student_id=r[0],
                        registered_courses=reg_map.get(r[0], [])) for r in rows]

    @property
    def instructors(self) -> List[Instructor]:
        cur = self.con.execute("SELECT instructor_id,name,age,email FROM instructors ORDER BY name")
        rows = cur.fetchall()
        # derive assigned courses from courses table
        assigned = {}
        for cid, iid in self.con.execute("SELECT course_id, instructor_id FROM courses WHERE instructor_id IS NOT NULL"):
            assigned.setdefault(iid, []).append(cid)
        return [Instructor(name=r[1], age=r[2], email=r[3], instructor_id=r[0],
                           assigned_courses=assigned.get(r[0], [])) for r in rows]

    @property
    def courses(self) -> List[Course]:
        # fetch instructors into a map for quick hydration
        ins_map = {i.instructor_id: i for i in self.instructors}
        cur = self.con.execute("SELECT course_id, course_name, instructor_id FROM courses ORDER BY course_name")
        rows = cur.fetchall()

        # enrolled students map
        enrolled = {}
        for sid, cid in self.con.execute("SELECT student_id, course_id FROM registrations"):
            enrolled.setdefault(cid, []).append(sid)
        # map student id -> Student object
        stu_map = {s.student_id: s for s in self.students}

        courses = []
        for cid, cname, iid in rows:
            instr = ins_map.get(iid)
            enrolled_objs = [stu_map[sid] for sid in enrolled.get(cid, []) if sid in stu_map]
            courses.append(Course(course_id=cid, course_name=cname, instructor=instr,
                                  enrolled_students=enrolled_objs))
        return courses

    # ------------------------
    # Update (simple helpers)
    # ------------------------
    def update_student(self, student_id: str, *, name=None, age=None, email=None, new_id=None):
        if name is not None:
            self.con.execute("UPDATE students SET name=? WHERE student_id=?", (name, student_id))
        if age is not None:
            self.con.execute("UPDATE students SET age=? WHERE student_id=?", (age, student_id))
        if email is not None:
            self.con.execute("UPDATE students SET email=? WHERE student_id=?", (email, student_id))
        if new_id is not None and new_id != student_id:
            # cascade registrations due to PK change
            self.con.execute("UPDATE registrations SET student_id=? WHERE student_id=?", (new_id, student_id))
            self.con.execute("UPDATE students SET student_id=? WHERE student_id=?", (new_id, student_id))
        self.con.commit()

    def update_instructor(self, instructor_id: str, *, name=None, age=None, email=None, new_id=None):
        if name is not None:
            self.con.execute("UPDATE instructors SET name=? WHERE instructor_id=?", (name, instructor_id))
        if age is not None:
            self.con.execute("UPDATE instructors SET age=? WHERE instructor_id=?", (age, instructor_id))
        if email is not None:
            self.con.execute("UPDATE instructors SET email=? WHERE instructor_id=?", (email, instructor_id))
        if new_id is not None and new_id != instructor_id:
            self.con.execute("UPDATE courses SET instructor_id=? WHERE instructor_id=?", (new_id, instructor_id))
            self.con.execute("UPDATE instructors SET instructor_id=? WHERE instructor_id=?", (new_id, instructor_id))
        self.con.commit()

    def update_course(self, course_id: str, *, name=None, instructor_id: Optional[str] = None, new_id=None):
        if name is not None:
            self.con.execute("UPDATE courses SET course_name=? WHERE course_id=?", (name, course_id))
        if instructor_id is not None:  # can be None = unassign
            self.con.execute("UPDATE courses SET instructor_id=? WHERE course_id=?", (instructor_id, course_id))
        if new_id is not None and new_id != course_id:
            self.con.execute("UPDATE registrations SET course_id=? WHERE course_id=?", (new_id, course_id))
            self.con.execute("UPDATE courses SET course_id=? WHERE course_id=?", (new_id, course_id))
        self.con.commit()

    # ------------------------
    # Delete
    # ------------------------
    def delete_student(self, student_id: str):
        self.con.execute("DELETE FROM students WHERE student_id=?", (student_id,))
        self.con.commit()

    def delete_instructor(self, instructor_id: str):
        # ON DELETE SET NULL will unassign courses automatically
        self.con.execute("DELETE FROM instructors WHERE instructor_id=?", (instructor_id,))
        self.con.commit()

    def delete_course(self, course_id: str):
        self.con.execute("DELETE FROM courses WHERE course_id=?", (course_id,))
        self.con.commit()

    # ------------------------
    # Enrollment & assignment
    # ------------------------
    def register_student_in_course(self, student_id: str, course_id: str):
        self.con.execute(
            "INSERT OR IGNORE INTO registrations(student_id, course_id) VALUES(?,?)",
            (student_id, course_id),
        )
        self.con.commit()

    def assign_instructor_to_course(self, instructor_id: Optional[str], course_id: str):
        self.con.execute("UPDATE courses SET instructor_id=? WHERE course_id=?", (instructor_id, course_id))
        self.con.commit()

    # ------------------------
    # Backup
    # ------------------------
    def backup_to(self, dest_path: str):
        # safest: sqlite iterdump
        with sqlite3.connect(dest_path) as out:
            for line in self.con.iterdump():
                out.execute(line)
            out.commit()

    # optional convenience close
    def close(self):
        try: self.con.close()
        except: pass
