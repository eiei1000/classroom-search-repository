import csv
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

# 曜日英→日変換辞書
WEEKDAY_MAP = {'Mon': '月曜日', 'Tue': '火曜日', 'Wed': '水曜日', 'Thu': '木曜日', 'Fri': '金曜日', 'Sat': '土曜日', 'Sun': '日曜日'}

# 時限定義（分単位で比較しやすく）
PERIOD_TIMES = {
    1: (8, 30, 10, 30),
    2: (10, 50, 11, 50),
    3: (12, 50, 14, 0),
    4: (14, 40, 16, 10),
    5: (16, 20, 17, 50)
}

def load_classrooms():
    classrooms = []
    try:
        with open('classrooms.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # 'room' カラムから教室名を取得し、辞書として格納
                classrooms.append({'room': row.get('room', '')})
    except FileNotFoundError:
        print("classrooms.csv が見つかりません。")
    return classrooms

def load_schedules():
    schedules = {}
    try:
        with open('classroom_schedules.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                room = row.get('room')
                weekday = row.get('weekday')
                try:
                    sh = int(row.get('start_hour', 0))
                    sm = int(row.get('start_minute', 0))
                    eh = int(row.get('end_hour', 0))
                    em = int(row.get('end_minute', 0))
                except ValueError:
                    continue

                if not (room and weekday):
                    continue

                if room not in schedules:
                    schedules[room] = {}
                if weekday not in schedules[room]:
                    schedules[room][weekday] = []

                schedules[room][weekday].append((sh, sm, eh, em))
    except FileNotFoundError:
        print("classroom_schedules.csv が見つかりません。")
    return schedules

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    classrooms = load_classrooms()
    schedules = load_schedules()
    classroom = None
    status = None
    today_schedule = []

    now = datetime.now()
    weekday_en = now.strftime("%a")
    weekday = WEEKDAY_MAP[weekday_en]
    time_now = now.strftime("%H:%M")

    if request.method == 'POST':
        classroom = request.form.get('classroom')
        today_schedule = schedules.get(classroom, {}).get(weekday, [])

        status = "空き"
        for sh, sm, eh, em in today_schedule:
            start = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
            end = now.replace(hour=eh, minute=em, second=0, microsecond=0)
            if start <= now < end:
                status = "使用中"
                break

    return render_template(
        'search.html',
        classrooms=classrooms,
        classroom=classroom,
        status=status,
        time=time_now,
        weekday=weekday,
        today_schedule=today_schedule
    )

@app.route('/display', methods=['GET', 'POST'])
def classroom_display():
    available_rooms = []
    search_performed = False

    if request.method == 'POST':
        search_performed = True
        weekday_query = request.form.get('weekday')
        period_str = request.form.get('period')

        if weekday_query and period_str:
            period = int(period_str)
            ps_h, ps_m, pe_h, pe_m = PERIOD_TIMES[period]
            period_start = ps_h * 60 + ps_m
            period_end = pe_h * 60 + pe_m

            classrooms = load_classrooms()
            schedules = load_schedules()

            for room in classrooms:
                room_name = room.get('room')
                is_reserved = False
                entries = schedules.get(room_name, {}).get(weekday_query, [])

                for sh, sm, eh, em in entries:
                    res_start = sh * 60 + sm
                    res_end = eh * 60 + em

                    # 重複判定：予約開始 < 検索終了 AND 予約終了 > 検索開始
                    if res_start < period_end and res_end > period_start:
                        is_reserved = True
                        break

                if not is_reserved:
                    # 教室名の文字列をリストに追加
                    available_rooms.append(room_name)

    return render_template(
        'classroom_display.html',
        rooms=available_rooms,
        search_performed=search_performed,
        request_form=request.form
    )

if __name__ == '__main__':
    app.run(debug=True)