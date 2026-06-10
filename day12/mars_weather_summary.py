#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''화성 날씨 CSV → MySQL 적재 및 요약 PNG 저장.'''

import csv
import getpass
import importlib.util
import os
import struct
import zlib
from datetime import datetime, timedelta

import mysql.connector

# 설정
CSV_FILENAME = 'mars_weathers_data.csv'
PNG_FILENAME = 'mars_weather_summary.png'
SQL_FILENAME = 'create_mars_weather.sql'

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'codyssey',
}

LOCAL_CONFIG_FILENAME = 'db_config.local.py'


def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def _resolve_csv_path():
    base = _script_dir()
    for name in (CSV_FILENAME, 'mars_weathers_data.CSV'):
        path = os.path.join(base, name)
        if os.path.isfile(path):
            return path
    return os.path.join(base, CSV_FILENAME)


# DB 접속 설정
def resolve_db_config():
    config = dict(DB_CONFIG)

    local_path = os.path.join(_script_dir(), LOCAL_CONFIG_FILENAME)
    if os.path.isfile(local_path):
        spec = importlib.util.spec_from_file_location('db_config_local', local_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, 'DB_CONFIG'):
            config.update(module.DB_CONFIG)
        if hasattr(module, 'MYSQL_PASSWORD'):
            config['password'] = module.MYSQL_PASSWORD

    env_password = os.environ.get('MYSQL_PASSWORD')
    if env_password is not None:
        config['password'] = env_password

    if not config.get('password'):
        prompt = f"MySQL 비밀번호 ({config.get('user', 'root')}): "
        config['password'] = getpass.getpass(prompt)

    return config


# CSV 읽기
def read_and_print_csv(path):
    rows = []
    try:
        with open(path, 'r', encoding='utf-8-sig', newline='') as file_obj:
            reader = csv.reader(file_obj)
            for raw_row in reader:
                if not raw_row or all(not cell.strip() for cell in raw_row):
                    continue
                rows.append(raw_row)
                print(','.join(raw_row))
    except FileNotFoundError:
        print(f'오류: CSV 파일을 찾을 수 없습니다: {path}')
        return []
    except OSError as err:
        print(f'CSV 읽기 오류: {err}')
        return []

    if not rows:
        print('CSV에 데이터가 없습니다.')
    return rows


def _normalize_header(cell):
    return cell.strip().lower().replace(' ', '_')


def _to_int(value):
    return int(round(float(value.strip())))


# CSV 파싱
def _parse_csv_rows(raw_rows):
    if not raw_rows:
        return []

    first = [cell.strip() for cell in raw_rows[0]]
    header_map = {_normalize_header(cell): idx for idx, cell in enumerate(first)}

    if 'stom' in header_map and 'storm' not in header_map:
        header_map['storm'] = header_map['stom']

    required = {'mars_date', 'temp', 'storm'}
    has_header = required.issubset(header_map.keys())
    data_rows = raw_rows[1:] if has_header else raw_rows

    records = []
    for row in data_rows:
        cells = [cell.strip() for cell in row]
        if len(cells) < 3:
            continue

        if has_header:
            if len(cells) <= max(header_map.values()):
                continue
            mars_date = cells[header_map['mars_date']]
            temp = _to_int(cells[header_map['temp']])
            storm = _to_int(cells[header_map['storm']])
        elif len(cells) == 4:
            mars_date = cells[1]
            temp = _to_int(cells[2])
            storm = _to_int(cells[3])
        else:
            mars_date = cells[0]
            temp = _to_int(cells[1])
            storm = _to_int(cells[2])

        records.append({
            'mars_date': mars_date,
            'temp': temp,
            'storm': storm,
        })
    return records


# INSERT SQL 변환
def row_to_insert_sql(record):
    mars_date = record['mars_date'].replace("'", "''")
    temp = record['temp']
    storm = record['storm']
    return (
        'INSERT INTO mars_weather (mars_date, temp, storm) '
        f"VALUES ('{mars_date}', {temp}, {storm});"
    )


