"""
BLE 모드 전환 간단 스크립트

사용법:
1. 현재 모드 확인: 인자 없이 실행
2. REPL 모드로 변경: change_repl_simple.py repl
3. IoT 모드로 변경: change_repl_simple.py iot
"""

import sys
import machine
import time

def read_current_mode():
    """config.py 파일에서 현재 repl_flag 값을 읽어옵니다."""
    try:
        import config
        # repl_flag 안전 접근 (기본값: False - IoT 모드)
        return getattr(config, 'repl_flag', False)
    except ImportError:
        print("config.py 파일을 찾을 수 없습니다.")
        return False  # 기본값: IoT 모드
    except Exception as e:
        print(f"설정을 읽는 중 오류 발생: {e}")
        return False  # 기본값: IoT 모드

def change_mode(new_mode_value):
    """config.py 파일의 repl_flag 값을 변경합니다."""
    try:
        # 기존 config에서 firmware_source 값 보존 시도
        existing_firmware_source = "unknown"
        try:
            import config
            existing_firmware_source = getattr(config, 'firmware_source', "unknown")
        except:
            pass  # 기존 설정을 읽을 수 없어도 계속 진행
        
        # 파일을 완전히 새로 생성
        new_content = [
            '"""\n',
            'ESP32-S3 BLE 모드 설정 파일\n',
            '\n',
            '이 파일은 BLE 통신 모드를 결정하는 설정값을 포함합니다.\n',
            '- repl_flag = True: REPL 모드로 실행 (ble_repl.py 사용)\n',
            '- repl_flag = False: IoT 모드로 실행 (bleIoT.py 사용)\n',
            '- firmware_source: 펌웨어 버전 정보\n',
            '"""\n',
            '\n',
            '# BLE 모드 설정\n',
            f'repl_flag = {new_mode_value}  # True: REPL 모드, False: IoT 센서 모드\n',
            '\n',
            '# 펌웨어 버전 정보\n',
            f'firmware_source = "{existing_firmware_source}"  # 펌웨어 버전\n',
            '\n'
        ]
        
        # 파일 쓰기
        with open('config.py', 'w') as file:
            for line in new_content:
                file.write(line)
        
        # 파일이 제대로 저장되었는지 확인
        print("config.py 파일을 새로 생성했습니다.")
        print(f"모드 설정: repl_flag = {new_mode_value}")
        print(f"펌웨어 버전: firmware_source = \"{existing_firmware_source}\"")
        
        # 메모리에서 config 모듈 제거 (다음 import 시 새로 로드되도록)
        #if 'config' in sys.modules:
        #    del sys.modules['config']
        #    print("메모리에서 기존 config 모듈을 제거했습니다.")
        time.sleep(1)
        machine.reset()
        return True
    except Exception as e:
        print(f"설정 변경 중 오류 발생: {e}")
        return False

def main():
    # 현재 모드 확인
    current_mode = read_current_mode()
    
    # 인자 확인
    if len(sys.argv) < 2:
        # 인자가 없으면 현재 모드 표시
        print(f"현재 모드: {'REPL' if current_mode else 'IoT'} (repl_flag = {current_mode})")
        return
    
    # 인자에 따라 모드 변경
    if sys.argv[1].lower() in ['repl', 'true', '1']:
        # REPL 모드로 변경
        if current_mode:
            print("이미 REPL 모드입니다.")
        else:
            if change_mode(True):
                print("REPL 모드로 변경되었습니다.")
                print("3초 후 재시작합니다...")
                time.sleep(3)
                machine.reset()
                
    elif sys.argv[1].lower() in ['iot', 'false', '0']:
        # IoT 모드로 변경
        if not current_mode:
            print("이미 IoT 모드입니다.")
        else:
            if change_mode(False):
                print("IoT 모드로 변경되었습니다.")
                print("3초 후 재시작합니다...")
                time.sleep(3)
                machine.reset()
    else:
        print("알 수 없는 모드입니다. 'repl' 또는 'iot'를 사용하세요.")

if __name__ == "__main__":
    main() 