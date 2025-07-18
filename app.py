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

# スケジュール読み込み（教室＋曜日で管理）
def load_schedules():
    schedules = {}
    with open('classroom_schedules.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            room = row['room']
            weekday = row['weekday']
            start = int(row['start_hour'])
            end = int(row['end_hour'])
            
            if room not in schedules:
                schedules[room] = {}
            if weekday not in schedules[room]:
                schedules[room][weekday] = []
            schedules[room][weekday].append((start, end))
    return schedules

@app.route('/search', methods=['GET', 'POST'])
def search():
    classrooms = load_classrooms()
    schedules = load_schedules()
    status = None
    classroom = None
    time = datetime.now().strftime("%H:%M")

    # 曜日を取得して「月」「火」形式に変換
    now_weekday_en = datetime.now().strftime("%a")  # Mon, Tue, ...
    weekday_map = {'Mon': '月', 'Tue': '火', 'Wed': '水', 'Thu': '木', 'Fri': '金', 'Sat': '土', 'Sun': '日'}
    weekday = weekday_map[now_weekday_en]

    now_hour = datetime.now().hour

    today_schedule = []  # 今日のその教室のスケジュール一覧

    if request.method == 'POST':
        classroom = request.form.get('classroom')

        # 今日のスケジュールを取得
        if classroom in schedules and weekday in schedules[classroom]:
            today_schedule = schedules[classroom][weekday]
        else:
            today_schedule = []

        # 空きか使用中か判定
        if not today_schedule:
            status = "空き"
        else:
            if any(start <= now_hour < end for start, end in today_schedule):
                status = "使用中"
            else:
                status = "空き"

    return render_template(
        'search.html',
        classrooms=classrooms,
        status=status,
        classroom=classroom,
        time=time,
        weekday=weekday,
        today_schedule=today_schedule  # 追加で渡す
    )

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/display')
def classroom_display():
    return "ここは教室表示画面です"

if __name__ == '__main__':
    app.run(debug=True)