# main.py

def read_mission_log(file_path):
    '''
    mission_computer_main.log 파일을 읽어서 화면에 출력하고
    오류 내용을 별도로 추출하여 저장합니다.
    '''
    try:
        # 파일 열기 및 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # 1. 전체 내용 화면 출력
        print('--- [전체 로그 내용] ---')
        for line in lines:
            # strip()으로 줄바꿈 중복 방지, PEP 8 공백 준수
            print(line.strip())

        # 2. 보너스 과제: 시간 역순 정렬 출력
        print('\n--- [시간 역순 로그] ---')
        for line in reversed(lines):
            print(line.strip())

        # 3. 보너스 과제: 문제가 되는 부분(ERROR/CRITICAL) 저장
        error_lines = []
        for line in lines:
            if 'ERROR' in line or 'CRITICAL' in line:
                error_lines.append(line)

        with open('error_only.log', 'w', encoding='utf-8') as ef:
            for error in error_lines:
                ef.write(error)
        
        print('\n[시스템] 분석 완료. 에러 로그가 error_only.log에 저장되었습니다.')

    except FileNotFoundError:
        print('오류: mission_computer_main.log 파일을 찾을 수 없습니다.')
    except Exception as e:
        print(f'예상치 못한 오류 발생: {e}')

if __name__ == '__main__':
    # 로그 파일 이름 지정
    log_file = 'mission_computer_main.log'
    read_mission_log(log_file)