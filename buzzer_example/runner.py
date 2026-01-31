"""
버저 예제 실행기

이 모듈은 샘플 코드를 함수로 래핑하여 반복 실행 가능하도록 합니다.
MicroPython의 REPL에서 쉽게 사용하기 위한 모듈입니다.
"""

import buzzer
import time
import _thread

def run_sample1():
    """기본 비프음 재생 예제 실행"""
    buzzer.reset_instance()  # 인스턴스 리셋
    
    try:
        print("버저 모듈 예제 1: 기본 비프음 재생")
        
        # 버저 인스턴스 가져오기
        buzzer_obj = buzzer.get_buzzer_instance()

        # 단일 비프음 재생
        print("단일 비프음 재생")
        buzzer_obj.beep()
        time.sleep(1)

        # 다양한 주파수, 길이의 비프음
        print("다양한 주파수, 길이의 비프음")
        buzzer_obj.beep(count=1, frequency=1500, duration_ms=200)
        time.sleep(1)

        # 여러 번 반복되는 비프음
        print("여러 번 반복되는 비프음")
        buzzer_obj.beep(count=3, frequency=2000, duration_ms=100, interval_ms=150)
        
        print("예제 완료")

    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    finally:
        # 항상 버저 정지 및 리소스 정리
        if 'buzzer_obj' in locals():
            buzzer_obj.stop()
            print("버저 중지됨")
            buzzer_obj.deinit()  # 리소스 완전 해제
            print("버저 리소스 해제됨")

def run_sample2():
    """내장 멜로디 재생 예제 실행"""
    buzzer.reset_instance()  # 인스턴스 리셋
    
    try:
        print("버저 모듈 예제 2: 내장 멜로디 재생")
        
        # 버저 인스턴스 가져오기
        buzzer_obj = buzzer.get_buzzer_instance()

        # 작은별 변주곡 재생
        print("재생: 작은별 변주곡")
        buzzer_obj.play_melody_by_name("TWINKLE", tempo=100)
        time.sleep(1)

        # 엘리제를 위하여 재생
        print("재생: 엘리제를 위하여")
        buzzer_obj.play_melody_by_name("FUR_ELISE", tempo=120)
        time.sleep(1)

        # 학교종이 땡땡땡 재생
        print("재생: 학교종이 땡땡땡")
        buzzer_obj.play_melody_by_name("SCHOOL_BELL", tempo=110)
        
        print("예제 완료")

    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    finally:
        # 항상 버저 정지 및 리소스 정리
        if 'buzzer_obj' in locals():
            buzzer_obj.stop()
            print("버저 중지됨")
            buzzer_obj.deinit()  # 리소스 완전 해제
            print("버저 리소스 해제됨")

def run_sample3():
    """사용자 정의 멜로디 예제 실행"""
    buzzer.reset_instance()  # 인스턴스 리셋
    
    try:
        print("버저 모듈 예제 3: 사용자 정의 멜로디 만들기")
        
        # 버저 인스턴스 가져오기
        buzzer_obj = buzzer.get_buzzer_instance()

        # 작은 사용자 정의 멜로디 만들기
        # (음표 주파수, 음표 유형) 형식으로 구성된 리스트
        # C - D - E - F - G - A - B - C
        my_scale = [
            (buzzer.NOTE_C4, '4'),  # 도
            (buzzer.NOTE_D4, '4'),  # 레
            (buzzer.NOTE_E4, '4'),  # 미
            (buzzer.NOTE_F4, '4'),  # 파
            (buzzer.NOTE_G4, '4'),  # 솔
            (buzzer.NOTE_A4, '4'),  # 라
            (buzzer.NOTE_B4, '4'),  # 시
            (buzzer.NOTE_C5, '2'),  # 도(높은 옥타브)
        ]

        print("재생: 사용자 정의 음계")
        buzzer_obj.play_melody(my_scale, tempo=120)
        
        # 간단한 멜로디: 작은별 일부분
        little_star = [
            (buzzer.NOTE_C4, '4'), (buzzer.NOTE_C4, '4'), 
            (buzzer.NOTE_G4, '4'), (buzzer.NOTE_G4, '4'),
            (buzzer.NOTE_A4, '4'), (buzzer.NOTE_A4, '4'), 
            (buzzer.NOTE_G4, '2')
        ]
        
        time.sleep(1)
        print("재생: 작은별 일부분")
        buzzer_obj.play_melody(little_star, tempo=100)
        
        print("예제 완료")

    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    finally:
        # 항상 버저 정지 및 리소스 정리
        if 'buzzer_obj' in locals():
            buzzer_obj.stop()
            print("버저 중지됨")
            buzzer_obj.deinit()  # 리소스 완전 해제
            print("버저 리소스 해제됨")

def run_sample4():
    """효과음 재생 예제 실행"""
    buzzer.reset_instance()  # 인스턴스 리셋
    
    try:
        print("버저 모듈 예제 4: 효과음 재생")
        
        # 버저 인스턴스 가져오기
        buzzer_obj = buzzer.get_buzzer_instance()

        # 간단한 효과음 재생
        print("재생: 비프음")
        buzzer_obj.play_melody_by_name("BEEP")
        time.sleep(1)

        print("재생: 성공 효과음")
        buzzer_obj.play_melody_by_name("SUCCESS")
        time.sleep(1)

        print("재생: 오류 효과음")
        buzzer_obj.play_melody_by_name("ERROR")
        time.sleep(1)

        print("재생: 경고 효과음")
        buzzer_obj.play_melody_by_name("ALERT")
        
        print("예제 완료")

    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    finally:
        # 항상 버저 정지 및 리소스 정리
        if 'buzzer_obj' in locals():
            buzzer_obj.stop()
            print("버저 중지됨")
            buzzer_obj.deinit()  # 리소스 완전 해제
            print("버저 리소스 해제됨")

