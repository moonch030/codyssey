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

---

## 예상 질문 & 답변

### 과제·설계

**Q. 왜 CSV를 bulk insert 안 하고 INSERT를 1000번 반복하나요?**  
→ 과제 요구가 「CSV를 **INSERT 쿼리로 변환**해서 **반복 실행**」이기 때문입니다. `insert_records()`의 `for` 루프가 핵심입니다.

**Q. `weather_id`는 CSV에 있는데 왜 INSERT에 안 넣나요?**  
→ DB에서 `weather_id`는 **PRIMARY KEY + AUTO_INCREMENT**라 MySQL이 1, 2, 3… 자동 부여합니다.

**Q. `temp`가 21.4인데 왜 INT로 넣나요?**  
→ 과제 테이블 스키마가 **`temp INT`**로 정해져 있어서 `int(round(float(...)))`로 반올림 후 저장합니다.

**Q. `stom`은 뭐예요?**  
→ CSV 헤더 **오타**입니다. 코드에서 `storm`으로 매핑해 처리했습니다.

**Q. `storm` 값 0, 56, 99는 무슨 의미인가요?**  
→ **`0` = 폭풍 없음**, **`0이 아님` = 폭풍 있음(또는 강도)**. 이동일 판단은 `storm == 0` 여부로 봅니다.

**Q. 이동 예정일은 어떻게 정했나요?**  
→ DB **마지막 날짜 + 1일**입니다. (예: `2052-09-26` → 이동일 `2052-09-27`)

**Q. 「내일 날씨는 맑음」은 어떻게 판단했나요?**  
→ 이동 예정일에 `storm == 0`이면 **폭풍 없음(이동 가능)**, `0`이 아니면 **폭풍 주의**입니다.

---

### MySQL·DB

**Q. `MySQLHelper` 클래스는 왜 만들었나요?**  
→ **보너스 과제**입니다. `connect`, `execute`, `fetchall`, `commit`, `close`를 묶어 DB 접근을 단순화했습니다.

**Q. `commit()`은 왜 필요한가요?**  
→ INSERT 후 **트랜잭션을 확정**해야 DB에 실제 저장됩니다.

**Q. 재실행하면 데이터가 중복되지 않나요?**  
→ `setup_database()`에서 **`DELETE FROM mars_weather`**로 비운 뒤 다시 INSERT합니다.

**Q. 왜 `mysql.connector`를 썼나요?**  
→ 과제에서 **MySQL 다루는 부분은 외부 라이브러리 사용 가능**하기 때문입니다.

**Q. `DATETIME`인데 날짜만 `2050-01-01`이어도 되나요?**  
→ MySQL이 `YYYY-MM-DD`도 받아들이며, 시간 없으면 `00:00:00`으로 처리됩니다.

---

### Python·코드

**Q. 왜 `csv` 모듈을 썼나요?**  
→ Python **표준 라이브러리**이고, 과제 제약(일반 처리는 stdlib)에 맞습니다.

**Q. `utf-8-sig`는 왜 썼나요?**  
→ Excel CSV의 **BOM** 때문에 첫 컬럼명이 깨지는 걸 방지합니다.

**Q. 딕셔너리로 변환한다는 게 무슨 뜻인가요?**  
→ CSV 한 줄을 `{'mars_date': '...', 'temp': 21, 'storm': 56}` 형태로 바꾼 것입니다. INSERT 만들기 편하게 **키-값 구조**로 정리한 것입니다.

**Q. SQL Injection 위험은 없나요?**  
→ `mars_date`의 `'`는 `''`로 이스케이프했습니다. 더 안전하게는 **prepared statement(바인딩)**를 씁니다. 과제는 INSERT **문자열 변환**을 요구해서 이 방식을 썼습니다.

**Q. 1000번 execute가 느리지 않나요?**  
→ 실무에선 `executemany()`가 더 빠릅니다. 다만 과제는 **한 줄씩 INSERT 변환·실행**이 목적입니다.

---

### PNG·시각화

**Q. 왜 matplotlib 안 썼나요?**  
→ CSV·일반 Python 처리는 **표준 라이브러리만** 써야 해서, PNG는 **`struct` + `zlib`**로 직접 생성했습니다.

**Q. PNG에 뭐가 들어가 있나요?**  
→ 요약 텍스트(기록 수, 평균 온도, 폭풍 일수, 이동일) + **최근 90일 온도 꺾은선** + **폭풍일 빨간 표시**입니다.

---

### 개념·확장

**Q. CSV와 DB 중 어느 게 더 좋나요?**  
→ CSV는 저장·백업에 좋고, DB는 **검색·정렬·집계**에 유리합니다. 이번엔 「이동일에 폭풍 있는지」 **조건 검색**이 필요해서 DB에 넣었습니다.

**Q. PRIMARY KEY와 AUTO_INCREMENT 차이는?**  
→ **PRIMARY KEY**는 행을 유일하게 구분하는 키, **AUTO_INCREMENT**는 그 값을 DB가 자동 증가시킵니다.

**Q. `SELECT ... ORDER BY mars_date`는 왜 하나요?**  
→ 날짜 순 정렬해야 **마지막 날짜·이동 예정일**을 정확히 구할 수 있어서입니다.

---

### 발표용 초단답 (외워두기)

| 질문 | 10초 답 |
|------|---------|
| 과제 핵심? | CSV → INSERT 변환 → 반복 execute |
| AUTO_INCREMENT? | weather_id는 DB가 자동 생성 |
| temp 소수? | 스키마가 INT라 round 후 저장 |
| stom? | storm 오타, 코드에서 보정 |
| MySQLHelper? | 보너스, DB 연결·쿼리 캡슐화 |
| matplotlib? | stdlib만 → PNG 직접 생성 |
| 맑음 판단? | 이동일 storm == 0 |
| 성공 확인? | `SELECT COUNT(*)` → 1000 |

> **TIP:** 코드 질문이 나오면 **`insert_records`의 for 루프** 또는 **`row_to_insert_sql`**을 화면에 띄우고, 「과제 요구가 INSERT **변환**과 **반복 실행**이라 이 부분이 핵심입니다」라고 답하면 됩니다.
