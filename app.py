import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('form.html')


@app.route('/log', methods=['POST'])
def log_workout():

    exercise = request.form['exercise'].strip()
    sets = int(request.form['sets'])
    reps = int(request.form['reps'])
    weight = float(request.form['weight'])
    date = request.form['date']
    day_type = request.form['day_type']

    conn = sqlite3.connect('gym_log.db')
    cursor = conn.cursor()

    cursor.execute("INSERT INTO workouts (exercise, sets, reps, weight, date, day_type) VALUES (?, ?, ?, ?, ?, ?)",
                   (exercise, sets, reps, weight, date, day_type))

    conn.commit()
    conn.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
