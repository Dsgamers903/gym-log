
from datetime import datetime, date as Date
import base64
import io
import sqlite3
import math
from flask import Flask, render_template, request, redirect, url_for
import matplotlib.dates as mdates
from matplotlib.figure import Figure

app = Flask(__name__)

# Application limits
MAX_SETS = 100
MAX_REPS = 1000
MAX_WEIGHT = 1000.0
MAX_EXERCISE_LENGTH = 100
MIN_WORKOUT_DATE = Date(1900, 1, 1)


def build_progress_chart(points, exercise):
    dates = [Date.fromisoformat(point[0]) for point in points]
    weights = [point[1] for point in points]

    fig = Figure()
    ax = fig.subplots()
    ax.plot(dates, weights, marker='o')

    ax.set_title(f'Progress for {exercise}')
    ax.set_xlabel('Date')
    ax.set_ylabel('Weight (kg)')
    ax.set_xticks(dates)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d %b'))
    fig.autofmt_xdate()

    buf = io.BytesIO()
    fig.savefig(buf, format='png')

    return base64.b64encode(buf.getvalue()).decode('ascii')


@app.route('/')
def index():
    return render_template('form.html', form=request.form)


@app.route('/log', methods=['POST'])
def log_workout():
    errors = []

    # Exercise validation
    exercise = request.form.get('exercise', '').strip().title()
    exercise = ' '.join(exercise.split())

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


@app.route('/stats')
def stats():
    conn = sqlite3.connect('gym_log.db')

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT exercise,
                   SUM(sets * reps * weight) AS total_volume
            FROM workouts
            GROUP BY exercise
            ORDER BY total_volume DESC
            """
        )
        volume_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT exercise,
                   MAX(weight) AS heaviest_weight
            FROM workouts
            GROUP BY exercise
            ORDER BY heaviest_weight DESC
            """
        )
        heaviest_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT day_type,
                   COUNT(DISTINCT date) AS sessions
            FROM workouts
            GROUP BY day_type
            ORDER BY sessions DESC
            """
        )
        session_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT DISTINCT exercise
            FROM workouts
            ORDER BY exercise
            """
        )
        exercises = [row[0] for row in cursor.fetchall()]

        selected = request.args.get('exercise')

        if selected not in exercises:
            selected = exercises[0] if exercises else None

        if selected is not None:
            cursor.execute(
                """
                SELECT date, MAX(weight)
                FROM workouts
                WHERE exercise = ?
                GROUP BY date
                ORDER BY date
                """,
                (selected,)
            )
            points = cursor.fetchall()
        else:
            points = []

    finally:
        conn.close()

    chart_data = build_progress_chart(points, selected) if points else None

    return render_template(
        'stats.html',
        volume_rows=volume_rows,
        heaviest_rows=heaviest_rows,
        session_rows=session_rows,
        exercises=exercises,
        selected=selected,
        chart_data=chart_data
    )


if __name__ == '__main__':
    app.run(debug=True)
