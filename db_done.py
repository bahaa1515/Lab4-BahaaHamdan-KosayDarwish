from __future__ import annotations

import sqlite3
from typing import Iterable, Any, Optional, List, Tuple

SCHEMA: list[str] = [
    
    """
    CREATE TABLE IF NOT EXISTS students(

            student_id   INTEGER PRIMARY KEY,
   
             name         TEXT    NOT NULL,
        age          INTEGER NOT NULL,
       
         email        TEXT    NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS instructors(
        
        instructor_id INTEGER PRIMARY KEY,
        name          TEXT    NOT NULL,
        age           INTEGER NOT NULL,
        
        email         TEXT    NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS courses(
        course_id    INTEGER PRIMARY KEY,
        
        course_name  TEXT    NOT NULL,
        
        instructor_id INTEGER,
        FOREIGN KEY(instructor_id) REFERENCES instructors(instructor_id)
            ON UPDATE CASCADE ON DELETE SET NULL
    )

    
    """,
    """
    
    CREATE TABLE IF NOT EXISTS enrollments(
        student_id INTEGER NOT NULL,
        course_id  INTEGER NOT NULL,
    
            PRIMARY KEY(student_id, course_id),
        
        FOREIGN KEY(student_id) REFERENCES students(student_id)
        
                ON UPDATE CASCADE ON DELETE CASCADE,
        
        FOREIGN KEY(course_id)  REFERENCES courses(course_id)
        
                ON UPDATE CASCADE ON DELETE CASCADE
    )
    """,
    # Helpfull indexe (will speed up lookups without channging API)

    "CREATE INDEX IF NOT EXISTS idx_students_email    ON students(email)",
    "CREATE INDEX IF NOT EXISTS idx_instructors_email ON instructors(email)",

    "CREATE INDEX IF NOT EXISTS idx_courses_instr     ON courses(instructor_id)",

    "CREATE INDEX IF NOT EXISTS idx_enroll_course     ON enrollments(course_id)",

    "CREATE INDEX IF NOT EXISTS idx_enroll_student    ON enrollments(student_id)",



]


class DB:

    """
    Thin wrapper around sqlite3 with a small, stable API.

        - Enforces foreign keys
    
    - Initializes schema on first use
    - Adds tiny helpers for queries and context use
    
    """


    def __init__(self, path: str = "school.db") -> None:
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA foreign_keys=ON")

        # Row tuples keep compatibikity with existing UI cod

        for stmt in SCHEMA:
            self.conn.execute(stmt)

        self.conn.commit()


    #internal helperss
    def _all(self, q: str, args: Iterable[Any] = ()) -> List[Tuple]:
        cur = self.conn.execute(q, tuple(args))
        
        rows = cur.fetchall()
        cur.close()
        return rows

    def _exec(self, q: str, args: Iterable[Any] = ()) -> None:
        self.conn.execute(q, tuple(args))
        self.conn.commit()

    #students

    def upsert_student(self, student_id: int, name: str, age: int, email: str) -> None:

        self._exec(
            """

                        INSERT INTO students(student_id, name, age, email)
            VALUES(?,?,?,?)
            
            ON CONFLICT(student_id) DO UPDATE SET
                name=excluded.name, age=excluded.age, email=excluded.email
            
            """,
            (student_id, name, age, email),

        )

    def list_students(self) -> List[Tuple]:
       
        return self._all(

            "SELECT student_id, name, age, email FROM students ORDER BY student_id"

        )


    #instructors
    def upsert_instructor(self, instructor_id: int, name: str, age: int, email: str) -> None:
        self._exec(
            """
            INSERT INTO instructors(instructor_id, name, age, email)
    
                    VALUES(?,?,?,?)

                        ON CONFLICT(instructor_id) DO UPDATE SET
            
                    name=excluded.name, age=excluded.age, email=excluded.email
            """,
            (instructor_id, name, age, email),
        )


    def list_instructors(self) -> List[Tuple]:
        return self._all(

            "SELECT instructor_id, name, age, email FROM instructors ORDER BY instructor_id"
        )



    # courses
    def upsert_course(
        self, course_id: int,
          course_name: str, 
          instructor_id: Optional[int] = None

    ) -> None:
        self._exec(

            """
            INSERT INTO courses(course_id, course_name, instructor_id)

                        VALUES(?,?,?)
            
            ON CONFLICT(course_id) DO UPDATE SET
            
                    course_name=excluded.course_name,
                
                instructor_id=excluded.instructor_id

                            """,
            (course_id, 
             course_name, 
             instructor_id),
     
        )
    def assign_instructor(self, course_id: int, instructor_id: int) -> None:
        self._exec(

            "UPDATE courses SET instructor_id=? WHERE course_id=?",

            (instructor_id, 
             course_id),

        )

    def list_courses(self) -> List[Tuple]:
        return self._all(

            """

                        SELECT c.course_id, c.course_name, i.name AS instructor_name, i.email AS instructor_email
            
            FROM courses c
            
            LEFT JOIN instructors i ON c.instructor_id = i.instructor_id
            
            ORDER BY c.course_id
            
            """
     
        )

    #enrrollments
    def enroll(self, student_id: int, course_id: int) -> None:
        self._exec(
     
     
     
     
            "INSERT OR IGNORE INTO enrollments(student_id, course_id) VALUES(?,?)",
            (student_id,
              course_id),
     
        )

    def list_enrollments(self, course_id: int) -> List[Tuple]:
        return self._all(
     
            """
            SELECT s.student_id, s.name, s.email
            FROM enrollments e
     
                   JOIN students s ON s.student_id = e.student_id
            
            WHERE e.course_id = ?
            
            ORDER BY s.student_id
            """,
            (course_id,),
        )


    def close(self) -> None:


        self.conn.close()

    def __enter__(self) -> "DB":

        return self



    def __exit__(self, exc_type, exc, tb) -> None:

        self.close()
