# main.py
import gc
import time
#import ubinascii
# 메모리 정리 (선택적)
gc.collect()

# === config 모듈 안전 로딩 및 기본값 설정 ===
try:
    import config
    # firmware_source 안전 접근
    firmware_version = getattr(config, 'firmware_source', 'unknown')
    if firmware_version and firmware_version != 'unknown':
        print(f"firmware version: {firmware_version}")
    else:
        print("firmware version: unknown (config.firmware_source 설정 없음)")
    
    # repl_flag 안전 접근 (기본값: False - IoT 모드)
    repl_flag = getattr(config, 'repl_flag', False)
    
except ImportError:
    print("Warning: config.py 파일을 읽을 수 없습니다. 기본값을 사용합니다.")
    firmware_version = 'unknown'
    repl_flag = False  # 기본값: IoT 모드
except Exception as e:
    print(f"Warning: config 로딩 중 오류 발생: {e}")
    firmware_version = 'unknown'
    repl_flag = False  # 기본값: IoT 모드

# 모드에 따라 적절한 BLE 모듈 로드
if repl_flag:
    import ble_repl
    ble_repl.start()
    print(f"BLE REPL mode initialized")
else:
    # IoT 모드 - bleIoT.py 사용
    print("Starting BLE in IoT mode.....")
    import bleIoT
    print("BLE IoT mode initialized")

    

print("Initialization complete.")