# MySQLHelper
class MySQLHelper:

    def __init__(self, config):
        self.config = dict(config)
        self.connection = None
        self.cursor = None

    def connect(self):
        self.connection = mysql.connector.connect(**self.config)
        self.cursor = self.connection.cursor()
        return self.connection

    def execute(self, query, params=None):
        if self.cursor is None:
            raise RuntimeError('데이터베이스에 연결되어 있지 않습니다.')
        self.cursor.execute(query, params or ())
        return self.cursor

    def fetchall(self):
        if self.cursor is None:
            return []
        return self.cursor.fetchall()

    def commit(self):
        if self.connection is not None:
            self.connection.commit()

    def close(self):
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None


def _load_create_table_sql():
    path = os.path.join(_script_dir(), SQL_FILENAME)
    if not os.path.isfile(path):
        return (
            'CREATE TABLE IF NOT EXISTS mars_weather ('
            'weather_id INT NOT NULL AUTO_INCREMENT, '
            'mars_date DATETIME NOT NULL, '
            'temp INT NOT NULL, '
            'storm INT NOT NULL, '
            'PRIMARY KEY (weather_id)'
            ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;'
        )

    with open(path, 'r', encoding='utf-8') as file_obj:
        text = file_obj.read()

    statements = []
    for part in text.split(';'):
        cleaned = part.strip()
        if cleaned:
            statements.append(cleaned)
    return statements


# DB 준비
def setup_database(helper):
    db_name = helper.config.get('database', 'codyssey')
    bootstrap = dict(helper.config)
    bootstrap.pop('database', None)

    root = MySQLHelper(bootstrap)
    root.connect()
    root.execute(
        f"CREATE DATABASE IF NOT EXISTS {db_name} "
        'DEFAULT CHARACTER SET utf8mb4 '
        'DEFAULT COLLATE utf8mb4_unicode_ci'
    )
    root.commit()
    root.close()

    helper.connect()
    for statement in _load_create_table_sql():
        upper = statement.upper()
        if upper.startswith('CREATE DATABASE') or upper.startswith('USE '):
            continue
        helper.execute(statement)
    helper.commit()
    helper.execute('DELETE FROM mars_weather')
    helper.commit()


# INSERT 반복 실행
def insert_records(helper, records):
    for record in records:
        sql = row_to_insert_sql(record)
        print(sql)
        helper.execute(sql)
    helper.commit()


# 조회
def fetch_weather_rows(helper):
    helper.execute(
        'SELECT mars_date, temp, storm FROM mars_weather '
        'ORDER BY mars_date ASC'
    )
    return helper.fetchall()


def _parse_db_datetime(value):
    if isinstance(value, datetime):
        return value
    return datetime.strptime(str(value), '%Y-%m-%d %H:%M:%S')


# 요약
def build_summary_text(rows):
    if not rows:
        return '데이터 없음', ['No data']

    dates = [_parse_db_datetime(row[0]) for row in rows]
    temps = [row[1] for row in rows]
    storms = [row[2] for row in rows]

    last_date = max(dates)
    travel_date = last_date + timedelta(days=1)
    storm_days = [d.strftime('%Y-%m-%d') for d, s in zip(dates, storms) if s != 0]

    on_travel = any(
        d.date() == travel_date.date() and s != 0
        for d, s in zip(dates, storms)
    )
    avg_temp = sum(temps) / len(temps)

    if on_travel:
        forecast_ko = '이동일 모래 폭풍 주의'
        forecast_en = 'Storm risk on travel day'
    else:
        forecast_ko = '내일 날씨는 맑음 (폭풍 없음)'
        forecast_en = 'Tomorrow weather is clear'

    console_lines = [
        '=== 화성 날씨 요약 ===',
        f'기록 수: {len(rows)}',
        f'평균 온도: {avg_temp:.1f}°C',
        f'폭풍 일수: {len(storm_days)}',
        f'이동 예정일: {travel_date.strftime("%Y-%m-%d")}',
        forecast_ko,
    ]
    if storm_days:
        console_lines.append('폭풍 날짜: ' + ', '.join(storm_days))

    png_lines = [
        'Mars Weather Summary',
        f'Records: {len(rows)}',
        f'Avg temp: {avg_temp:.1f} C',
        f'Storm days: {len(storm_days)}',
        f'Travel: {travel_date.strftime("%Y-%m-%d")}',
        forecast_en,
    ]
    return '\n'.join(console_lines), png_lines


