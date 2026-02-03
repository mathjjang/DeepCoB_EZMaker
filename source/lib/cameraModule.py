"""
카메라 모듈 - ESP32-S3용 범용 카메라 인터페이스 클래스

이 모듈은 ESP32-S3에 연결된 카메라를 제어하기 위한 독립적인 클래스를 제공합니다.
다양한 애플리케이션에서 재사용할 수 있는 핵심 카메라 기능을 구현합니다.
"""

import time
import gc
import array
import logger  # 로거 모듈 임포트

class CameraModule:
    def __init__(self):
        """
        카메라 모듈 초기화
        """
        self.camera_enabled = False
        self.cam = None             # 카메라 객체
        self.frame_size = "QVGA"    # 기본 프레임 크기 (320x240)
        self.quality = 85           # 기본 품질 (1-85)
        self.fb_count = 2           # 프레임 버퍼 수

    def init(self, frame_size="QVGA", quality=85, fb_count=2):
        """
        카메라 초기화 및 설정
        
        Args:
            frame_size: 프레임 크기 ("QVGA", "VGA", "SVGA" 등)
            quality: JPEG 품질 (1-85, 숫자가 클수록 고품질)
            fb_count: 프레임 버퍼 수
        
        Returns:
            bool: 초기화 성공 여부
        """
        self.frame_size = frame_size
        self.quality = max(1, min(85, quality))
        self.fb_count = fb_count
        
        try:
            logger.info("카메라 초기화 시도...", "CAM")
            from camera import Camera, GrabMode, PixelFormat, FrameSize
            
            # 카메라 객체 생성
            self.cam = Camera(
                data_pins=[11, 9, 8, 10, 12, 18, 17, 16],
                vsync_pin=6, href_pin=7, sda_pin=4, scl_pin=5,
                pclk_pin=13, xclk_pin=15, xclk_freq=20000000,
                powerdown_pin=-1, reset_pin=-1
            )
            
            # 프레임 크기 매핑
            size_map = {
                "QQVGA": FrameSize.QQVGA,    # 160x120
                "QVGA": FrameSize.QVGA,      # 320x240
                "VGA": FrameSize.VGA,        # 640x480
                "SVGA": FrameSize.SVGA,      # 800x600
                "XGA": FrameSize.XGA,        # 1024x768
                "HD": FrameSize.HD,          # 1280x720
                "SXGA": FrameSize.SXGA,      # 1280x1024
                "UXGA": FrameSize.UXGA       # 1600x1200
            }
            
            selected_size = size_map.get(frame_size.upper(), FrameSize.QVGA)
            
            # 카메라 구성
            self.cam.reconfigure(
                pixel_format=PixelFormat.JPEG,
                frame_size=selected_size,
                grab_mode=GrabMode.LATEST,
                fb_count=self.fb_count
            )
            
            # 이미지 품질 설정
            self.cam.set_quality(self.quality)
            
            # 카메라 초기화
            self.cam.init()
            #self.cam.set_hmirror(True)
            self.camera_enabled = True
            logger.info(f"카메라 초기화 성공. 크기: {frame_size}, 품질: {quality}%, 버퍼: {fb_count}", "CAM")
            return True
            
        except Exception as e:
            logger.error(f"카메라 초기화 실패: {e}", "CAM")
            if self.cam is not None:
                try:
                    self.cam.deinit()
                except:
                    pass
            self.camera_enabled = False
            self.cam = None
             # 카메라 초기화 실패 시 자동 하드 리셋 수행
            logger.critical("Camera initialization failed!", "CAM")
            logger.warning("Performing automatic hard reset in 3 seconds...", "CAM")
            for i in range(3, 0, -1):
                logger.info(f"{i}...", "CAM")
                time.sleep(0.5)
            logger.critical("Resetting now!", "CAM")
            import machine
            machine.reset()  # 하드 리셋 수행
            return False

    def deinit(self):
        """카메라 리소스 해제"""
        if self.cam is not None:
            try:
                self.cam.deinit()
                logger.info("카메라 리소스 해제 완료", "CAM")
            except Exception as e:
                logger.error(f"카메라 리소스 해제 중 오류: {e}", "CAM")
            self.cam = None
        self.camera_enabled = False

    def is_initialized(self):
        """카메라가 초기화되었는지 확인"""
        return self.camera_enabled and self.cam is not None

    def set_flip(self, vertical=False, horizontal=False):
        """
        카메라 이미지 반전 설정
        
        Args:
            vertical: 수직 반전 여부
            horizontal: 수평 반전 여부
            
        Returns:
            bool: 설정 성공 여부
        """
        if not self.is_initialized():
            logger.warning("카메라가 초기화되지 않음", "CAM")
            return False
            
        try:
            if vertical:
                self.cam.set_vflip(True)
                logger.info("수직 반전 활성화", "CAM")
            
            if horizontal:
                self.cam.set_hmirror(True)
                logger.info("수평 반전 활성화", "CAM")
                
            return True
        except Exception as e:
            logger.error(f"이미지 반전 설정 오류: {e}", "CAM")
            return False

    def set_quality(self, quality):
        """
        카메라 이미지 품질 설정
        
        Args:
            quality: JPEG 품질 (1-85, 숫자가 클수록 고품질)
            
        Returns:
            bool: 설정 성공 여부
        """
        if not self.is_initialized():
            logger.warning("카메라가 초기화되지 않음", "CAM")
            return False
            
        try:
            quality = max(1, min(85, quality))
            self.cam.set_quality(quality)
            self.quality = quality
            logger.info(f"이미지 품질 {quality}로 설정", "CAM")
            return True
        except Exception as e:
            logger.error(f"품질 설정 오류: {e}", "CAM")
            return False

    def capture_frame(self):
        """
        카메라 프레임 캡처
        
        Returns:
            bytes/bytearray/array.array: 캡처된 JPEG 이미지 데이터 또는 실패 시 None
        """
        if not self.is_initialized():
            logger.warning("카메라가 초기화되지 않음", "CAM")
            return None
            
        # 메모리 부족 방지를 위한 GC 실행
        gc.collect()
        
        # 먼저 한 번 캡처 시도
        try:
            buf = self.cam.capture()
            if buf:
                frame = array.array('B', buf)
                buf = None  # 원본 버퍼 해제
                gc.collect()
                
                if frame and len(frame) > 0 and self.validate_jpeg(frame):
                    logger.debug(f"프레임 캡처 성공: {len(frame)} 바이트", "CAM")
                    return frame
        except Exception as e:
            logger.error(f"첫 번째 프레임 캡처 시도 실패: {e}", "CAM")
        
        # 첫 시도가 실패했을 경우 재시도 (최대 2회)
        max_retries = 2
        for retry in range(max_retries):
            try:
                logger.info(f"프레임 캡처 재시도 {retry+1}/{max_retries}", "CAM")
                
                # 센서 안정화를 위해 짧은 대기
                time.sleep_ms(100)
                
                # 캡처 시도
                buf = self.cam.capture()
                if buf:
                    frame = array.array('B', buf)
                    buf = None  # 원본 버퍼 해제
                    gc.collect()
                    
                    if frame and len(frame) > 0 and self.validate_jpeg(frame):
                        logger.info(f"프레임 캡처 성공 (재시도 {retry+1}): {len(frame)} 바이트", "CAM")
                        return frame
            except Exception as e:
                logger.error(f"프레임 캡처 재시도 {retry+1} 실패: {e}", "CAM")
                gc.collect()
                
            # 실패 후 좀 더 긴 대기
            time.sleep_ms(100)  #200
        
        logger.error("모든 프레임 캡처 시도 실패", "CAM")
        return None

    def validate_jpeg(self, frame):
        """
        JPEG 이미지 데이터 검증
        
        Args:
            frame: 검증할 이미지 데이터
            
        Returns:
            bool: 유효한 JPEG 이미지인지 여부
        """
        if not frame or len(frame) < 4:
            return False
            
        # JPEG 시작 마커 (SOI) 확인
        has_soi = frame[0] == 0xFF and frame[1] == 0xD8
        
        # JPEG 종료 마커 (EOI) 확인
        has_eoi = frame[-2] == 0xFF and frame[-1] == 0xD9
        
        return has_soi and has_eoi

    def get_frame_size(self):
        """
        현재 설정된 프레임 크기 반환
        
        Returns:
            str: 프레임 크기 이름
        """
        return self.frame_size

    def get_quality(self):
        """
        현재 설정된 이미지 품질 반환
        
        Returns:
            int: 이미지 품질 (1-85)
        """
        return self.quality


# 파일이 직접 실행될 때 수행되는 메인 코드
if __name__ == "__main__":
    print("=" * 50)
    print("카메라 모듈 테스트")
    print("=" * 50)
    
    # 테스트할 해상도 목록
    resolutions = ["QQVGA", "QVGA", "VGA"]  # 저해상도부터 시작
    
    try:
        # 카메라 모듈 인스턴스 생성 (디버그 로그 레벨 설정)
        logger.set_level(logger.DEBUG)  # 테스트를 위해 DEBUG 레벨로 설정
        camera = CameraModule()
        
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
        import sys
        sys.print_exception(e)
        print("\n테스트 중 오류 발생!")
    finally:
        # 카메라 리소스 정리
        try:
            if 'camera' in locals() and camera is not None:
                camera.deinit()
        except:
            pass 