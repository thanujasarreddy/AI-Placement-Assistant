import sqlite3
from datetime import datetime


def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    """)

    # RESUMES TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        role TEXT,
        score INTEGER,
        skills TEXT,
        timestamp TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()


def save_resume(role, score, skills, user_id):
    print("SAVING RESUME:", role, score, user_id)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO resumes
    (user_id, role, score, skills, timestamp)
    VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        role,
        score,
        ",".join(skills),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_user_resumes(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    SELECT role, score, skills, timestamp
    FROM resumes
    WHERE user_id = ?
    ORDER BY id DESC
    """, (user_id,))

    rows = cursor.fetchall()
    conn.close()

    return rows