def _draw_line_chart(pixels, width, height, rows):
    margin_left = 50
    margin_right = 20
    margin_top = 90
    margin_bottom = 40
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    temps = [row[1] for row in rows]
    min_temp = min(temps)
    max_temp = max(temps)
    if min_temp == max_temp:
        min_temp -= 1
        max_temp += 1

    def plot_x(index):
        if len(rows) == 1:
            return margin_left + plot_w // 2
        ratio = index / (len(rows) - 1)
        return margin_left + int(ratio * plot_w)

    def plot_y(temp):
        ratio = (temp - min_temp) / (max_temp - min_temp)
        return margin_top + int((1.0 - ratio) * plot_h)

    for x in range(margin_left, width - margin_right):
        y = margin_top + plot_h
        if 0 <= y < height:
            pixels[y * width + x] = (220, 220, 220)

    for y in range(margin_top, margin_top + plot_h, max(1, plot_h // 5)):
        for x in range(margin_left, width - margin_right):
            pixels[y * width + x] = (235, 235, 235)

    points = []
    for idx, row in enumerate(rows):
        x = plot_x(idx)
        y = plot_y(row[1])
        points.append((x, y))
        if row[2] != 0:
            for bar_x in range(max(margin_left, x - 2), min(width - margin_right, x + 3)):
                for bar_y in range(margin_top, margin_top + plot_h):
                    pixels[bar_y * width + bar_x] = (255, 210, 210)

    for idx in range(1, len(points)):
        x0, y0 = points[idx - 1]
        x1, y1 = points[idx]
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for step in range(steps + 1):
            t = step / steps
            x = int(x0 + (x1 - x0) * t)
            y = int(y0 + (y1 - y0) * t)
            if 0 <= x < width and 0 <= y < height:
                pixels[y * width + x] = (30, 90, 200)
                for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        pixels[ny * width + nx] = (30, 90, 200)


def _draw_text_block(pixels, width, height, lines):
    font = {
        ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'],
        '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],
        '.': ['00000', '00000', '00000', '00000', '00000', '01100', '01100'],
        ':': ['00000', '01100', '01100', '00000', '01100', '01100', '00000'],
        '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
        '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
        '2': ['01110', '10001', '00001', '00110', '01000', '10000', '11111'],
        '3': ['01110', '10001', '00001', '00110', '00001', '10001', '01110'],
        '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
        '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
        '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'],
        '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
        '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],
        '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
        'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
        'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
        'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
        'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
        'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
        'G': ['01110', '10001', '10000', '10011', '10001', '10001', '01110'],
        'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
        'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'],
        'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
        'M': ['10001', '11011', '10101', '10001', '10001', '10001', '10001'],
        'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
        'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
        'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
        'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
        'S': ['01111', '10000', '10000', '01110', '00001', '00001', '11110'],
        'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
        'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
        'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
        'W': ['10001', '10001', '10001', '10101', '10101', '10101', '01010'],
        'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
        'a': ['00000', '00000', '01110', '00001', '01111', '10001', '01111'],
        'e': ['00000', '00000', '01110', '10001', '11111', '10000', '01110'],
        'g': ['00000', '00000', '01111', '10001', '01111', '00001', '01110'],
        'h': ['10000', '10000', '10110', '11001', '10001', '10001', '10001'],
        'i': ['00100', '00000', '01100', '00100', '00100', '00100', '01110'],
        'l': ['00100', '00100', '00100', '00100', '00100', '00100', '00100'],
        'm': ['00000', '00000', '11010', '10101', '10101', '10101', '10101'],
        'n': ['00000', '00000', '10110', '11001', '10001', '10001', '10001'],
        'o': ['00000', '00000', '01110', '10001', '10001', '10001', '01110'],
        'p': ['00000', '00000', '11110', '10001', '11110', '10000', '10000'],
        'r': ['00000', '00000', '10110', '11001', '10000', '10000', '10000'],
        's': ['00000', '00000', '01111', '10000', '01110', '00001', '11110'],
        't': ['01000', '01000', '11110', '01000', '01000', '01001', '00110'],
        'u': ['00000', '00000', '10001', '10001', '10001', '10001', '01110'],
        'v': ['00000', '00000', '10001', '10001', '10001', '01010', '00100'],
        'w': ['00000', '00000', '10001', '10001', '10101', '10101', '01010'],
        'y': ['00000', '00000', '10001', '10001', '01111', '00001', '01110'],
        '(': ['00010', '00100', '01000', '01000', '01000', '00100', '00010'],
        ')': ['01000', '00100', '00010', '00010', '00010', '00100', '01000'],
    }

    def draw_char(ch, start_x, start_y, color):
        glyph = font.get(ch)
        if glyph is None:
            return start_x + 8
        for row_idx, row_bits in enumerate(glyph):
            for col_idx, bit in enumerate(row_bits):
                if bit != '1':
                    continue
                x = start_x + col_idx
                y = start_y + row_idx
                if 0 <= x < width and 0 <= y < height:
                    pixels[y * width + x] = color
        return start_x + 7

    y = 8
    for line in lines[:6]:
        x = 10
        for ch in line:
            if ch == '\n':
                continue
            x = draw_char(ch, x, y, (20, 20, 20))
        y += 12


