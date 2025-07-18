import csv
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

# 教室リスト読み込み
def load_classrooms():
    classrooms = []
    with open('classrooms.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            classrooms.append(row['room'])
    return classrooms

# スケジュール読み込み（教室＋曜日で管理、時間＋分）
def load_schedules():
    schedules = {}
    with open('classroom_schedules.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            room = row['room']
            weekday = row['weekday']
            try:
                start_hour = int(row['start_hour'])
                start_minute = int(row['start_minute'])
                end_hour = int(row['end_hour'])
                end_minute = int(row['end_minute'])
            except (ValueError, TypeError):
                # 空欄の行はスキップ
                continue
            
            if room not in schedules:
                schedules[room] = {}
            if weekday not in schedules[room]:
                schedules[room][weekday] = []
            schedules[room][weekday].append((start_hour, start_minute, end_hour, end_minute))
    return schedules

@app.route('/search', methods=['GET', 'POST'])
def search():
    classrooms = load_classrooms()
    schedules = load_schedules()
    status = None
    classroom = None
    time = datetime.now().strftime("%H:%M")

    # 今日の曜日（日本語）取得
    now_weekday_en = datetime.now().strftime("%a")  # Mon, Tue, ...
    weekday_map = {'Mon': '月', 'Tue': '火', 'Wed': '水', 'Thu': '木', 'Fri': '金', 'Sat': '土', 'Sun': '日'}
    weekday = weekday_map[now_weekday_en]

    now = datetime.now()

    today_schedule = []

    if request.method == 'POST':
        classroom = request.form.get('classroom')

        if classroom in schedules and weekday in schedules[classroom]:
            today_schedule = schedules[classroom][weekday]
        else:
            today_schedule = []

        # 現在の時刻が含まれているか判定
        status = "空き"
        for start_hour, start_minute, end_hour, end_minute in today_schedule:
            start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
            end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
            if start_time <= now < end_time:
                status = "使用中"
                break

    return render_template(
        'search.html',
        classrooms=classrooms,
        status=status,
        classroom=classroom,
        time=time,
        weekday=weekday,
        today_schedule=today_schedule
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/display')
def classroom_display():
    return "ここは教室表示画面です"

if __name__ == '__main__':
    app.run(debug=True)