import os

class Config:
    # Ensure the data folder exists and define the SQLite database URI
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    os.makedirs(DATA_DIR, exist_ok=True)  # Create 'data' folder if it doesn't exist

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(DATA_DIR, 'student_project.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
