# Codyssey 문제5 「내일 날씨는 맑음」

---

스토리는 화성 이동 경로는 정해졌는데, **이동 날짜에 모래 폭풍이 겹치면 위험**합니다. 그래서 미션 컴퓨터에 백업된 **`mars_weathers_data.csv`** 를 MySQL에 넣고, **이동해도 되는지** 확인한 뒤 **`mars_weather_summary.png`** 로 결과를 남깁니다.

쓴 파일은 **`mars_weathers_data.csv`**(과제 데이터), **`mars_weather_summary.py`**(메인), **`create_mars_weather.sql`**(테이블 DDL), **`db_config.local.py`**(MySQL 비밀번호) 네 가지입니다.

**코드가 어떻게 돌아가는지** 순서대로 설명하겠습니다.

---

## 코드 설명 (`mars_weather_summary.py`)

### 1. `main` — 전체 흐름

실행하면 `main` 

**CSV 읽기 → 파싱 → DB 연결·테이블 준비 → INSERT 반복 → SELECT·요약 → PNG 저장**

순서로 호출합니다.

---

### 2. `read_and_print_csv` — CSV 읽고 출력

`csv.reader`로 파일을 열고 **한 줄씩 `print`** 합니다.

```python
with open(path, 'r', encoding='utf-8-sig', newline='') as file_obj:
    reader = csv.reader(file_obj)
```

`utf-8-sig`는 Excel에서 저장한 CSV의 BOM을 처리하기 위함입니다.  
파일이 없으면 `FileNotFoundError`를 잡아서 오류 메시지를 냅니다.

---

### 3. `_parse_csv_rows` — DB에 넣을 형태로 변환

여기가 데이터 전처리입니다.

<!-- **① 헤더 오타**  
CSV 헤더가 `storm`이 아니라 **`stom`** 입니다. 코드에서 `stom`을 `storm`으로 매핑합니다. -->

**② 온도 소수**  
`temp`가 `21.4`처럼 들어오는데, DB 컬럼은 **INT**입니다.

```python
def _to_int(value):
    return int(round(float(value.strip())))
```

`round` 후 `int`로 바꿉니다.

**③ weather_id는 INSERT 안 함**  
CSV에 `weather_id`가 있어도, DB는 **AUTO_INCREMENT**라서 INSERT할 때는 **`mars_date`, `temp`, `storm`만** 딕셔너리로 1000건이 나옵니다.

---

### 4. `resolve_db_config` + `MySQLHelper` — DB 연결

`mysql.connector`로 MySQL에 붙습니다.

**`MySQLHelper`**(보너스)는 연결·쿼리를 묶은 클래스입니다.

| 메서드 | 하는 일 |
|--------|---------|
| `connect()` | `mysql.connector.connect` |
| `execute(query)` | SQL 실행 |
| `fetchall()` | SELECT 결과 |
| `commit()` | 저장 확정 |
| `close()` | 연결 종료 |

비밀번호는 **`db_config.local.py`** 에 두고, Workbench와 같은 계정을 씁니다.

---

### 5. `setup_database` — DB·테이블 준비

1. `codyssey` 데이터베이스가 없으면 생성  
2. **`create_mars_weather.sql`** 을 읽어 `mars_weather` 테이블 생성  

```sql
weather_id INT AUTO_INCREMENT PRIMARY KEY
mars_date  DATETIME NOT NULL
temp       INT
storm      INT
```

3. 재실행을 위해 `DELETE FROM mars_weather`로 기존 데이터 비움

---

### 6. `row_to_insert_sql` + `insert_records` — 과제 핵심

**CSV 한 줄 → INSERT 문자열 → `execute` 반복** 입니다.

```python
def row_to_insert_sql(record):
    return (
        'INSERT INTO mars_weather (mars_date, temp, storm) '
        f"VALUES ('{mars_date}', {temp}, {storm});"
    )

def insert_records(helper, records):
    for record in records:
        sql = row_to_insert_sql(record)
        print(sql)          # 변환된 쿼리 출력
        helper.execute(sql) # 한 건씩 실행
    helper.commit()
```

**[데모]** INSERT 문이 터미널에 찍히는 화면, 또는 이 `for` 루프 부분을 보여 주세요.

과제 요구인 「INSERT로 **변환**해서 **반복 실행**」이 바로 이 부분입니다.

---

### 7. `build_summary_text` — 스토리와 연결

DB에서 `SELECT ... ORDER BY mars_date`로 다시 읽습니다.

- **마지막 날짜 + 1일** = 이동 예정일  
- 그날 `storm != 0` → 「이동일 모래 폭풍 주의」  
- `storm == 0` → 「내일 날씨는 맑음」에 해당하는 「폭풍 없음」

평균 온도, 폭풍 일수도 함께 출력합니다.

---

### 8. `save_summary_png` — PNG (표준 라이브러리만)

**`struct` + `zlib`** 로 PNG를 직접 만듭니다.  
위쪽 요약 텍스트, 아래쪽 온도 꺾은선, 폭풍일은 빨간 띠로 표시합니다.  
결과 파일: **`mars_weather_summary.png`**

**[데모]** PNG 파일 열기

---

## 실행·마무리 (30초)

```bash
cd day12
python mars_weather_summary.py
```

Workbench에서 `SELECT COUNT(*) FROM mars_weather` → **1000**이면 성공입니다.

**정리:** CSV → INSERT 반복 → DB 조회 → PNG. 핵심은 **`insert_records`의 for 루프**와 **`MySQLHelper`** 입니다.

---

## 예상 질문 (한 줄 답)

| 질문 | 답 |
|------|-----|
| weather_id INSERT 안 하는 이유? | AUTO_INCREMENT PK |
| stom? | storm 오타, 코드에서 보정 |
| matplotlib? | 과제상 stdlib만 → PNG 직접 생성 |
