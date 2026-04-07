#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''미션 컴퓨터: DummySensor 연동, 환경 값 JSON 출력, 5초 주기·5분 평균·종료 키.'''

import json
import random
import sys
import threading
import time
from datetime import datetime

ENV_LOG_FILENAME = 'mars_base_environment.log'
INTERVAL_SEC = 5
SAMPLES_PER_FIVE_MIN = 60
STOP_KEY = 'q'


def _script_dir():
    path = __file__
    if '/' in path:
        return path.rsplit('/', 1)[0]
    return '.'


def _join_path(dir_path, filename):
    if not dir_path or dir_path == '.':
        return filename
    if dir_path.endswith('/'):
        return dir_path + filename
    return dir_path + '/' + filename


class DummySensor:
    KEY_INTERNAL_TEMP = 'mars_base_internal_temperature'
    KEY_EXTERNAL_TEMP = 'mars_base_external_temperature'
    KEY_INTERNAL_HUMIDITY = 'mars_base_internal_humidity'
    KEY_EXTERNAL_ILLUMINANCE = 'mars_base_external_illuminance'
    KEY_INTERNAL_CO2 = 'mars_base_internal_co2'
    KEY_INTERNAL_OXYGEN = 'mars_base_internal_oxygen'

    def __init__(self):
        self.env_values = {
            self.KEY_INTERNAL_TEMP: None,
            self.KEY_EXTERNAL_TEMP: None,
            self.KEY_INTERNAL_HUMIDITY: None,
            self.KEY_EXTERNAL_ILLUMINANCE: None,
            self.KEY_INTERNAL_CO2: None,
            self.KEY_INTERNAL_OXYGEN: None,
        }

    def set_env(self):
        self.env_values[self.KEY_INTERNAL_TEMP] = random.uniform(18.0, 30.0)
        self.env_values[self.KEY_EXTERNAL_TEMP] = random.uniform(0.0, 21.0)
        self.env_values[self.KEY_INTERNAL_HUMIDITY] = random.uniform(50.0, 60.0)
        self.env_values[self.KEY_EXTERNAL_ILLUMINANCE] = random.uniform(500.0, 715.0)
        self.env_values[self.KEY_INTERNAL_CO2] = random.uniform(0.02, 0.1)
        self.env_values[self.KEY_INTERNAL_OXYGEN] = random.uniform(4.0, 7.0)

    def get_env(self):
        log_path = _join_path(_script_dir(), ENV_LOG_FILENAME)
        ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = (
            f'{ts}, '
            f'화성 기지 내부 온도: {self.env_values[self.KEY_INTERNAL_TEMP]:.4f} °C, '
            f'화성 기지 외부 온도: {self.env_values[self.KEY_EXTERNAL_TEMP]:.4f} °C, '
            f'화성 기지 내부 습도: {self.env_values[self.KEY_INTERNAL_HUMIDITY]:.4f} %, '
            f'화성 기지 외부 광량: {self.env_values[self.KEY_EXTERNAL_ILLUMINANCE]:.4f} W/m2, '
            f'화성 기지 내부 이산화탄소 농도: {self.env_values[self.KEY_INTERNAL_CO2]:.6f} %, '
            f'화성 기지 내부 산소 농도: {self.env_values[self.KEY_INTERNAL_OXYGEN]:.4f} %\n'
        )
        try:
            with open(log_path, 'a', encoding='utf-8') as log_file:
                log_file.write(line)
        except OSError:
            pass
        return self.env_values


ENV_KEYS = (
    'mars_base_internal_temperature',
    'mars_base_external_temperature',
    'mars_base_internal_humidity',
    'mars_base_external_illuminance',
    'mars_base_internal_co2',
    'mars_base_internal_oxygen',
)


class MissionComputer:
    def __init__(self):
        self.ds = DummySensor()
        self.env_values = {k: None for k in ENV_KEYS}
        self._stop = threading.Event()
        self._samples = []
        self._input_thread = None
        self._stopped_by_key = False

    def _watch_stdin(self):
        while not self._stop.is_set():
            try:
                line = sys.stdin.readline()
            except OSError:
                break
            if not line:
                self._stop.set()
                break
            if line.strip() == STOP_KEY:
                self._stopped_by_key = True
                self._stop.set()
                break

    def _start_input_thread(self):
        if self._input_thread is not None:
            return
        self._input_thread = threading.Thread(target=self._watch_stdin, daemon=True)
        self._input_thread.start()

    def _sleep_interval(self):
        for _ in range(INTERVAL_SEC):
            if self._stop.is_set():
                return False
            time.sleep(1)
        return True

    def _append_sample(self):
        self._samples.append({k: self.env_values[k] for k in ENV_KEYS})

    def _maybe_print_five_minute_average(self):
        if len(self._samples) < SAMPLES_PER_FIVE_MIN:
            return
        n = len(self._samples)
        avg = {k: sum(s[k] for s in self._samples) / n for k in ENV_KEYS}
        print('=== 5분 평균 (JSON) ===')
        print(json.dumps(avg, indent=2, ensure_ascii=False))
        self._samples.clear()

    def get_sensor_data(self):
        self._start_input_thread()
        print(
            f'환경 데이터를 {INTERVAL_SEC}초마다 JSON으로 출력한다. '
            f"종료하려면 '{STOP_KEY}' 입력 후 Enter."
        )

        while not self._stop.is_set():
            self.ds.set_env()
            reading = self.ds.get_env()
            for k in ENV_KEYS:
                self.env_values[k] = reading[k]

            print(json.dumps(self.env_values, indent=2, ensure_ascii=False))

            self._append_sample()
            self._maybe_print_five_minute_average()

            if not self._sleep_interval():
                break

        if self._stopped_by_key:
            print('Sytem stoped....')


if __name__ == '__main__':
    RunComputer = MissionComputer()
    RunComputer.get_sensor_data()
