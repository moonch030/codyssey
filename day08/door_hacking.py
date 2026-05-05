#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# emergency_storage_key.zip 비밀번호(숫자+소문자 6자리) 탐색 스크립트

import itertools
import os
import string
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime


# 비밀번호 후보 문자 집합: 숫자 + 소문자 알파벳
CHARSET = string.digits + string.ascii_lowercase
# 비밀번호 길이(문제 조건)
PASSWORD_LENGTH = 6
# 진행 상황 로그 출력 간격(순차 모드)
PROGRESS_INTERVAL = 100000
# 성공 시 저장할 파일 이름
PASSWORD_OUTPUT = 'password.txt'


def _safe_extract_test(zip_path, password):
    '''주어진 비밀번호가 ZIP 해제에 성공하는지 검사한다.'''
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            names = zf.namelist()
            if not names:
                return False
            with zf.open(names[0], pwd=password.encode('utf-8')) as file:
                file.read(1)
        return True
    except (RuntimeError, zipfile.BadZipFile, OSError, KeyError):
        return False


def _save_password(output_path, password):
    '''찾은 비밀번호를 파일로 저장한다.'''
    try:
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(password)
        return True
    except OSError as exc:
        print(f'[오류] 비밀번호 저장 실패: {exc}')
        return False


def _sequential_unlock(zip_path, progress_interval=PROGRESS_INTERVAL):
    '''순차 브루트포스 방식으로 비밀번호를 찾는다.'''
    start = time.perf_counter()
    started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    attempts = 0

    print(f'[시작] {started_at}')
    print('[모드] 순차 브루트포스')

    for chars in itertools.product(CHARSET, repeat=PASSWORD_LENGTH):
        candidate = ''.join(chars)
        attempts += 1

        if _safe_extract_test(zip_path, candidate):
            elapsed = time.perf_counter() - start
            print(f'[성공] 비밀번호 발견: {candidate}')
            print(f'[반복] 총 시도 횟수: {attempts:,}')
            print(f'[경과] {elapsed:.2f}초')
            return candidate, attempts, elapsed

        if attempts % progress_interval == 0:
            elapsed = time.perf_counter() - start
            print(f'[진행] 시도: {attempts:,}회 / 경과: {elapsed:.2f}초')

    elapsed = time.perf_counter() - start
    print('[실패] 가능한 모든 조합을 시도했지만 찾지 못했습니다.')
    print(f'[반복] 총 시도 횟수: {attempts:,}')
    print(f'[경과] {elapsed:.2f}초')
    return None, attempts, elapsed


def _worker_try_prefix(zip_path, prefix):
    '''보너스: 접두어 1글자 단위 작업을 병렬 처리한다.'''
    attempts = 0
    for tail in itertools.product(CHARSET, repeat=PASSWORD_LENGTH - 1):
        candidate = prefix + ''.join(tail)
        attempts += 1
        if _safe_extract_test(zip_path, candidate):
            return candidate, attempts
    return None, attempts


def _parallel_unlock(zip_path):
    '''보너스: 멀티프로세스 병렬 브루트포스로 비밀번호를 찾는다.'''
    start = time.perf_counter()
    started_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_attempts = 0

    print(f'[시작] {started_at}')
    print('[모드] 병렬 브루트포스(보너스)')

    with ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(_worker_try_prefix, zip_path, prefix): prefix
            for prefix in CHARSET
        }

        for index, future in enumerate(as_completed(futures), start=1):
            password, attempts = future.result()
            total_attempts += attempts
            elapsed = time.perf_counter() - start
            print(
                f'[진행] 완료 작업: {index}/{len(CHARSET)} '
                f'/ 누적 시도: {total_attempts:,}회 '
                f'/ 경과: {elapsed:.2f}초'
            )

            if password is not None:
                for pending in futures:
                    pending.cancel()
                print(f'[성공] 비밀번호 발견: {password}')
                print(f'[반복] 누적 시도 횟수(완료 작업 기준): {total_attempts:,}')
                print(f'[경과] {elapsed:.2f}초')
                return password, total_attempts, elapsed

    elapsed = time.perf_counter() - start
    print('[실패] 가능한 모든 조합을 시도했지만 찾지 못했습니다.')
    print(f'[반복] 누적 시도 횟수: {total_attempts:,}')
    print(f'[경과] {elapsed:.2f}초')
    return None, total_attempts, elapsed


def unlock_zip(zip_path='emergency_storage_key.zip', output_path=PASSWORD_OUTPUT, use_parallel=True):
    '''ZIP 비밀번호를 찾아 출력하고, 성공하면 password.txt로 저장한다.'''
    if not os.path.exists(zip_path):
        print(f'[오류] ZIP 파일을 찾을 수 없습니다: {zip_path}')
        return None

    if not zipfile.is_zipfile(zip_path):
        print(f'[오류] 올바른 ZIP 파일 형식이 아닙니다: {zip_path}')
        return None

    if use_parallel:
        password, attempts, elapsed = _parallel_unlock(zip_path)
    else:
        password, attempts, elapsed = _sequential_unlock(zip_path)

    if password is None:
        return None

    if _save_password(output_path, password):
        print(f'[저장] 비밀번호를 {output_path} 파일에 저장했습니다.')
        print(f'[요약] 비밀번호: {password}, 반복: {attempts:,}, 경과: {elapsed:.2f}초')
        return password

    return None


if __name__ == '__main__':
    # 현재 파일이 있는 폴더 기준으로 ZIP/출력 파일 경로를 고정한다.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_file_path = os.path.join(base_dir, 'emergency_storage_key.zip')
    output_file_path = os.path.join(base_dir, PASSWORD_OUTPUT)

    # 보너스 과제 반영: 기본 실행은 병렬 모드
    unlock_zip(zip_path=zip_file_path, output_path=output_file_path, use_parallel=True)
