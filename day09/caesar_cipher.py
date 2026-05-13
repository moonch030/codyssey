import os

def caesar_cipher_decode(target_text):
    """
    주어진 암호화된 문자열을 카이사르 암호 방식으로 복호화하는 함수입니다.
    """
    # 보너스 과제: 텍스트 사전 (원하는 키워드를 추가할 수 있습니다)
    dictionary = [
        'mars', 'base', 'door', 'open', 'system', 'admin', 
        'password', 'key', 'rome', 'caesar', 'security', 
        'hello', 'world', 'unlock', 'success'
    ]
    
    # 자리수는 알파벳 수인 26만큼 반복
    for shift in range(1, 27):
        decoded_text = ''
        
        for char in target_text:
            if char.isalpha():
                # 대소문자 구분하여 기준 아스키 코드 설정
                shift_base = ord('a') if char.islower() else ord('A')
                # 자리수만큼 이동하여 복호화 (문자 범위를 벗어나지 않도록 % 26 연산)
                decoded_text += chr((ord(char) - shift_base - shift) % 26 + shift_base)
            else:
                # 알파벳이 아닌 문자는 그대로 유지
                decoded_text += char
                
        print(f'자리수 {shift:2}: {decoded_text}')
        
        # 보너스 과제: 사전에 있는 단어와 일치하는 키워드가 발견될 경우 반복 멈춤
        found_keyword = False
        for word in dictionary:
            if word in decoded_text.lower():
                print(f'\n[알림] 사전에서 \'{word}\' 단어가 발견되어 반복을 중단합니다.')
                found_keyword = True
                break
                
        if found_keyword:
            break

def main():
    target_text = ''
    
    # 예외처리: 파일을 읽어오는 부분
    try:
        with open('password.txt', 'r', encoding='utf-8') as file:
            target_text = file.read().strip()
    except FileNotFoundError:
        print('오류: password.txt 파일이 존재하지 않습니다.')
        return
    except Exception as e:
        print(f'오류: 파일을 읽는 중 문제가 발생했습니다. ({e})')
        return

    print('--- 카이사르 암호 해독 시작 ---\n')
    
    # 카이사르 암호 해독 함수 호출
    caesar_cipher_decode(target_text)
    
    # 몇 번째 자리수로 암호가 해독되는지 눈으로 식별 후 입력
    try:
        shift_input = input('\n해독이 완료된 자리수(번호)를 입력하세요 (종료하려면 엔터): ')
        if not shift_input:
            print('종료합니다.')
            return
            
        shift_number = int(shift_input)
        
        # 입력받은 자리수로 최종 해독
        final_text = ''
        for char in target_text:
            if char.isalpha():
                shift_base = ord('a') if char.islower() else ord('A')
                final_text += chr((ord(char) - shift_base - shift_number) % 26 + shift_base)
            else:
                final_text += char
                
        # 예외처리: 파일을 저장하는 부분
        with open('result.txt', 'w', encoding='utf-8') as file:
            file.write(final_text)
            
        print('해독된 결과가 result.txt 파일에 성공적으로 저장되었습니다.')
        
    except ValueError:
        print('오류: 숫자를 올바르게 입력해야 합니다.')
    except Exception as e:
        print(f'오류: 파일을 저장하는 중 문제가 발생했습니다. ({e})')

if __name__ == '__main__':
    main()
