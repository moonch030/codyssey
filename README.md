# codyssey

화성 기지 Codyssey 미션 코드 모음

## 폴더 구조

| 폴더 | 내용 |
|------|------|
| **day01/** | 1일차 — 미션 컴퓨터 로그 분석 (`main.py`, `mission_computer_main.log`, `error_only.log`, `log_analysis.md`) |
| **day02/** | 2일차 — 화성 기지 인벤토리·인화성 분류 (`mars_base_inventory.py`, `Mars_Base_Inventory_List.csv`, 생성물 `Mars_Base_Inventory_danger.csv`, `Mars_Base_Inventory_List.bin`) |
| **day03/** | 3일차 — 더미 센서 (`mars_mission_computer.py`, `mars_base_environment.log`) |
| **day04/** | 4일차 — 미션 컴퓨터·센서 주기 출력·5분 평균 (`mars_mission_computer.py`) |

## 실행 방법

```bash
# 1일차
cd day01 && python3 main.py

# 2일차
cd day02 && python3 mars_base_inventory.py

# 3일차
cd day03 && python3 mars_mission_computer.py

# 4일차 (종료: 터미널에 q 입력 후 Enter)
cd day04 && python3 mars_mission_computer.py
```

루트에서 실행할 때는 위처럼 해당 일차 폴더로 이동한 뒤 실행
