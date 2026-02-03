"""
버저 모듈 예제 1: 기본 비프음 재생
다양한 비프음과 패턴 재생 방법을 보여줍니다.
"""

import buzzer
import time
import sys

def main():
    buzzer_obj = None
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
# 예: import buzzer_example.sample1 as s1; s1.run()
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