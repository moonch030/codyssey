#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# 이 파일 전체 모듈 설명(독스트링): 미션 컴퓨터용 더미 센서 역할을 요약한다.
'''미션 컴퓨터용 더미 센서: 환경 값 랜덤 생성·조회 및 환경 로그 기록.'''

# 운영체제 경로·파일 조작을 위해 표준 라이브러리 os를 가져온다.
import os
# 난수 생성을 위해 과제에서 허용한 표준 라이브러리 random을 가져온다.
import random
# 로그에 넣을 현재 날짜·시간을 위해 datetime 클래스만 가져온다.
from datetime import datetime


# 환경 로그 파일의 기본 이름(스크립트와 같은 폴더에 생성·추가됨)
ENV_LOG_FILENAME = 'mars_base_environment.log'


def _script_dir():
    '''현재 파이썬 파일이 있는 디렉터리의 절대 경로를 반환한다.'''
    # __file__의 절대 경로에서 디렉터리 부분만 잘라 반환한다.
    return os.path.dirname(os.path.abspath(__file__))


class DummySensor:
    '''
    테스트용 더미 센서.

    실제 센서 없이 미션 컴퓨터 환경 표시·로깅 흐름을 검증하기 위해
    지정된 범위에서 난수로 환경 값을 채운다.
    '''

    # env_values 사전에서 쓰는 키 문자열: 화성 기지 내부 온도
    KEY_INTERNAL_TEMP = 'mars_base_internal_temperature'
    # 화성 기지 외부 온도 키
    KEY_EXTERNAL_TEMP = 'mars_base_external_temperature'
    # 화성 기지 내부 습도 키
    KEY_INTERNAL_HUMIDITY = 'mars_base_internal_humidity'
    # 화성 기지 외부 광량 키
    KEY_EXTERNAL_ILLUMINANCE = 'mars_base_external_illuminance'
    # 화성 기지 내부 이산화탄소 농도 키
    KEY_INTERNAL_CO2 = 'mars_base_internal_co2'
    # 화성 기지 내부 산소 농도 키
    KEY_INTERNAL_OXYGEN = 'mars_base_internal_oxygen'

    def __init__(self):
        # 인스턴스 생성 시 env_values를 만들고, 과제 요구 키 6개를 None으로 둔다.
        self.env_values = {
            # 내부 온도 값 자리(아직 측정 전이면 None)
            self.KEY_INTERNAL_TEMP: None,
            # 외부 온도 값 자리
            self.KEY_EXTERNAL_TEMP: None,
            # 내부 습도 값 자리
            self.KEY_INTERNAL_HUMIDITY: None,
            # 외부 광량 값 자리
            self.KEY_EXTERNAL_ILLUMINANCE: None,
            # 내부 CO2 농도 값 자리
            self.KEY_INTERNAL_CO2: None,
            # 내부 산소 농도 값 자리
            self.KEY_INTERNAL_OXYGEN: None,
        }

    def set_env(self):
        '''
        random 모듈로 각 항목의 허용 범위 안에서 값을 만들어 env_values에 넣는다.

        범위:
            내부 온도 18~30 °C, 외부 온도 0~21 °C, 내부 습도 50~60 %,
            외부 광량 500~715 W/m², 내부 CO₂ 0.02~0.1 %, 내부 O₂ 4~7 %
        '''
        # 내부 온도: 18도 이상 30도 이하 균등 난수
        self.env_values[self.KEY_INTERNAL_TEMP] = random.uniform(18.0, 30.0)
        # 외부 온도: 0도 이상 21도 이하 균등 난수
        self.env_values[self.KEY_EXTERNAL_TEMP] = random.uniform(0.0, 21.0)
        # 내부 습도: 50% 이상 60% 이하 균등 난수
        self.env_values[self.KEY_INTERNAL_HUMIDITY] = random.uniform(50.0, 60.0)
        # 외부 광량: 500~715 W/m² 균등 난수
        self.env_values[self.KEY_EXTERNAL_ILLUMINANCE] = random.uniform(500.0, 715.0)
        # 내부 CO2: 0.02~0.1% 균등 난수
        self.env_values[self.KEY_INTERNAL_CO2] = random.uniform(0.02, 0.1)
        # 내부 산소: 4~7% 균등 난수
        self.env_values[self.KEY_INTERNAL_OXYGEN] = random.uniform(4.0, 7.0)

    def get_env(self):
        '''
        현재 env_values 사전을 반환한다.

        보너스: 반환 전에 날짜·시간과 각 환경 항목을 한 줄로 로그 파일에 추가한다.
        '''
        # 스크립트 폴더와 로그 파일 이름을 합쳐 전체 경로 문자열을 만든다.
        log_path = os.path.join(_script_dir(), ENV_LOG_FILENAME)
        # 현재 시각을 '년-월-일 시:분:초' 형태 문자열로 만든다.
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # 로그 한 줄: 타임스탬프 뒤에 사람이 읽기 쉬운 한글 라벨과 수치를 이어 붙인다.
        line = (
            # 로그 맨 앞: 날짜와 시간
            f'{ts}, '
            # 내부 온도(소수 넷째 자리까지)
            f'화성 기지 내부 온도: {self.env_values[self.KEY_INTERNAL_TEMP]:.4f} °C, '
            # 외부 온도
            f'화성 기지 외부 온도: {self.env_values[self.KEY_EXTERNAL_TEMP]:.4f} °C, '
            # 내부 습도
            f'화성 기지 내부 습도: {self.env_values[self.KEY_INTERNAL_HUMIDITY]:.4f} %, '
            # 외부 광량
            f'화성 기지 외부 광량: {self.env_values[self.KEY_EXTERNAL_ILLUMINANCE]:.4f} W/m2, '
            # 내부 CO2(CO2는 소수 여섯째 자리까지)
            f'화성 기지 내부 이산화탄소 농도: {self.env_values[self.KEY_INTERNAL_CO2]:.6f} %, '
            # 내부 산소, 줄 끝에 개행 문자로 한 줄 기록을 마친다.
            f'화성 기지 내부 산소 농도: {self.env_values[self.KEY_INTERNAL_OXYGEN]:.4f} %\n'
        )
        # 로그 파일을 추가 모드('a')로 열고 UTF-8로 기록한다.
        with open(log_path, 'a', encoding='utf-8') as log_file:
            # 방금 만든 한 줄 문자열을 파일 끝에 쓴다.
            log_file.write(line)

        # 호출한 쪽에서 쓸 수 있도록 환경 값 사전 전체를 돌려준다.
        return self.env_values


# 이 파일이 직접 실행될 때만 아래 블록이 돌아가고, import될 때는 실행되지 않는다.
if __name__ == '__main__':
    # DummySensor 클래스로 인스턴스 ds를 하나 만든다.
    ds = DummySensor()
    # 더미 데이터로 env_values를 채운다.
    ds.set_env()
    # 로그를 남기고, 현재 사전 내용을 snapshot 변수에 받는다.
    snapshot = ds.get_env()

    # 콘솔에 섹션 제목을 출력한다.
    print('=== DummySensor 환경 값 (get_env 반환 사전) ===')
    # 사전의 키와 값을 한 쌍씩 꺼내어 보기 좋게 출력한다.
    for key, value in snapshot.items():
        # 키 이름과 해당 측정값(실수)을 한 줄에 출력한다.
        print(f'  {key}: {value}')

    # 로그가 저장된 파일의 전체 경로를 사용자에게 알려 준다.
    print(f'\n로그 파일 위치: {os.path.join(_script_dir(), ENV_LOG_FILENAME)}')
