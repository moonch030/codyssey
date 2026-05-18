import os
import wave
import datetime

try:
    import pyaudio
except ImportError:
    print('pyaudio 라이브러리가 필요합니다. pip install pyaudio 를 실행해주세요.')


def record_audio(duration=5):
    """
    지정된 시간(초) 동안 마이크로 음성을 녹음하여 파일로 저장하는 함수
    """
    chunk = 1024
    audio_format = pyaudio.paInt16
    channels = 1
    rate = 44100

    # records 폴더 생성
    if not os.path.exists('records'):
        os.makedirs('records')

    # 파일 이름 생성 (년월일-시간분초)
    now = datetime.datetime.now()
    filename = now.strftime('%Y%m%d-%H%M%S') + '.wav'
    filepath = os.path.join('records', filename)

    audio = pyaudio.PyAudio()

    print('녹음을 시작합니다...')

    stream = audio.open(format=audio_format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        frames_per_buffer=chunk)

    frames = []

    for _ in range(0, int(rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print('녹음이 완료되었습니다.')

    stream.stop_stream()
    stream.close()
    audio.terminate()

    # wav 파일로 저장
    with wave.open(filepath, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(audio_format))
        wf.setframerate(rate)
        wf.writeframes(b''.join(frames))

    print(f'파일이 저장되었습니다: {filepath}')


def find_records_in_range(start_date, end_date):
    """
    특정 범위의 날짜의 녹음 파일을 찾아 출력해주는 함수
    """
    if not os.path.exists('records'):
        print('records 폴더가 존재하지 않습니다.')
        return

    print(f'{start_date} 부터 {end_date} 까지의 녹음 파일 목록:')

    start = datetime.datetime.strptime(start_date, '%Y%m%d')
    end = datetime.datetime.strptime(end_date, '%Y%m%d')
    end = end.replace(hour=23, minute=59, second=59)

    files = os.listdir('records')
    found = False

    for file_name in files:
        if file_name.endswith('.wav'):
            try:
                date_str = file_name.split('.')[0]
                file_time = datetime.datetime.strptime(date_str, '%Y%m%d-%H%M%S')
                if start <= file_time <= end:
                    print(file_name)
                    found = True
            except ValueError:
                pass

    if not found:
        print('해당 기간에 녹음된 파일이 없습니다.')


if __name__ == '__main__':
    # 5초간 녹음 실행
    record_audio(5)

    # 보너스 과제 테스트: 오늘 날짜로 검색
    today_str = datetime.datetime.now().strftime('%Y%m%d')
    find_records_in_range(today_str, today_str)