def _png_pack(tag, data):
    chunk = tag + data
    return (
        struct.pack('!I', len(data))
        + chunk
        + struct.pack('!I', zlib.crc32(chunk) & 0xFFFFFFFF)
    )


# PNG 저장
def save_summary_png(path, rows, summary_text):
    width = 900
    height = 520
    pixels = [(255, 255, 255)] * (width * height)

    _draw_text_block(pixels, width, height, summary_text.splitlines())
    _draw_line_chart(pixels, width, height, rows)

    raw = bytearray()
    for rgb in pixels:
        raw.extend(rgb)

    compressed = zlib.compress(bytes(raw), 9)
    png = bytearray()
    png.extend(b'\x89PNG\r\n\x1a\n')
    png.extend(_png_pack(b'IHDR', struct.pack('!IIBBBBB', width, height, 8, 2, 0, 0, 0)))
    png.extend(_png_pack(b'IDAT', compressed))
    png.extend(_png_pack(b'IEND', b''))

    with open(path, 'wb') as file_obj:
        file_obj.write(png)
    print(f'PNG 저장 완료: {path}')


# 실행
def main():
    csv_path = _resolve_csv_path()
    print(f'=== {os.path.basename(csv_path)} 내용 ===')
    raw_rows = read_and_print_csv(csv_path)
    records = _parse_csv_rows(raw_rows)
    if not records:
        print('적재할 레코드가 없습니다. CSV 형식을 확인하세요.')
        return

    print(f'\n[파싱 완료] {len(records)}건 (mars_date, temp, storm)')

    db_config = resolve_db_config()
    helper = MySQLHelper(db_config)
    try:
        setup_database(helper)
        print('\n=== INSERT 쿼리 실행 ===')
        insert_records(helper, records)

        rows = fetch_weather_rows(helper)
        console_summary, png_lines = build_summary_text(rows)
        print('\n' + console_summary)

        png_path = os.path.join(_script_dir(), PNG_FILENAME)
        save_summary_png(png_path, rows, '\n'.join(png_lines))
    except mysql.connector.Error as err:
        print(f'MySQL 오류: {err}')
        if err.errno == 1045:
            print(
                '로그인 실패입니다. day12/db_config.local.py 에서 '
                'Workbench와 같은 user·password를 넣으세요.\n'
                f"  현재 user: {db_config.get('user')}\n"
                '  (로컬 Workbench는 보통 root가 아니라 dvely 계정입니다.)'
            )
        else:
            print('MySQL 서버 실행 및 db_config.local.py 설정을 확인하세요.')
    finally:
        helper.close()


if __name__ == '__main__':
    main()
