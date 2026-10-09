import sqlite3

conn = sqlite3.connect('gym_log.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise TEXT NOT NULL,
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    date TEXT NOT NULL,
    day_type TEXT NOT NULL
    )
''')

conn.commit()
conn.close()

print("Database initialized successfully.")
