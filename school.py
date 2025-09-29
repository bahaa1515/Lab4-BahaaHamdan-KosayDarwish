"""
Core domain models and utilities for the School Management System.

This module defines validation helpers, entity models (`Person`, `Student`,
`Instructor`, `Course`) and a simple in-memory database adapter (`School_DB`).
The models provide (de)serialization helpers to/from dictionaries for use when
persisting to JSON files.
"""

import json
import re

def validate_email(email):
    """Validate an email address string.

    :param email: Email string to validate
    :type email: str
    :return: True if valid
    :rtype: bool
    :raises ValueError: If the email format is invalid
    """
    pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if re.match(pattern, email):
        return True
    else:
        raise ValueError("Invalid email format")
    
def validate_age(age):
    """Validate a non-negative age value.

    :param age: Age value (expected non-negative integer)
    :type age: int
    :return: None
    :rtype: None
    :raises ValueError: If age is negative
    """
    if(age<0):
        raise ValueError("Age must be non-negative integer")

class Person:
    """Base class for people in the system.

    :param name: Person's full name
    :type name: str
    :param age: Person's age (non-negative)
    :type age: int
    :param email: Person's email (validated)
    :type email: str
    :raises ValueError: If email or age are invalid
    """

    def __init__(self, name, age,email):
        validate_email(email)
        validate_age(age)
        self.name=name
        self._email=email
        self.age=age
    
    def introduce(self):
        """Print an introduction string for the person."""
        print(f"Hello, I am {self.name}, I am {self.age} years old. You can reach me at {self._email}.")

    def save_to_dict(self):
        """Serialize the person to a dictionary suitable for JSON."""
        return{
            "name":self.name,
            "age":self.age,
            "email":self._email
        }

class Student(Person):
    """A student with an ID and registered course IDs.

    :param name: Student's name
    :param age: Student's age
    :param email: Student's email
    :param student_id: Unique student identifier
    :param registered_courses: Optional list of course IDs the student is registered in
    """

    def __init__(self, name, age,email, student_id, registered_courses=None):
        super().__init__(name, age,email)
        self.student_id=student_id
        if registered_courses is None:
            self.registered_courses=[]
        else:
            self.registered_courses=registered_courses

    def register_course(self, course):
        """Register the student in a course by course ID or name.

        :param course: Course identifier (string) to add
        :type course: str
        """
        self.registered_courses.append(course)
        print(f"{self.name} has registered for the course: {course} successfully.")

    def save_to_dict(self):
        """Serialize the student to a dictionary (extends ``Person.save_to_dict``)."""
        data=super().save_to_dict()
        data.update({
            "student_id":self.student_id,
            "registered_courses":self.registered_courses
        })
        return data

    @classmethod
    def from_dict(cls, data):
        """Create a ``Student`` from a serialized dictionary."""
        return cls(
            name=data["name"],
            age=data["age"],
            email=data["email"],
            student_id=data["student_id"],
            registered_courses=data["registered_courses"]
        )

class Instructor(Person): 
    """An instructor with an ID and assigned course IDs.

    :param name: Instructor's name
    :param age: Instructor's age
    :param email: Instructor's email
    :param instructor_id: Unique instructor identifier
    :param assigned_courses: Optional list of course IDs the instructor teaches
    """

    def __init__(self, name, age, email, instructor_id, assigned_courses=None):
        super().__init__(name, age, email)
        self.instructor_id=instructor_id
        if assigned_courses is None:
            self.assigned_courses=[]     
        else:
            self.assigned_courses=assigned_courses

    def assign_course(self, course):
        """Assign a course by course ID or name to the instructor if not already assigned."""
        if course not in self.assigned_courses:

            self.assigned_courses.append(course)
            print(f"{self.name} has been assigned to teach the course: {course} successfully.")
        else:
            print("Already assigned!")

    def save_to_dict(self):
        """Serialize the instructor to a dictionary (extends ``Person.save_to_dict``)."""
        data=super().save_to_dict()
        data.update({
            "instructor_id":self.instructor_id,
            "assigned_courses":self.assigned_courses
        })
        return data
    
    @classmethod
    def from_dict(cls, data):
        """Create an ``Instructor`` from a serialized dictionary."""
        return cls(
            name=data["name"],
            age=data["age"],
            email=data["email"],
            instructor_id=data["instructor_id"],
            assigned_courses=data["assigned_courses"]
        )
    
class Course:
    """A course taught by an ``Instructor`` with enrolled ``Student``s.

    :param course_id: Unique course identifier
    :param course_name: Human-readable name
    :param instructor: Optional ``Instructor`` teaching the course
    :param enrolled_students: Optional list of ``Student`` objects
    """

    def __init__(self, course_id,course_name, instructor, enrolled_students=None):
        self.course_id=course_id
        self.course_name=course_name
        self.instructor=instructor
        if enrolled_students is None:
           self.enrolled_students=[]
        else:
            self.enrolled_students=enrolled_students 

    def add_student(self, student): 
        """Enroll a ``Student`` instance in the course if not already enrolled."""
        if student  not in self.enrolled_students:
            self.enrolled_students.append(student)
            print(f"{student.name} has been added to the course: {self.course_name} successfully.")

        else:
            print("This student is already enrolled!")

    def save_to_dict(self):
        """Serialize the course to a dictionary, including nested instructor and students."""
        return {
            "course_id": self.course_id,
            "course_name": self.course_name,
            "instructor": self.instructor.save_to_dict() if self.instructor else None,
            "enrolled_students": [s.save_to_dict() for s in self.enrolled_students],
        }

    @classmethod
    def from_dict(cls, data):
        """Create a ``Course`` from a serialized dictionary (recursively deserializes nested objects)."""
        instructor = Instructor.from_dict(data["instructor"]) if data.get("instructor") else None
        enrolled_students = [Student.from_dict(s) for s in data.get("enrolled_students", [])]
        return cls(
            course_id=data["course_id"],
            course_name=data["course_name"],
            instructor=instructor,
            enrolled_students=enrolled_students
        )


class School_DB:
    """Simple in-memory storage for students, instructors, and courses with JSON persistence."""
    def __init__(self):
        self.students=[]
        self.instructors=[]
        self.courses=[]

    def add_student(self, student):
        """Add a ``Student`` to the database."""
        self.students.append(student)
        print(f"Student {student.name} added to the school database successfully.")

    def add_instructor(self, instructor):
        """Add an ``Instructor`` to the database."""
        self.instructors.append(instructor)
        print(f"Instructor {instructor.name} added to the school database successfully.")

    def add_course(self, course):
        """Add a ``Course`` to the database."""
        self.courses.append(course)
        print(f"Course {course.course_name} added to the school database successfully.")

    def save_to_file(self, filename):
        """Persist the database to a JSON file.

        :param filename: Path to output file
        :type filename: str
        """
        data={
            "students":[student.save_to_dict() for student in self.students],
            "instructors":[instructor.save_to_dict() for instructor in self.instructors],
            "courses":[course.save_to_dict() for course in self.courses]
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"School database saved to {filename} successfully.")

    def load_from_file(self, filename):
        """Load the database contents from a JSON file.

        :param filename: Path to JSON input file
        :type filename: str
        """
        with open(filename, 'r') as f:
            data=json.load(f)
        
        self.students=[Student.from_dict(s) for s in data["students"]]
        self.instructors=[Instructor.from_dict(i) for i in data["instructors"]]
        self.courses=[Course.from_dict(c) for c in data["courses"]]
        
        print(f"School database loaded from {filename} successfully.")