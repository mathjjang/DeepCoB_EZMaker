"""
버저 모듈 예제 6: 재생 중지 및 리소스 정리
스레드를 사용한 멜로디 재생과 적절한 리소스 정리 방법을 보여줍니다.
"""

import buzzer
import time
import _thread
import sys

def main():
    buzzer_obj = None
    play_active = False  # 스레드 제어 플래그
    
    try:
        print("버저 모듈 예제 6: 재생 중지 및 리소스 정리")
        
        # 버저 인스턴스 가져오기
        buzzer_obj = buzzer.get_buzzer_instance()
        
        # 재생 활성화 플래그
        play_active = True
        
        # 다른 스레드에서 멜로디 재생
        def play_music_thread():
            local_buzzer = buzzer_obj  # 버저 객체의 로컬 참조 유지
            print("멜로디 재생 스레드 시작")
            melody_index = 0
            melodies = ["TWINKLE", "FUR_ELISE", "SCHOOL_BELL"]
            
            try:
                while play_active:
                    # 플래그 확인: 빠른 종료 보장
                    if not play_active:
                        break
                        
                    try:
                        if local_buzzer and not local_buzzer.is_playing():
                            melody_name = melodies[melody_index]
                            print(f"스레드에서 재생: {melody_name}")
                            local_buzzer.play_melody_by_name(melody_name, tempo=80)
                            
                            # 다음 멜로디로
                            melody_index = (melody_index + 1) % len(melodies)
                    except:
                        # 스레드에서 예외 발생 시 조용히 처리
                        if not play_active:  # 종료 플래그 확인
                            break
                    
                    # 짧은 대기 시간으로 반응성 향상
                    for _ in range(5):  # 0.5초를 0.1초 간격으로 분할
                        if not play_active:
                            break
                        time.sleep(0.1)
            finally:
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
        if buzzer_obj:
            buzzer_obj.stop()
        time.sleep(1)
        
        # 새로운 비프음 재생
        print("비프음 재생")
        if buzzer_obj:
            buzzer_obj.beep(count=2, frequency=1500, duration_ms=200, interval_ms=200)
        time.sleep(1)
        
        # 스레드 종료 준비 및 리소스 정리
        print("\n스레드 종료 준비")
        play_active = False
        time.sleep(1)  # 스레드가 종료될 시간 제공 (2초에서 1초로 변경)
        
        print("버저 리소스 해제")
        if buzzer_obj:
            buzzer_obj.deinit()
        
        print("예제 완료")

    except KeyboardInterrupt:
        print("\n프로그램이 사용자에 의해 중단되었습니다.")
        # 먼저 스레드 종료 플래그 설정
        play_active = False
        print("스레드 종료 중...")
        time.sleep(1)  # 스레드 종료를 위한 충분한 시간
        
        # 즉시 버저 중지를 시도
        if buzzer_obj:
            try:
                buzzer_obj.stop()
                print("버저 중지됨 (인터럽트 처리)")
            except Exception as e:
                print(f"버저 중지 중 오류: {e}")
    except Exception as e:
        print(f"\n오류 발생: {e}")
    finally:
        # 항상 스레드 종료 플래그 설정
        play_active = False
        print("리소스 정리 중...")
        time.sleep(1)  # 스레드 종료 대기 (더 긴 시간으로 변경)
        
        # 항상 버저 정지 및 리소스 정리
        if buzzer_obj:
            try:
                # 한번 더 확실하게 stop 호출
                buzzer_obj.stop()
                print("버저 중지됨")
                
                # PWM 리소스 완전 해제
                buzzer_obj.deinit()
                print("버저 리소스 해제됨")
            except Exception as e:
                print(f"리소스 정리 중 오류: {e}")
                # 마지막 수단으로 싱글톤 리셋
                try:
                    buzzer.reset_instance()
                    print("버저 인스턴스 강제 리셋")
                except:
                    pass

# 모듈로 불러올 때는 자동 실행되지 않음
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n메인 프로그램 인터럽트 발생")
        # 싱글톤 인스턴스 강제 리셋
        try:
            buzzer.reset_instance()
            print("버저 인스턴스 강제 리셋 (메인)")
        except:
            pass
        sys.exit(1)

# 이 함수를 호출하여 샘플을 직접 실행할 수 있음
# 예: import buzzer_example.sample6 as s6; s6.run()
def run():
    buzzer.reset_instance()
    try:
        main()
    except KeyboardInterrupt:
        print("\nrun() 함수 인터럽트 발생")
        # 추가 인스턴스 리셋
        try:
            buzzer.reset_instance()
            print("버저 인스턴스 강제 리셋 (run)")
        except:
            pass 