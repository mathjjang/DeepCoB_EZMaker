"""
버저 모듈 예제 3: 사용자 정의 멜로디 만들기
사용자 정의 멜로디를 생성하고 재생하는 방법을 보여줍니다.
"""

import buzzer
import time
import sys

def main():
    buzzer_obj = None
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
# 예: import buzzer_example.sample3 as s3; s3.run()
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