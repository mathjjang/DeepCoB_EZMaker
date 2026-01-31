"""
ESP32-S3 카메라 모듈 테스트 스크립트

이 스크립트는 cameraModule.py에서 제공하는 CameraModule 클래스를 테스트합니다.
다양한 해상도에서 카메라 프레임을 캡처하고 각 프레임의 크기와 속성을 출력합니다.
"""

import time
import gc
import sys
from cameraModule import CameraModule

def main():
    print("=" * 50)
    print("카메라 모듈 테스트")
    print("=" * 50)
    
    # 테스트할 해상도 목록
    resolutions = ["QQVGA", "QVGA", "VGA"]  # 저해상도부터 시작
    
    try:
        # 카메라 모듈 인스턴스 생성 (디버그 모드 활성화)
        camera = CameraModule(debug=True)
        
        print("\n메모리 사용량:")
        gc.collect()
        free_mem = gc.mem_free() // 1024
        used_mem = gc.mem_alloc() // 1024
        total_mem = (free_mem + used_mem)
        print(f"  - 여유: {free_mem}KB, 사용: {used_mem}KB, 총: {total_mem}KB ({used_mem/total_mem*100:.1f}%)")
        
        for resolution in resolutions:
            print(f"\n[{resolution}] 해상도 테스트")
            
            # 카메라 초기화 (이전 상태가 있다면 해제 후 재초기화)
            if camera.is_initialized():
                camera.deinit()
                
            # 현재 해상도로 초기화
            success = camera.init(frame_size=resolution, quality=70)
            if not success:
                print(f"  - {resolution} 해상도 초기화 실패!")
                continue
                
            # 프레임 캡처 시도
            print(f"  - 프레임 캡처 시도...")
            start_time = time.ticks_ms()
            frame = camera.capture_frame()
            elapsed = time.ticks_diff(time.ticks_ms(), start_time)
            
            if frame:
                # 메모리 사이즈 변환
                size_kb = len(frame) / 1024
                
                # 해상도 정보 (대략적인 매핑)
                resolution_info = {
                    "QQVGA": "160x120",
                    "QVGA": "320x240", 
                    "VGA": "640x480",
                    "SVGA": "800x600", 
                    "XGA": "1024x768",
                    "HD": "1280x720",
                    "SXGA": "1280x1024", 
                    "UXGA": "1600x1200"
                }.get(resolution, "알 수 없음")
                
                print(f"  - 캡처 성공!")
                print(f"  - 프레임 크기: {len(frame)} 바이트 ({size_kb:.2f}KB)")
                print(f"  - 해상도: {resolution} ({resolution_info})")
                print(f"  - 캡처 시간: {elapsed}ms")
                
                # JPEG 유효성 검사 확인
                is_valid = camera.validate_jpeg(frame)
                print(f"  - 유효한 JPEG: {'예' if is_valid else '아니오'}")
                
                # 메모리 해제
                frame = None
                gc.collect()
            else:
                print(f"  - 프레임 캡처 실패!")
                
            # 메모리 사용량 출력
            gc.collect()
            free_mem = gc.mem_free() // 1024
            used_mem = gc.mem_alloc() // 1024
            print(f"  - 메모리: 여유 {free_mem}KB, 사용 {used_mem}KB ({used_mem/(free_mem+used_mem)*100:.1f}%)")
            
        # 테스트 후 메모리 정리
        camera.deinit()
        camera = None
        gc.collect()
        
        print("\n" + "=" * 50)
        print("테스트 완료")
        print("=" * 50)
        
    except Exception as e:
        sys.print_exception(e)
        print("\n테스트 중 오류 발생!")
    finally:
        # 카메라 리소스 정리
        try:
            if 'camera' in locals() and camera is not None:
                camera.deinit()
        except:
            pass

# 직접 실행될 때만 main() 함수 호출
if __name__ == "__main__":
    main() 