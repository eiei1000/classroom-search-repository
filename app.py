import csv
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

WEEKDAYS_JP = ['月', '火', '水', '木', '金']
WEEKDAY_MAP_EN_JP = {'Mon': '月', 'Tue': '火', 'Wed': '水', 'Thu': '木', 'Fri': '金', 'Sat': '土', 'Sun': '日'}

PERIOD_TIMES = {
    1: (8, 30, 10, 0),
    2: (10, 20, 11, 50),
    3: (12, 50, 14, 20),
    4: (14, 40, 16, 10),
    5: (16, 20, 17, 50)
}

def load_classrooms():
    classrooms = []
    try:
        with open('classrooms.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('room'):
                    classrooms.append({'room': row['room']})
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
                    if not all([row.get('start_hour'), row.get('start_minute'), row.get('end_hour'), row.get('end_minute')]):
                        continue
                    sh = int(row['start_hour'])
                    sm = int(row['start_minute'])
                    eh = int(row['end_hour'])
                    em = int(row['end_minute'])
                except (ValueError, TypeError):
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
    schedules_data = load_schedules()
    
    selected_classroom = None
    current_status = None
    schedule_matrix = None

    now = datetime.now()
    weekday_en = now.strftime("%a")
    weekday_jp = WEEKDAY_MAP_EN_JP.get(weekday_en, '')
    time_now_str = now.strftime("%H:%M")

    if request.method == 'POST':
        selected_classroom = request.form.get('classroom')
        
        if selected_classroom:
            today_reservations = schedules_data.get(selected_classroom, {}).get(weekday_jp, [])
            current_status = "空き"
            for sh, sm, eh, em in today_reservations:
                start_time = now.replace(hour=sh, minute=sm, second=0, microsecond=0)
                end_time = now.replace(hour=eh, minute=em, second=0, microsecond=0)
                if start_time <= now < end_time:
                    current_status = "使用中"
                    break

            schedule_matrix = {}
            for period in range(1, 6):
                schedule_matrix[period] = {}
                ps_h, ps_m, pe_h, pe_m = PERIOD_TIMES[period]
                period_start_mins = ps_h * 60 + ps_m
                period_end_mins = pe_h * 60 + pe_m

                for day in WEEKDAYS_JP:
                    is_reserved = False
                    day_reservations = schedules_data.get(selected_classroom, {}).get(day, [])
                    
                    for sh, sm, eh, em in day_reservations:
                        res_start_mins = sh * 60 + sm
                        res_end_mins = eh * 60 + em
                        
                        if res_start_mins < period_end_mins and res_end_mins > period_start_mins:
                            is_reserved = True
                            break
                    
                    schedule_matrix[period][day] = "利用不可" if is_reserved else "空き"

    return render_template(
        'search.html',
        classrooms=classrooms,
        classroom=selected_classroom,
        status=current_status,
        time=time_now_str,
        weekday=weekday_jp,
        schedule_matrix=schedule_matrix
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

            for room_data in classrooms:
                room_name = room_data.get('room')
                is_reserved = False
                entries = schedules.get(room_name, {}).get(weekday_query, [])

                for sh, sm, eh, em in entries:
                    res_start = sh * 60 + sm
                    res_end = eh * 60 + em

                    if res_start < period_end and res_end > period_start:
                        is_reserved = True
                        break

                if not is_reserved:
                    available_rooms.append(room_name)

    return render_template(
        'classroom_display.html',
        rooms=available_rooms,
        search_performed=search_performed,
        request_form=request.form
    )

if __name__ == '__main__':
    app.run(debug=True)
