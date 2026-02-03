# soil_test_simple.py
# 토양수분센서 간단 실행 예제

from soil_moisture_test import SoilMoistureSensor, test_soil_moisture_sensor, calibration_helper
import time

def simple_test():
    """간단한 토양수분센서 테스트"""
    print("🌱 토양수분센서 간단 테스트")
    print("=" * 40)
    
    # 핀 1번 사용 (필요에 따라 변경)
    PIN = 2
    
    try:
        # 센서 초기화
        sensor = SoilMoistureSensor(adc_pin=PIN)
        
        print("\n📊 10회 측정 테스트:")
        for i in range(10):
            status = sensor.get_status()
            
            print(f"측정 {i+1:2d}: "
                  f"원시값={status['raw']:4d}, "
                  f"전압={status['voltage']:4.2f}V, "
                  f"수분={status['moisture_percent']:5.1f}%")
            
            time.sleep(1)
        
        print(f"\n✅ 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def continuous_monitoring():
    """연속 모니터링"""
    print("🔄 토양수분센서 연속 모니터링")
    print("=" * 40)
    print("Ctrl+C로 중지")
    
    PIN = 2
    
    try:
        sensor = SoilMoistureSensor(adc_pin=PIN)
        
        while True:
            status = sensor.get_status()
            moisture = status['moisture_percent']
            
            # 이모지로 상태 표시
            if moisture >= 70:
                emoji = "💧"
                status_text = "매우 습함"
            elif moisture >= 40:
                emoji = "🌿"
                status_text = "적당함"
            elif moisture >= 20:
                emoji = "🌾"
                status_text = "건조함"
            else:
                emoji = "🏜️"
                status_text = "매우 건조"
            
            print(f"{emoji} 수분: {moisture:5.1f}% ({status_text}) "
                  f"[전압: {status['voltage']:.2f}V, 원시값: {status['raw']}]")
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n⏹️ 모니터링 중지")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

def quick_calibration():
    """빠른 보정"""
    print("⚙️ 토양수분센서 빠른 보정")
    print("=" * 40)
    
    PIN = 2
    
    try:
        sensor = SoilMoistureSensor(adc_pin=PIN)
        
        print("현재 센서 값:")
        status = sensor.get_status()
        print(f"  원시값: {status['raw']}")
        print(f"  수분율: {status['moisture_percent']:.1f}%")
        
        print("\n보정 옵션:")
        print("1. 현재 상태를 '건조'로 설정")
        print("2. 현재 상태를 '습윤'로 설정") 
        print("3. 건조값과 습윤값 직접 입력")
        print("4. 보정 안함")
        
        choice = input("\n선택 (1-4): ").strip()
        
        if choice == "1":
            dry_val = sensor.calibrate_dry()
            print(f"✅ 건조값 설정: {dry_val}")
        elif choice == "2":
            wet_val = sensor.calibrate_wet()
            print(f"✅ 습윤값 설정: {wet_val}")
        elif choice == "3":
            try:
                dry_val = int(input("건조값 입력 (0-4095): "))
                wet_val = int(input("습윤값 입력 (0-4095): "))
                sensor.dry_value = dry_val
                sensor.wet_value = wet_val
                print(f"✅ 보정값 설정: 건조={dry_val}, 습윤={wet_val}")
            except ValueError:
                print("❌ 잘못된 입력")
                return
        else:
            print("보정하지 않음")
            return
            
        # 보정 후 테스트
        print("\n보정 후 결과:")
        for i in range(3):
            status = sensor.get_status()
            print(f"  측정 {i+1}: 수분율 {status['moisture_percent']:.1f}%")
            time.sleep(1)
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")

# 메뉴 시스템
def main_menu():
    """메인 메뉴"""
    while True:
        print("\n🌱 토양수분센서 테스트 메뉴")
        print("=" * 40)
        print("1. 간단 테스트 (10회 측정)")
        print("2. 연속 모니터링")
        print("3. 빠른 보정")
        print("4. 상세 테스트 (30초)")
        print("5. 전체 보정 가이드")
        print("0. 종료")
        
        choice = input("\n선택하세요 (0-5): ").strip()
        
        if choice == "1":
            simple_test()
        elif choice == "2":
            continuous_monitoring()
        elif choice == "3":
            quick_calibration()
        elif choice == "4":
            test_soil_moisture_sensor(pin=1, duration=30)
        elif choice == "5":
            calibration_helper(pin=1)
        elif choice == "0":
            print("👋 프로그램을 종료합니다.")
            break
        else:
            print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main_menu() 