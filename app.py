
from datetime import datetime, date as Date
import sqlite3
import math
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Application limits
MAX_SETS = 100
MAX_REPS = 1000
MAX_WEIGHT = 1000.0
MAX_EXERCISE_LENGTH = 100
MIN_WORKOUT_DATE = Date(1900, 1, 1)


@app.route('/')
def index():
    return render_template('form.html', form=request.form)


@app.route('/log', methods=['POST'])
def log_workout():
    errors = []

    # Exercise validation
    exercise = request.form.get('exercise', '').strip()

    if not exercise:
        errors.append("Exercise name cannot be empty.")
    elif len(exercise) > MAX_EXERCISE_LENGTH:
        errors.append(
            f"Exercise name cannot exceed {MAX_EXERCISE_LENGTH} characters."
        )

    # Sets validation
    try:
        sets = int(request.form.get('sets', ''))

        if not 1 <= sets <= MAX_SETS:
            errors.append(
                f"Sets must be between 1 and {MAX_SETS}."
            )
    except (ValueError, OverflowError):
        sets = 0
        errors.append("Sets must be a valid whole number.")

    # Reps validation
    try:
        reps = int(request.form.get('reps', ''))

        if not 1 <= reps <= MAX_REPS:
            errors.append(
                f"Reps must be between 1 and {MAX_REPS}."
            )
    except (ValueError, OverflowError):
        reps = 0
        errors.append("Reps must be a valid whole number.")

    # Weight validation
    try:
        weight = float(request.form.get('weight', ''))

        if not math.isfinite(weight) or not 0 <= weight <= MAX_WEIGHT:
            errors.append(
                f"Weight must be between 0 and {MAX_WEIGHT:g} kg."
            )
    except (ValueError, OverflowError):
        weight = 0.0
        errors.append("Weight must be a valid number.")

    # Date validation
    date = ''
    try:
        parsed_date = datetime.strptime(
            request.form.get('date', ''), "%Y-%m-%d"
        ).date()
    except ValueError:
        errors.append("Please enter a valid date in YYYY-MM-DD format.")
    else:
        if not MIN_WORKOUT_DATE <= parsed_date <= Date.today():
            errors.append(
                f"Date must be between {MIN_WORKOUT_DATE.isoformat()} and today."
            )
        date = parsed_date.isoformat()

    # Day type validation
    day_type = request.form.get('day_type', '')

    if day_type not in ['Push', 'Pull', 'Legs']:
        errors.append(
            "Please select a valid day type (Push, Pull, or Legs)."
        )

    if errors:
        return render_template(
            'form.html',
            form=request.form,
            errors=errors
        ), 400

    conn = sqlite3.connect('gym_log.db')

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO workouts
                (exercise, sets, reps, weight, date, day_type)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (exercise, sets, reps, weight, date, day_type)
        )

        conn.commit()
    finally:
        conn.close()

    return redirect(url_for('history'))


@app.route('/history')
def history():
    conn = sqlite3.connect('gym_log.db')

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, exercise, sets, reps, weight, date, day_type
            FROM workouts
            ORDER BY date DESC, id DESC
            """
        )

        rows = cursor.fetchall()
    finally:
        conn.close()

    return render_template('history.html', rows=rows)


if __name__ == '__main__':
    app.run(debug=True)
