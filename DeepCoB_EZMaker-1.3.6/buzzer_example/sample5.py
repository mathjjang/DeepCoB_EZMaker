"""
버저 모듈 예제 5: 단일 음표 및 톤 재생
단일 음표와 주파수 조정 방법을 보여줍니다.
"""

import buzzer
import time
import sys

def main():
    buzzer_obj = None
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
# 예: import buzzer_example.sample5 as s5; s5.run()
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