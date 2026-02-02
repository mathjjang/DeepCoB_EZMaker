# main.py
import gc
import time
import config
#import ubinascii
# 메모리 정리 (선택적)
gc.collect()



# 모드에 따라 적절한 BLE 모듈 로드
if config.repl_flag:
    import ble_repl
    ble_repl.start()
    print(f"BLE REPL mode initialized")
else:
    # IoT 모드 - bleIoT.py 사용
    print("Starting BLE in IoT mode...")
    import bleIoT
    print("BLE IoT mode initialized")

print("Initialization complete.")

