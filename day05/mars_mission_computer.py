#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''미션 컴퓨터: 센서 데이터, 시스템 정보, 실시간 부하를 출력한다.'''

import json
import os
import platform
import random
import subprocess
import time

ENV_KEYS = (
    'mars_base_internal_temperature',
    'mars_base_external_temperature',
    'mars_base_internal_humidity',
    'mars_base_external_illuminance',
    'mars_base_internal_co2',
    'mars_base_internal_oxygen',
)

INFO_KEYS = (
    'os_name',
    'os_version',
    'cpu_type',
    'cpu_cores',
    'memory_total_mb',
)

LOAD_KEYS = (
    'cpu_realtime_percent',
    'memory_realtime_percent',
)

SETTING_FILE = 'setting.txt'


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
    def __init__(self):
        self.env_values = {k: None for k in ENV_KEYS}

    def set_env(self):
        self.env_values['mars_base_internal_temperature'] = random.uniform(18.0, 30.0)
        self.env_values['mars_base_external_temperature'] = random.uniform(0.0, 21.0)
        self.env_values['mars_base_internal_humidity'] = random.uniform(50.0, 60.0)
        self.env_values['mars_base_external_illuminance'] = random.uniform(500.0, 715.0)
        self.env_values['mars_base_internal_co2'] = random.uniform(0.02, 0.1)
        self.env_values['mars_base_internal_oxygen'] = random.uniform(4.0, 7.0)

    def get_env(self):
        return self.env_values


class MissionComputer:
    def __init__(self):
        self.ds = DummySensor()
        self.env_values = {k: None for k in ENV_KEYS}
        self._setting_path = _join_path(_script_dir(), SETTING_FILE)
        self._settings = self._load_or_create_settings()

    def _default_settings(self):
        keys = INFO_KEYS + LOAD_KEYS
        return {k: True for k in keys}

    def _write_default_setting_file(self):
        lines = ['# true/false 로 출력 항목 설정']
        for key in INFO_KEYS + LOAD_KEYS:
            lines.append(f'{key}=true')
        try:
            with open(self._setting_path, 'w', encoding='utf-8') as file:
                file.write('\n'.join(lines) + '\n')
        except OSError as error:
            print(f'setting.txt 생성 오류: {error}')

    def _load_or_create_settings(self):
        default_settings = self._default_settings()

        if not os.path.exists(self._setting_path):
            self._write_default_setting_file()
            return default_settings

        try:
            with open(self._setting_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except OSError as error:
            print(f'setting.txt 읽기 오류: {error}')
            return default_settings

        parsed = default_settings.copy()
        for raw_line in lines:
            line = raw_line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().lower()
            if key in parsed:
                parsed[key] = value == 'true'
        return parsed

    def _filter_by_settings(self, data):
        return {
            key: value
            for key, value in data.items()
            if self._settings.get(key, True)
        }

    def get_sensor_data(self):
        self.ds.set_env()
        reading = self.ds.get_env()
        for key in ENV_KEYS:
            self.env_values[key] = reading[key]
        print('=== 센서 데이터(JSON) ===')
        print(json.dumps(self.env_values, indent=2, ensure_ascii=False))

    def _get_total_memory_bytes(self):
        try:
            if hasattr(os, 'sysconf'):
                pages = os.sysconf('SC_PHYS_PAGES')
                page_size = os.sysconf('SC_PAGE_SIZE')
                if isinstance(pages, int) and isinstance(page_size, int):
                    return pages * page_size
        except (OSError, ValueError):
            pass

        try:
            output = subprocess.check_output(
                ['sysctl', '-n', 'hw.memsize'],
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            return int(output)
        except (OSError, ValueError, subprocess.CalledProcessError):
            return None

    def get_mission_computer_info(self):
        try:
            total_memory = self._get_total_memory_bytes()
            memory_mb = None
            if isinstance(total_memory, int) and total_memory > 0:
                memory_mb = round(total_memory / (1024 * 1024), 2)

            info = {
                'os_name': platform.system(),
                'os_version': platform.version(),
                'cpu_type': platform.machine(),
                'cpu_cores': os.cpu_count(),
                'memory_total_mb': memory_mb,
            }
        except OSError as error:
            info = {'error': f'시스템 정보 수집 오류: {error}'}

        filtered_info = self._filter_by_settings(info)
        print('=== 미션 컴퓨터 시스템 정보(JSON) ===')
        print(json.dumps(filtered_info, indent=2, ensure_ascii=False))
        return filtered_info

    def _cpu_realtime_percent(self):
        try:
            load_1m = os.getloadavg()[0]
            cores = os.cpu_count() or 1
            return round((load_1m / cores) * 100.0, 2)
        except OSError:
            pass

        try:
            output = subprocess.check_output(
                ['uptime'],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            if 'load averages:' in output:
                load_text = output.split('load averages:')[1].strip()
                first = load_text.split()[0].strip(',')  # 1분 평균
                load_1m = float(first)
                cores = os.cpu_count() or 1
                return round((load_1m / cores) * 100.0, 2)
        except (OSError, ValueError, IndexError, subprocess.CalledProcessError):
            return None

        return None

    def _memory_realtime_percent(self):
        try:
            output = subprocess.check_output(
                ['vm_stat'],
                text=True,
                stderr=subprocess.DEVNULL,
            )
        except (OSError, subprocess.CalledProcessError):
            return None

        page_size = 4096
        active = 0
        wired = 0
        compressed = 0
        free = 0
        inactive = 0

        for line in output.splitlines():
            text = line.strip().replace('.', '')
            if text.startswith('Mach Virtual Memory Statistics'):
                if 'page size of' in text:
                    try:
                        page_size = int(text.split('page size of')[1].split('bytes')[0].strip())
                    except (ValueError, IndexError):
                        page_size = 4096
                continue
            if ':' not in text:
                continue

            key, value = text.split(':', 1)
            value_text = value.strip().replace('.', '')
            value_text = value_text.replace(',', '')
            if not value_text.isdigit():
                continue
            count = int(value_text)

            if key == 'Pages active':
                active = count
            elif key == 'Pages wired down':
                wired = count
            elif key == 'Pages occupied by compressor':
                compressed = count
            elif key == 'Pages free':
                free = count
            elif key == 'Pages inactive':
                inactive = count

        used = (active + wired + compressed) * page_size
        total = (active + wired + compressed + free + inactive) * page_size
        if total <= 0:
            return None
        return round((used / total) * 100.0, 2)

    def get_mission_computer_load(self):
        try:
            load_info = {
                'cpu_realtime_percent': self._cpu_realtime_percent(),
                'memory_realtime_percent': self._memory_realtime_percent(),
            }
        except OSError as error:
            load_info = {'error': f'실시간 부하 수집 오류: {error}'}

        filtered_load = self._filter_by_settings(load_info)
        print('=== 미션 컴퓨터 실시간 부하(JSON) ===')
        print(json.dumps(filtered_load, indent=2, ensure_ascii=False))
        return filtered_load


if __name__ == '__main__':
    runComputer = MissionComputer()
    runComputer.get_mission_computer_info()
    runComputer.get_mission_computer_load()

    # 문제 7 클래스 연속성 확인용: 센서 데이터도 함께 1회 출력
    time.sleep(0.2)
    runComputer.get_sensor_data()
