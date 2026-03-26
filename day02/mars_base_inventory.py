#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''화성 기지 인벤토리: CSV 읽기, 인화성 정렬, 고위험 추출·저장, 이진 저장/복원.'''

import os
import struct

CSV_IN = 'Mars_Base_Inventory_List.csv'
CSV_DANGER = 'Mars_Base_Inventory_danger.csv'
BIN_OUT = 'Mars_Base_Inventory_List.bin'


def _script_dir():
    return os.path.dirname(os.path.abspath(__file__))


def read_and_print_csv(path):
    '''CSV 전체를 읽어 화면에 출력하고 원문 문자열을 반환한다.'''
    try:
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
    except FileNotFoundError:
        print(f'오류: 파일을 찾을 수 없습니다: {path}')
        return None
    except OSError as e:
        print(f'파일 읽기 오류: {e}')
        return None

    print('=== Mars_Base_Inventory_List.csv (원문) ===')
    print(text, end='' if text.endswith('\n') else '\n')
    return text


def text_to_rows(text):
    '''CSV 문자열을 헤더(str)와 데이터 행 list[list[str]]로 변환한다.'''
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return '', []
    header = lines[0]
    data = []
    for line in lines[1:]:
        parts = line.split(',', 4)
        if len(parts) != 5:
            continue
        data.append(parts)
    return header, data


def sort_by_flammability_desc(rows):
    '''인화성(마지막 열, float) 내림차순으로 정렬한 새 리스트를 반환한다.'''

    def key_flammability(row):
        return float(row[4])

    return sorted(rows, key=key_flammability, reverse=True)


def filter_high_flammability(rows, threshold=0.7):
    '''인화성 지수가 threshold 이상인 행만 반환한다.'''
    return [r for r in rows if float(r[4]) >= threshold]


def write_danger_csv(path, header, rows):
    '''고위험 목록을 CSV로 저장한다.'''
    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(header + '\n')
            for row in rows:
                f.write(','.join(row) + '\n')
    except OSError as e:
        print(f'CSV 저장 오류: {e}')
        return False
    return True


def write_sorted_binary(path, header, sorted_rows):
    '''인화성 순 정렬된 행을 이진 형식으로 저장한다.
    형식: 헤더 UTF-8 길이(4바이트 BE) + 헤더 바이트, 행 개수(4바이트 BE),
    각 행: 줄 UTF-8 길이(4바이트 BE) + 줄 바이트(CSV 한 줄).
    '''
    try:
        with open(path, 'wb') as f:
            hb = header.encode('utf-8')
            f.write(struct.pack('>I', len(hb)))
            f.write(hb)
            f.write(struct.pack('>I', len(sorted_rows)))
            for row in sorted_rows:
                line = ','.join(row)
                bb = line.encode('utf-8')
                f.write(struct.pack('>I', len(bb)))
                f.write(bb)
    except OSError as e:
        print(f'이진 파일 저장 오류: {e}')
        return False
    return True


def read_binary_and_print(path):
    '''이진 파일을 읽어 화면에 출력한다.'''
    try:
        with open(path, 'rb') as f:
            raw = f.read()
    except FileNotFoundError:
        print(f'오류: 이진 파일을 찾을 수 없습니다: {path}')
        return
    except OSError as e:
        print(f'이진 파일 읽기 오류: {e}')
        return

    off = 0
    try:
        if len(raw) < 8:
            raise ValueError('파일이 너무 짧습니다.')

        (hlen,) = struct.unpack_from('>I', raw, off)
        off += 4
        header = raw[off:off + hlen].decode('utf-8')
        off += hlen

        (nrows,) = struct.unpack_from('>I', raw, off)
        off += 4

        lines_out = []
        for _ in range(nrows):
            if off + 4 > len(raw):
                raise ValueError('행 길이 필드가 잘렸습니다.')
            (blen,) = struct.unpack_from('>I', raw, off)
            off += 4
            if off + blen > len(raw):
                raise ValueError('행 데이터가 잘렸습니다.')
            line = raw[off:off + blen].decode('utf-8')
            off += blen
            lines_out.append(line)
    except (struct.error, ValueError, UnicodeDecodeError) as e:
        print(f'이진 파일 형식 오류: {e}')
        return

    print('\n=== Mars_Base_Inventory_List.bin (복원 출력) ===')
    print(header)
    for csv_line in lines_out:
        print(csv_line)


def print_text_vs_binary_notes():
    '''텍스트(CSV)와 이진 파일의 차이·장단점 요약.'''
    notes = '''
=== 텍스트 파일(CSV) vs 이진 파일 ===
- 차이: CSV는 사람이 읽을 수 있는 문자(UTF-8 등)로 행을 저장하고,
  이진은 길이 필드·바이트 열로 구조화해 저장한다(이 스크립트는 길이 접두 이진 형식).
- 텍스트 장점: 에디터·스프레드시트로 바로 확인·수정 가능, 디버깅이 쉽다.
- 텍스트 단점: 용량이 상대적으로 크고, 숫자·구조를 문자로 풀어 쓰므로 파싱 비용이 있다.
- 이진 장점: 구조가 고정되면 읽기/쓰기가 빠르고, 숫자·배열을 압축적으로 넣기 좋다.
- 이진 단점: 전용 규격을 알아야 하며, 잘못 쓰면 가독성·호환성이 떨어진다.
'''
    print(notes)


def main():
    base = _script_dir()
    path_in = os.path.join(base, CSV_IN)
    path_danger = os.path.join(base, CSV_DANGER)
    path_bin = os.path.join(base, BIN_OUT)

    text = read_and_print_csv(path_in)
    if text is None:
        return

    header, rows = text_to_rows(text)
    print('\n=== Python list 로 변환된 데이터 행 수 ===')
    print(len(rows))
    print('(각 행은 5개 필드의 list[str])')

    sorted_rows = sort_by_flammability_desc(rows)
    print('\n=== 인화성 높은 순 정렬 목록 ===')
    for r in sorted_rows:
        print(','.join(r))

    danger = filter_high_flammability(sorted_rows, 0.7)
    print('\n=== 인화성 지수 0.7 이상 ===')
    for r in danger:
        print(','.join(r))

    if write_danger_csv(path_danger, header, danger):
        print(f'\n[저장 완료] {path_danger}')

    if write_sorted_binary(path_bin, header, sorted_rows):
        print(f'[저장 완료] {path_bin}')

    read_binary_and_print(path_bin)
    print_text_vs_binary_notes()


if __name__ == '__main__':
    main()