def run_sample5():
    """단일 음표 및 톤 재생 예제 실행"""
    buzzer.reset_instance()  # 인스턴스 리셋
    
    try:
        print("버저 모듈 예제 5: 단일 음표 및 톤 재생")
        
        # 버저 인스턴스 가져오기
        buzzer_obj = buzzer.get_buzzer_instance()

        # 특정 주파수 재생
        print("A4 음표 (440Hz) 재생")
        buzzer_obj.play_tone(440, 500)  # A4 음표 0.5초 재생
        time.sleep(0.5)

        # 모스 부호 SOS 패턴 (... --- ...)
        def play_sos():
            print("SOS 모스 부호 패턴 시작")
            
            # 짧은 신호 3번
            for _ in range(3):
                buzzer_obj.play_note(2000, 200)
                time.sleep(0.1)
            time.sleep(0.3)
            
            # 긴 신호 3번
            for _ in range(3):
                buzzer_obj.play_note(2000, 600)
                time.sleep(0.1)
            time.sleep(0.3)
            
            # 짧은 신호 3번
            for _ in range(3):
                buzzer_obj.play_note(2000, 200)
                time.sleep(0.1)
                
            print("SOS 모스 부호 패턴 완료")

        print("재생: SOS 모스 부호")
        play_sos()
        
        # 주파수 슬라이드
        print("주파수 슬라이드 재생 (저음→고음)")
        for freq in range(500, 2500, 100):
            buzzer_obj.play_note(freq, 50)
        
        time.sleep(0.5)
        
        print("주파수 슬라이드 재생 (고음→저음)")
        for freq in range(2500, 500, -100):
            buzzer_obj.play_note(freq, 50)
        
        print("예제 완료")

    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    finally:
        # 항상 버저 정지 및 리소스 정리
        if 'buzzer_obj' in locals():
            buzzer_obj.stop()
            print("버저 중지됨")
            buzzer_obj.deinit()  # 리소스 완전 해제
            print("버저 리소스 해제됨")

def run_sample6():
    """재생 중지 및 리소스 정리 예제 실행"""
    buzzer.reset_instance()  # 인스턴스 리셋
    
    try:
        print("버저 모듈 예제 6: 재생 중지 및 리소스 정리")
        
        # 버저 인스턴스 가져오기
        buzzer_obj = buzzer.get_buzzer_instance()
        
        # 재생 활성화 플래그
        play_active = True
        
        # 다른 스레드에서 멜로디 재생
        def play_music_thread():
            print("멜로디 재생 스레드 시작")
            melody_index = 0
            melodies = ["TWINKLE", "FUR_ELISE", "SCHOOL_BELL"]
            
            while play_active:
                if not buzzer_obj.is_playing():
                    melody_name = melodies[melody_index]
                    print(f"스레드에서 재생: {melody_name}")
                    buzzer_obj.play_melody_by_name(melody_name, tempo=80)
                    
                    # 다음 멜로디로
                    melody_index = (melody_index + 1) % len(melodies)
                    time.sleep(0.5)
            
            print("멜로디 재생 스레드 종료")

        # 스레드 시작
        music_thread = _thread.start_new_thread(play_music_thread, ())
        
        # 메인 스레드에서는 제어 및 정보 출력
        print("5초 동안 멜로디 재생...")
        for i in range(5, 0, -1):
            print(f"{i}초 남음")
            time.sleep(1)
        
        # 재생 중지
        print("\n재생 중지 명령")
        buzzer_obj.stop()
        time.sleep(1)
        
        # 새로운 비프음 재생
        print("비프음 재생")
        buzzer_obj.beep(count=2, frequency=1500, duration_ms=200, interval_ms=200)
        time.sleep(1)
        
        # 스레드 종료 준비 및 리소스 정리
        print("\n스레드 종료 준비")
        play_active = False
        time.sleep(2)  # 스레드가 종료될 시간 제공
        
        print("버저 리소스 해제")
        buzzer_obj.deinit()
        
        print("예제 완료")

    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    finally:
        # 항상 스레드 종료 플래그 설정 및 버저 리소스 정리
        if 'play_active' in locals():
            play_active = False
        
        if 'buzzer_obj' in locals():
            buzzer_obj.stop()
            print("버저 중지됨")
            # 완전히 리소스 해제
            buzzer_obj.deinit()
            print("버저 리소스 해제됨")

# 샘플 실행 방법 안내
print("""
버저 예제 실행기 (runner.py)

다음 함수를 호출하여 예제를 실행하세요:
- run_sample1(): 기본 비프음 재생
- run_sample2(): 내장 멜로디 재생
- run_sample3(): 사용자 정의 멜로디
- run_sample4(): 효과음 재생
- run_sample5(): 단일 음표 및 톤 재생
- run_sample6(): 재생 중지 및 리소스 정리

예: 
>>> import buzzer_example.runner as buzzer_runner
>>> buzzer_runner.run_sample1()
""") 