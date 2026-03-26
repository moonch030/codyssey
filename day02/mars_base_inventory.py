#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''화성 기지 인벤토리: CSV 읽기, 인화성 정렬, 고위험 추출·저장, 이진 저장/복원.'''

import os
import struct

# 입력/출력 파일 이름 상수
CSV_IN = 'Mars_Base_Inventory_List.csv'
CSV_DANGER = 'Mars_Base_Inventory_danger.csv'
BIN_OUT = 'Mars_Base_Inventory_List.bin'


def _script_dir():
    # 현재 파이썬 파일이 위치한 폴더 절대경로
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
    print(text)
    return text

def text_to_rows(text):
    '''CSV 문자열을 헤더(str)와 데이터 행 list[list[str]]로 변환한다.'''
    
    # 1. 들어온 전체 텍스트를 줄바꿈(\n) 기준으로 자르고, 
    #    각 줄의 앞뒤 공백을 제거(.strip())한 뒤, 내용이 있는 줄만 리스트에 담습니다.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    # 2. 만약 처리할 줄이 하나도 없다면(빈 파일 등), 빈 제목과 빈 리스트를 돌려줍니다.
    if not lines:
        return '', []
    
    # 3. 리스트의 가장 첫 번째 줄(0번 인덱스)을 표의 '제목(Header)'으로 저장합니다.
    header = lines[0]
    
    # 4. 실제 데이터를 담을 빈 바구니(리스트)를 준비합니다.
    data = []
    
    # 5. 첫 줄(제목)을 제외한 두 번째 줄(1번 인덱스)부터 마지막까지 하나씩 꺼내서 반복합니다.
    for line in lines[1:]:
        
        # 6. 각 줄을 콤마(,) 기준으로 자릅니다. 
        #    최대 5개의 덩어리만 만듭니다(0~4번 인덱스). 5개 이후는 마지막 덩어리에 합쳐집니다.
        parts = line.split(',', 4)
        
        # 7. 만약 잘린 데이터 조각이 정확히 5개가 아니라면(데이터가 빠졌다면), 
        #    그 줄은 무시하고 다음 줄로 넘어갑니다(continue).
        if len(parts) != 5:
            continue
        
        # 8. 정상적으로 5개가 잘렸다면, 그 조각들의 리스트(['철', '7.8', ...])를 data 바구니에 넣습니다.
        data.append(parts)
    
    # 9. 최종적으로 완성된 제목(문자열)과 데이터 목록(이중 리스트)을 반환합니다.
    return header, data


def sort_by_flammability_desc(rows):
    '''인화성(마지막 열, float) 내림차순으로 정렬한 새 리스트를 반환한다.'''

    def key_flammability(row):
        # 문자열인 인화성 값을 실수로 변환해 정렬 키로 사용
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
    '''정렬된 데이터를 약속된 이진 형식(Binary Format)으로 파일에 저장한다.'''
    try:
        # 1. 'wb' 모드(Write Binary)로 파일을 엽니다. 텍스트가 아닌 '바이트'를 쓰겠다는 뜻입니다.
        with open(path, 'wb') as f:
            
            # 2. 제목(Header) 문자열을 컴퓨터가 이해하는 바이트 덩어리로 변환합니다.
            hb = header.encode('utf-8')
            
            # 3. [헤더 길이 저장]: 헤더가 몇 바이트인지 '4바이트 정수'로 기록합니다.
            # '>I'는 빅엔디안(Big-Endian) 방식의 4바이트 정수를 의미합니다.
            f.write(struct.pack('>I', len(hb)))
            
            # 4. [헤더 데이터 저장]: 실제 헤더 바이트를 이어서 씁니다.
            f.write(hb)
            
            # 5. [행 개수 저장]: 데이터가 총 몇 줄인지 4바이트 정수로 기록합니다.
            # 나중에 파일을 읽을 때 "몇 번 반복해서 읽어야 할지" 알려주는 가이드 역할을 합니다.
            f.write(struct.pack('>I', len(sorted_rows)))
            
            # 6. 각 데이터 행을 하나씩 꺼내서 반복 저장합니다.
            for row in sorted_rows:
                # 7. 리스트 형태인 ['철', '7.8', ...]를 '철,7.8,...' 형태의 문자열로 합칩니다.
                line = ','.join(row)
                
                # 8. 문자열을 바이트로 변환합니다.
                bb = line.encode('utf-8')
                
                # 9. [행 길이 + 행 데이터]: 각 줄마다 길이를 먼저 쓰고 데이터를 씁니다.
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

        # 헤더 길이 읽기 -> 헤더 바이트 읽기
        (hlen,) = struct.unpack_from('>I', raw, off)
        off += 4
        header = raw[off:off + hlen].decode('utf-8')
        off += hlen

        # 행 개수 읽기
        (nrows,) = struct.unpack_from('>I', raw, off)
        off += 4

        lines_out = []
        for _ in range(nrows):
            # 각 행의 길이 읽기
            if off + 4 > len(raw):
                raise ValueError('행 길이 필드가 잘렸습니다.')
            (blen,) = struct.unpack_from('>I', raw, off)
            off += 4
            # 길이만큼 실제 행 데이터 읽기
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
    # 1) 스크립트 기준 경로를 사용해, 실행 위치와 무관하게 파일을 찾는다.
    base = _script_dir()
    path_in = os.path.join(base, CSV_IN)
    path_danger = os.path.join(base, CSV_DANGER)
    path_bin = os.path.join(base, BIN_OUT)

    # 2) 입력 CSV를 읽고 원문을 그대로 출력한다.
    text = read_and_print_csv(path_in)
    if text is None:
        return

    # 3) CSV 문자열을 Python 리스트 구조(헤더 + 데이터 행)로 변환한다.
    header, rows = text_to_rows(text)
    print('\n=== Python list 로 변환된 데이터 행 수 ===')
    print(len(rows))
    print('(각 행은 5개 필드의 list[str])')

    # 4) 인화성 지수(5번째 열)를 기준으로 내림차순 정렬한다.
    sorted_rows = sort_by_flammability_desc(rows)
    print('\n=== 인화성 높은 순 정렬 목록 ===')
    for r in sorted_rows:
        print(','.join(r))

    # 5) 임계값(0.7) 이상만 추려서 위험 목록을 만든다.
    danger = filter_high_flammability(sorted_rows, 0.7)
    print('\n=== 인화성 지수 0.7 이상 ===')
    for r in danger:
        print(','.join(r))

    # 6) 위험 목록을 CSV로 저장한다.
    if write_danger_csv(path_danger, header, danger):
        print(f'\n[저장 완료] {path_danger}')

    # 7) 정렬 결과 전체를 이진 파일로 저장한다.
    if write_sorted_binary(path_bin, header, sorted_rows):
        print(f'[저장 완료] {path_bin}')

    # 8) 저장한 이진 파일을 다시 읽어 복원 출력한다.
    read_binary_and_print(path_bin)
    # 9) 텍스트/이진 파일 방식의 차이와 장단점을 출력한다.
    print_text_vs_binary_notes()


if __name__ == '__main__':
    main()
