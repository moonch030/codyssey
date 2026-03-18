# 사고 원인 분석 보고서 (log_analysis.md)

## 1. 분석 개요
- **대상 파일:** mission_computer_main.log
- **분석 도구:** Python 3.x (PEP 8 준수 커스텀 스크립트)

## 2. 사고 원인 추정
로그 데이터 분석 결과, 폭발 직전 수전해 장치(Water Electrolysis System)에서 임계 압력을 초과하는 `CRITICAL` 메시지가 반복적으로 발생함. 

## 3. 결론
소프트웨어 제어 로직 오류로 인한 가압 조절 실패가 기지 폭발의 직접적인 원인으로 판단됨.