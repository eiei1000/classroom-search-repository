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

@app.route('/display', methods=['GET', 'POST'])
def classroom_display():
    # --- この関数内で全ての処理を完結させます ---

    # 1. 変数を初期化
    available_rooms = []
    search_performed = False

    # 2. 各時限に対応する開始・終了時刻を定義
    PERIOD_TIMES = {
        1: (9, 0, 10, 30),   # 1限: 9:00 ~ 10:30
        2: (10, 40, 12, 10), # 2限: 10:40 ~ 12:10
        3: (13, 0, 14, 30),  # 3限: 13:00 ~ 14:30
        4: (14, 40, 16, 10), # 4限: 14:40 ~ 16:10
        5: (16, 20, 17, 50)  # 5限: 16:20 ~ 17:50
    }

    # 3. フォームが送信された場合（POSTリクエスト）の処理
    if request.method == 'POST':
        search_performed = True
        weekday_query = request.form.get('weekday')
        period_query_str = request.form.get('period')

        if weekday_query and period_query_str:
            # --- 教室リストの読み込み ---
            all_classrooms = []
            try:
                with open('classrooms.csv', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        # has_power列が 'true' や '1' の場合にTrueとする
                        row['has_power'] = row.get('has_power', 'false').lower() in ['true', '1', 'yes']
                        all_classrooms.append(row)
            except FileNotFoundError:
                print("Warning: classrooms.csv が見つかりません。")

            # --- スケジュール（予約情報）の読み込み ---
            schedules = {}
            try:
                with open('classroom_schedules.csv', newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        room = row.get('room')
                        weekday = row.get('weekday')
                        start_h_str = row.get('start_hour')
                        end_h_str = row.get('end_hour')
                        if room and weekday and start_h_str and end_h_str:
                            if room not in schedules:
                                schedules[room] = {}
                            if weekday not in schedules[room]:
                                schedules[room][weekday] = []
                            schedules[room][weekday].append((int(start_h_str), int(end_h_str)))
            except FileNotFoundError:
                print("Warning: classroom_schedules.csv が見つかりません。")

            # --- 空き教室の判定 ---
            period_query = int(period_query_str)
            p_start_h, p_start_m, p_end_h, p_end_m = PERIOD_TIMES[period_query]
            period_start_minute = p_start_h * 60 + p_start_m
            period_end_minute = p_end_h * 60 + p_end_m

            # 全ての教室をループ
            for room in all_classrooms:
                room_name = room.get('name')
                is_reserved = False
                
                # この教室に、指定された曜日の予約情報があるか確認
                if room_name in schedules and weekday_query in schedules[room_name]:
                    # 予約されている時間帯をチェック
                    for r_start_h, r_end_h in schedules[room_name][weekday_query]:
                        reserved_start_minute = r_start_h * 60
                        reserved_end_minute = r_end_h * 60
                        
                        # 時間が重複しているかチェック
                        if reserved_start_minute < period_end_minute and reserved_end_minute > period_start_minute:
                            is_reserved = True
                            break # 重複が見つかったのでこの教室のチェックは終了
                
                if not is_reserved:
                    available_rooms.append(room)

    # 4. HTMLテンプレートを表示
    return render_template(
        'classroom_display.html', 
        rooms=available_rooms, 
        search_performed=search_performed, 
        request_form=request.form
    )

if __name__ == '__main__':
    app.run(debug=True)