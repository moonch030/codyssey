import os
import csv


def search_keyword_in_csvs(keyword, records_dir='records'):
    '''
    CSV 파일 목록을 돌면서 특정 키워드가 포함된 행을 찾아 출력하는 함수
    '''
    possible_paths = [
        records_dir,
        os.path.join('day10', 'records'),
        os.path.join('..', 'records'),
        os.path.join('..', 'day10', 'records'),
        os.path.join('..', '..', 'records')
    ]
    resolved_dir = None
    for path in possible_paths:
        if os.path.exists(path) and os.path.isdir(path):
            resolved_dir = path
            break

    if resolved_dir is None:
        print('records 폴더를 찾을 수 없습니다.')
        return

    records_dir = resolved_dir
    files = os.listdir(records_dir)

    csv_files = [f for f in files if f.endswith('.CSV') or f.endswith('.csv')]

    if not csv_files:
        print('검색할 CSV 파일이 없습니다.')
        return

    found = False
    print(f'\'{keyword}\' 키워드로 검색을 시작합니다...\n')

    for file_name in csv_files:
        filepath = os.path.join(records_dir, file_name)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)  # 헤더 읽기
                if not header:
                    continue

                # 각 행에서 키워드 검색
                for row in reader:
                    if len(row) >= 2:
                        time_str = row[0]
                        text_str = row[1]
                        if keyword.lower() in text_str.lower():
                            print(f'파일: {file_name}')
                            print(f'시간: {time_str}')
                            print(f'텍스트: {text_str}')
                            print('-' * 40)
                            found = True
        except Exception as e:
            print(f'{file_name} 파일 읽기 오류: {e}')

    if not found:
        print('검색 결과가 없습니다.')


if __name__ == '__main__':
    keyword_input = input('검색할 키워드를 입력하세요: ')
    if keyword_input.strip():
        search_keyword_in_csvs(keyword_input.strip())
    else:
        print('키워드를 입력하지 않았습니다.')
