"""
버저 모듈 예제 2: 내장 멜로디 재생
다양한 내장 멜로디를 재생하는 방법을 보여줍니다.
"""

import buzzer
import time
import sys

def main():
    buzzer_obj = None
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
# 예: import buzzer_example.sample2 as s2; s2.run()
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