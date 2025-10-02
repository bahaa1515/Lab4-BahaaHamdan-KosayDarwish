# Lab4-BahaaHamdan-KosayDarwish
A project combining Tkinter and PyQt documented implementations

##  Project Overview  
This project demonstrates collaborative software development using **Git branching** and **Python GUI frameworks**.  

- **Bahaa Hamdan** implemented the **Tkinter UI**.  
- **Kosay Darwish** implemented the **PyQt UI**.  
- PyQt UI has a backend (`school.py`) and database logic (`school_sqlite.py`).  

The system allows basic school management functionalities (students, instructors, courses) stored in an SQLite database (`school.db`).  

---

## 🛠 Requirements  

- Python **3.10+**  
- Virtual environment (recommended)  
- Dependencies:  
  ```bash
  pip install pyqt5


🚀 Setup Instructions
1. Clone the Repository
   ```bash
   git clone https://github.com/username/Lab4-Student1_Student2.git
   cd Lab4-Student1_Student2

3. Create and Activate Virtual Environment

Windows (PowerShell):
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```
3. Install Dependencies
```bash
pip install -r requirements.txt
```

(or simply pip install pyqt5 if requirements file is missing)

💻 How to Run

Tkinter Interface
```bash
python app_tk_done.py
```
PyQt Interface
```bash
python school_qt.py
```

🖱️ How to Use the Application

Tkinter Interface

Run the Tkinter program:
```bash
python app_tk_done.py
```

A Tkinter window will open.

Available actions:

-Add Student / Instructor → Fill in the fields and click the “Add” button.

-Add Course → Enter course details and save.

-Enroll Student in Course → Select a student and course, then confirm.

-View Records → Use the records tab to see all entries in the database.


PyQt Interface

Run the PyQt program:
```bash
python school_qt.py
```

A PyQt window will open with tabbed navigation.

Available actions:

-Manage Students → Add, update, or view student details.

-Manage Instructors → Add and view instructor information.

-Manage Courses → Add new courses and view the list.

-Records Tab → Browse students, instructors, and courses stored in the SQLite database.



