# mission_log_parser.py
# 미션 컴퓨터 로그(CSV)를 읽어 리스트·사전으로 변환하고 JSON으로 저장하는 스크립트
import os


def read_log_file(file_path):
    '''
    mission_computer_main.log 파일을 읽어 원문 문자열을 반환한다.
    파일이 없거나 읽기 실패 시 None을 반환한다.
    '''
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f'오류: 파일을 찾을 수 없습니다: {file_path}')
        return None
    except OSError as e:
        print(f'파일 읽기 오류: {e}')
        return None


def parse_log_to_list(log_text):
    '''
    CSV 형식 로그 문자열을 파이썬 리스트로 변환한다.
    각 행은 [날짜 및 시간, 로그 내용] 형태의 리스트가 된다.
    '''
    log_list = []
    if not log_text:
        return log_list

    # 줄 단위로 나눈 뒤 빈 줄은 제외
    lines = [line.strip() for line in log_text.splitlines() if line.strip()]

    for line in lines:
        # 콤마를 기준으로 날짜·시간과 로그 내용을 분리 (첫 번째 콤마만 사용)
        parts = line.split(',', 1)
        if len(parts) != 2:
            print(f'경고: 형식이 올바르지 않은 줄을 건너뜁니다: {line}')
            continue
        datetime_str = parts[0].strip()
        message_str = parts[1].strip()
        # CSV 헤더 행(timestamp,event,message)은 건너뜀
        if datetime_str.lower() == 'timestamp':
            continue
        log_list.append([datetime_str, message_str])

    return log_list


def sort_log_list_reverse(log_list):
    '''
    리스트를 날짜·시간(첫 번째 요소) 기준 역순으로 정렬한다.
    ISO 형식 문자열이므로 문자열 비교만으로 시간 순서가 맞다.
    '''
    # sorted()는 원본을 바꾸지 않으므로, 역순 정렬 결과를 새 리스트로 반환
    return sorted(log_list, key=lambda row: row[0], reverse=True)


def list_to_dict(log_list):
    '''
    리스트를 사전으로 변환한다.
    키: 날짜 및 시간, 값: 로그 내용
    '''
    log_dict = {}
    for row in log_list:
        datetime_str = row[0]
        message_str = row[1]
        log_dict[datetime_str] = message_str
    return log_dict


def escape_json_string(value):
    '''JSON 문자열에 들어갈 특수문자를 이스케이프 처리한다.'''
    result = []
    for char in value:
        if char == '\\':
            result.append('\\\\')
        elif char == '"':
            result.append('\\"')
        elif char == '\n':
            result.append('\\n')
        elif char == '\r':
            result.append('\\r')
        elif char == '\t':
            result.append('\\t')
        else:
            result.append(char)
    return ''.join(result)


def dict_to_json_string(data):
    '''
    사전 객체를 JSON 형식 문자열로 변환한다.
    json 모듈 없이 Python 기본 기능만 사용한다.
    '''
    pairs = []
    for key, value in data.items():
        key_json = '"' + escape_json_string(str(key)) + '"'
        value_json = '"' + escape_json_string(str(value)) + '"'
        pairs.append(key_json + ': ' + value_json)
    return '{\n  ' + ',\n  '.join(pairs) + '\n}'


def save_json_file(file_path, json_text):
    '''JSON 문자열을 파일로 저장한다.'''
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_text)
        print(f'[시스템] JSON 파일 저장 완료: {file_path}')
        return True
    except OSError as e:
        print(f'파일 쓰기 오류: {e}')
        return False


def search_in_dict(log_dict, keyword):
    '''
    보너스 과제: 사전 값(로그 내용)에서 특정 문자열을 검색해 출력한다.
    대소문자 구분 없이 검색한다.
    '''
    if not keyword:
        print('검색어가 비어 있습니다.')
        return

    found = False
    keyword_lower = keyword.lower()
    print(f'\n--- [{keyword}] 검색 결과 ---')

    for datetime_str, message_str in log_dict.items():
        if keyword_lower in message_str.lower():
            print(f'시간: {datetime_str}')
            print(f'내용: {message_str}')
            print('-' * 40)
            found = True

    if not found:
        print('검색 결과가 없습니다.')


def print_log_list(title, log_list):
    '''리스트 내용을 보기 좋게 화면에 출력한다.'''
    print(f'\n--- [{title}] ---')
    for row in log_list:
        print(row)


def main():
    # 스크립트와 같은 폴더 기준으로 파일 경로 설정
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, 'mission_computer_main.log')
    json_path = os.path.join(base_dir, 'mission_computer_main.json')

    # 1. 로그 파일 읽기 및 원문 출력
    log_text = read_log_file(log_path)
    if log_text is None:
        return

    print('--- [원본 로그 파일 내용] ---')
    print(log_text)

    # 2. CSV 로그를 리스트로 변환 후 출력
    log_list = parse_log_to_list(log_text)
    print_log_list('리스트로 변환된 로그', log_list)

    # 3. 시간 역순 정렬 후 출력
    sorted_list = sort_log_list_reverse(log_list)
    print_log_list('시간 역순 정렬된 리스트', sorted_list)

    # 4. 리스트를 사전으로 변환
    log_dict = list_to_dict(sorted_list)
    print('\n--- [사전으로 변환된 로그] ---')
    for dt, msg in log_dict.items():
        print(f'{dt}: {msg}')

    # 5. 사전을 JSON 문자열로 만들어 파일 저장
    json_text = dict_to_json_string(log_dict)
    save_json_file(json_path, json_text)

    # 6. 보너스: 사용자 입력 키워드 검색
    try:
        keyword = input('\n검색할 키워드를 입력하세요 (예: Oxygen): ').strip()
    except EOFError:
        keyword = ''
    if keyword:
        search_in_dict(log_dict, keyword)


if __name__ == '__main__':
    main()
