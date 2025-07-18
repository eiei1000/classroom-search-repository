import csv
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

def load_classrooms():
    classrooms = []
    with open('classrooms.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            classrooms.append(row['room'])
    return classrooms

def load_schedules():
    schedules = {}
    with open('classroom_schedules.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            room = row['room']
            start = int(row['start_hour'])
            end = int(row['end_hour'])
            if room not in schedules:
                schedules[room] = []
            schedules[room].append((start, end))
    return schedules

@app.route('/search', methods=['GET', 'POST'])
def search():
    classrooms = load_classrooms()
    schedules = load_schedules()
    status = None
    classroom = None
    time = datetime.now().strftime("%H:%M")
    now_hour = datetime.now().hour

    if request.method == 'POST':
        classroom = request.form.get('classroom')

        if classroom not in schedules:
            # スケジュールがなければ空きとみなす
            status = "空き"
        else:
            # 今の時刻がどの使用時間にも含まれなければ空き
            if any(start <= now_hour < end for start, end in schedules[classroom]):
                status = "使用中"
            else:
                status = "空き"

    return render_template('search.html', classrooms=classrooms, status=status, classroom=classroom, time=time)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)