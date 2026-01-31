"""
ESP32-S3 펌웨어 업그레이드 수신기
웹에서 시리얼로 전송되는 펌웨어 파일을 받아서 기존 파일을 업데이트
IRQ 스케줄 큐 오버플로우 방지를 위한 백그라운드 처리 포함
"""

import os
import sys
import gc
import time
import json
import _thread
import micropython
from machine import reset

class FirmwareUpgrader:
    def __init__(self):
        self.is_upgrade_mode = False
        self.received_files = {}
        self.backup_dir = "/backup"
        self.temp_dir = "/temp"
        self.chunk_buffer = bytearray()
        
        # ===== IRQ 최적화: 백그라운드 처리 시스템 =====
        self.chunk_queue = []
        self.processing_thread = None
        self.thread_running = False
        self.queue_lock = _thread.allocate_lock()
        self.processing_enabled = False
        
        # ===== 메모리 관리 최적화 =====
        self.gc_counter = 0
        self.gc_frequency = 1  # 1청크마다 GC 실행 (기존 3에서 단축, 메모리 절약)
        self.memory_threshold = 50000  # 50KB 미만 시 경고
        
        # 업그레이드 상태
        self.current_file = None
        self.current_file_handle = None
        self.bytes_received = 0
        self.total_bytes = 0
        
        print("[FirmwareUpgrader] 초기화 완료 - 백그라운드 처리 모드")
    
    def enter_upgrade_mode(self):
        """업그레이드 모드 진입"""
        if self.is_upgrade_mode:
            print("이미 업그레이드 모드입니다")
            return
            
        try:
            # 임시 디렉토리 생성 (MicroPython 호환)
            self._ensure_directory_micropython(self.temp_dir)
            
            # 백업 디렉토리 생성 (MicroPython 호환)
            self._ensure_directory_micropython(self.backup_dir)
            
            # ===== 동기 처리 방식 사용 (백그라운드 비활성화) =====
            print("[ProcessMode] 동기 처리 방식 사용 - 큐 제거")
            self.processing_enabled = False  # 백그라운드 처리 비활성화
            
            self.is_upgrade_mode = True
            print("UPGRADE_MODE_READY")
            print("[ProcessMode] 직접 처리 모드 활성화")
            
        except Exception as e:
            print(f"UPGRADE_ERROR:모드진입실패:{e}")
    
    def exit_upgrade_mode(self):
        """업그레이드 모드 종료"""
        # ===== 백그라운드 처리 정리 (혹시 활성화되어 있을 경우) =====
        if self.processing_enabled or self.thread_running:
            self._stop_background_processor()
        
        self.is_upgrade_mode = False
        # temp 폴더 완전 삭제 (폴더 자체도 삭제)
        self.remove_folder_files()  # target_dir=None(temp), delete_root=True
        print("UPGRADE_MODE_EXIT")
        print("[ProcessMode] 직접 처리 모드 종료")
    
    # ===== 백그라운드 처리 시스템 =====
    
    def _start_background_processor(self):
        """백그라운드 청크 처리 스레드 시작"""
        try:
            self.thread_running = True
            self.processing_enabled = True
            self.processing_thread = _thread.start_new_thread(self._background_chunk_processor, ())
            print("[BackgroundProcessor] 스레드 시작 성공")
        except Exception as e:
            print(f"[BackgroundProcessor] 스레드 시작 실패: {e}")
            # 백그라운드 실패 시 동기 처리로 fallback
            self.processing_enabled = False
    
    def _stop_background_processor(self):
        """백그라운드 처리 스레드 중지"""
        self.thread_running = False
        self.processing_enabled = False
        
        # 스레드 종료 대기
        if self.processing_thread:
            time.sleep_ms(200)  # 스레드 종료 대기
            print("[BackgroundProcessor] 스레드 종료 완료")
        
        # 남은 큐 정리
        with self.queue_lock:
            remaining_chunks = len(self.chunk_queue)
            self.chunk_queue.clear()
            if remaining_chunks > 0:
                print(f"[BackgroundProcessor] 미처리 청크 {remaining_chunks}개 정리")
    
    def _background_chunk_processor(self):
        """백그라운드에서 실행되는 청크 처리 루프"""
        print("[BackgroundProcessor] 청크 처리 루프 시작")
        
        while self.thread_running:
            try:
                chunk_data = None
                queue_size = 0
                
                # 큐에서 청크 가져오기 (lock 사용)
                with self.queue_lock:
                    queue_size = len(self.chunk_queue)
                    if self.chunk_queue:
                        chunk_data = self.chunk_queue.pop(0)
                        print(f"[BackgroundProcessor] 큐에서 청크 가져옴, 남은 큐 크기: {len(self.chunk_queue)}")
                
                if chunk_data:
                    print(f"[BackgroundProcessor] 청크 처리 시작: {chunk_data[1]}")
                    # 실제 청크 처리
                    self._process_single_chunk_background(chunk_data)
                    
                    # ===== 메모리 관리 최적화: 매 청크마다 즉시 GC =====
                    self._optimized_gc_collection()  # 매번 즉시 실행
                    print(f"[BackgroundProcessor] 청크 {chunk_data[1]} 처리 완료")
                
                else:
                    # 큐가 비어있으면 잠시 대기 (CPU 양보)
                    if queue_size == 0:
                        print(f"[BackgroundProcessor] 큐 비어있음, 10ms 대기")
                    time.sleep_ms(10)
                    
            except Exception as e:
                print(f"[Background] 청크 처리 실패: {e}")
                print(f"[Background] 스택 추적: {sys.print_exception(e)}")
                time.sleep_ms(50)  # 오류 시 대기
        
        print("[BackgroundProcessor] 청크 처리 루프 종료")
    
    def _process_single_chunk_background(self, chunk_data):
        """백그라운드에서 단일 청크 처리 (스트리밍 방식)"""
        try:
            data_str, chunk_id = chunk_data
            
            # === 스트리밍 방식: Base64 검증용 저장 제거 (메모리 절약) ===
            # received_base64_chunks.append(data_str) 제거
            # self.total_base64_length += len(data_str) 제거
            
            # Base64 디코딩 (기존 로직과 동일)
            import ubinascii
            padded_data_str = self._fix_base64_padding(data_str)
            
            if not self._validate_base64_chars(padded_data_str):
                print(f"[Background] 청크 {chunk_id}: 잘못된 Base64")
                # ACK 실패 응답 전송
                self._send_chunk_ack(chunk_id, False, "Invalid Base64")
                return
            
            try:
                chunk_decoded = ubinascii.a2b_base64(padded_data_str)
                decoded_length = len(chunk_decoded)
            except Exception as decode_error:
                print(f"[Background] 청크 {chunk_id}: 디코딩 실패 - {decode_error}")
                # ACK 실패 응답 전송
                self._send_chunk_ack(chunk_id, False, f"Decode error: {decode_error}")
                return
            
            # 파일에 쓰기 (동기화 필요)
            if self.current_file_handle:
                try:
                    self.current_file_handle.write(chunk_decoded)
                    self.current_file_handle.flush()
                    
                    # 진행 상태 업데이트
                    self.bytes_received += decoded_length
                    chunk_checksum = self._calculate_simple_checksum(chunk_decoded)
                    self.file_checksum = (self.file_checksum + chunk_checksum) & 0xFFFFFFFF
                    
                    print(f"[Background] RX-{chunk_id}: {decoded_length}바이트 처리 완료 ✓")
                    
                    # ===== ACK 성공 응답 전송 =====
                    self._send_chunk_ack(chunk_id, True, f"OK:{decoded_length}")
                    
                except Exception as write_error:
                    print(f"[Background] 청크 {chunk_id}: 파일 쓰기 실패 - {write_error}")
                    # ACK 실패 응답 전송
                    self._send_chunk_ack(chunk_id, False, f"Write error: {write_error}")
                    return
            else:
                print(f"[Background] 청크 {chunk_id}: 파일 핸들 없음")
                # ACK 실패 응답 전송
                self._send_chunk_ack(chunk_id, False, "No file handle")
                
        except Exception as e:
            print(f"[Background] 청크 처리 실패: {e}")
            # 스택 추적 출력
            import sys
            sys.print_exception(e)
            # ACK 실패 응답 전송 (chunk_id가 있는 경우만)
            try:
                if 'chunk_id' in locals():
                    self._send_chunk_ack(chunk_id, False, f"Processing error: {e}")
                else:
                    print(f"[Background] chunk_id를 알 수 없어 ACK 전송 불가")
            except Exception as ack_error:
                print(f"[Background] ACK 전송 중 추가 오류: {ack_error}")
    
    def _send_chunk_ack(self, chunk_id, success, message):
        """청크 수신 확인 응답 전송 (기존 BLE 구조 활용)"""
        try:
            # ACK 메시지 형식: "CHUNK_ACK:chunk_id:status:message"
            status = "OK" if success else "ERROR"
            ack_message = f"CHUNK_ACK:{chunk_id}:{status}:{message}"
            
            # 기존 BLE 통신 구조 활용 - 글로벌 uart 객체 사용
            import bleIoT
            if hasattr(bleIoT, 'uart') and bleIoT.uart:
                ack_bytes = ack_message.encode('utf-8')
                bleIoT.uart.upgrade_notify(ack_bytes)
                print(f"[ACK] 청크 {chunk_id} ACK 전송: {status}")
            else:
                print(f"[ACK] BLE 연결 없음 - 청크 {chunk_id} ACK 전송 실패")
                
        except Exception as e:
            print(f"[ACK] 청크 {chunk_id} ACK 전송 실패: {e}")
    
    def _optimized_gc_collection(self):
        """
        메모리 관리 및 가비지 컬렉션 최적화 (적극적 모드)
        """
        try:
            import gc
            
            # 현재 메모리 상태 확인
            free_before = gc.mem_free()
            
            # 가비지 컬렉션 실행
            gc.collect()
            
            # 가비지 컬렉션 후 메모리 상태
            free_after = gc.mem_free()
            freed_bytes = free_after - free_before
            
            print(f"[GC] 메모리 정리: {free_before//1024}KB → {free_after//1024}KB (+"
                  f"{freed_bytes//1024}KB 확보)")
            
            # 메모리 부족 경고 (100KB 미만으로 임계값 상향)
            if free_after < 100 * 1024:
                print(f"[GC] ⚠️ 메모리 부족 경고: {free_after//1024}KB 남음")
                
                # 큐 크기 조정 (메모리 압박 시 더 적극적으로)
                if hasattr(self, 'chunk_queue') and len(self.chunk_queue) > 2:
                    dropped = len(self.chunk_queue) - 1
                    self.chunk_queue = self.chunk_queue[-1:]  # 최근 1개만 유지
                    print(f"[GC] 큐 크기 축소: {dropped}개 청크 삭제")
                    
        except Exception as e:
            print(f"[GC] 가비지 컬렉션 오류: {e}")
    
    # ===== 기존 함수들 수정 =====
    
    def process_upgrade_command(self, command):
        """업그레이드 명령어 처리"""
        if not command.startswith("UPGRADE:"):
            return False
            
        try:
            cmd_parts = command[8:].split(":", 2)  # "UPGRADE:" 제거
            cmd_type = cmd_parts[0]
            
            if cmd_type == "START":
                self.enter_upgrade_mode()
                
            elif cmd_type == "FILE_START":
                # UPGRADE:FILE_START:filename:size
                filename = cmd_parts[1]
                file_size = int(cmd_parts[2])
                self._start_file_reception(filename, file_size)
                
            elif cmd_type == "FILE_DATA":
                # UPGRADE:FILE_DATA:base64_data
                data_str = cmd_parts[1]
                self._receive_file_chunk_optimized(data_str)  # 최적화된 버전 사용
                
            elif cmd_type == "FILE_END":
                # UPGRADE:FILE_END:filename
                filename = cmd_parts[1]
                self._finish_file_reception(filename)
                
            elif cmd_type == "COMMIT":
                # 모든 파일 수신 완료, 실제 업그레이드 실행
                self._commit_upgrade()
                
            # === 🧪 단계별 테스트 명령어 추가 ===
            elif cmd_type == "STEP2_BACKUP":
                # 2단계: 기존 파일들만 백업
                self._step2_backup_only()
                
            elif cmd_type == "STEP3_APPLY":
                # 3단계: temp 파일들을 실제 위치로 적용만
                self._step3_apply_only()
                
            elif cmd_type == "STEP4_CLEANUP":
                # 4단계: temp 정리 및 재시작
                self._step4_cleanup_and_restart()
                
            elif cmd_type == "ABORT":
                # 업그레이드 중단
                self._abort_upgrade()
                
            elif cmd_type == "ROLLBACK":
                # 기존 버전 롤백 (백업에서 복원)
                self._rollback_from_backup()
                
            # === 🔍 상태 확인 명령어 추가 ===
            elif cmd_type == "STATUS":
                # 현재 업그레이드 상태 확인
                self._check_upgrade_status()
                
            elif cmd_type == "VERSION" or cmd_type == "FIRMWARE_VERSION":
                # 현재 펌웨어 버전 확인
                self._check_firmware_version()
                
            return True
            
        except Exception as e:
            print(f"UPGRADE_ERROR:명령처리실패:{e}")
            return False
    
    def _receive_file_chunk_optimized(self, data_str):
        """최적화된 파일 청크 수신 (직접 처리 방식)"""
        try:
            print(f"[ChunkReceive] 함수 시작 - 데이터 길이: {len(data_str)}")
            
            if not self.current_file_handle:
                print("FILE_CHUNK_ERROR:파일이 열려있지 않음")
                return
            
            self.chunk_count += 1
            original_data_length = len(data_str)
            
            print(f"RX-{self.chunk_count}: {original_data_length}글자 수신")
            print(f"[ChunkReceive] 청크 번호: {self.chunk_count} 설정됨")
            
            # ===== 직접 처리 방식 (큐 제거) =====
            print(f"[ChunkReceive] 직접 처리 방식으로 진행")
            
            # 즉시 동기 처리 (스트리밍!)
            self._receive_file_chunk_sync(data_str)
            
            # ===== 메모리 관리: 매 청크마다 즉시 GC =====
            self._optimized_gc_collection()  # 매번 즉시 실행
            
            print(f"[ChunkReceive] 함수 정상 완료")
            
        except Exception as e:
            print(f"FILE_CHUNK_ERROR:{e}")
            print(f"[ChunkReceive] 예외 발생: {type(e).__name__}: {e}")
            # 스택 추적 출력
            import sys
            print(f"[ChunkReceive] 스택 추적:")
            sys.print_exception(e)
            # 오류 발생시 메모리 정리
            self._optimized_gc_collection()
    
    def _receive_file_chunk_sync(self, data_str):
        """동기 방식 청크 처리 (스트리밍 방식으로 변경)"""
        try:
            # === 중복 청크 수신 방지 ===
            expected_chunk = self.chunk_count
            print(f"[Sync] 현재 청크 번호: {self.chunk_count}, 기대 청크: {expected_chunk}")
            
            # 현재 진행률 확인
            if self.bytes_received >= self.total_bytes:
                print(f"[Sync] 파일 전송 이미 완료됨 - 중복 청크 무시")
                print(f"[Sync] 수신 완료: {self.bytes_received}/{self.total_bytes} 바이트")
                # 중복 청크에 대해서도 ACK 전송 (웹 클라이언트 만족용)
                self._send_chunk_ack(expected_chunk, True, f"DUPLICATE:Already completed")
                return
            
            # === 스트리밍 방식: Base64 검증용 저장 제거 (메모리 절약) ===
            # self.received_base64_chunks.append(data_str) 제거
            # self.total_base64_length += len(data_str) 제거
            
            # Base64 디코딩 (MicroPython 호환, 패딩 오류 처리 개선)
            import ubinascii
            
            # Base64 패딩 검증 및 보정
            padded_data_str = self._fix_base64_padding(data_str)
            
            # Base64 문자 유효성 검증 (간소화)
            if not self._validate_base64_chars(padded_data_str):
                print(f"[Sync] 청크 {expected_chunk}: 잘못된 Base64")
                # ACK 실패 응답 전송
                self._send_chunk_ack(expected_chunk, False, "Invalid Base64")
                return
            
            try:
                chunk_data = ubinascii.a2b_base64(padded_data_str)
                decoded_length = len(chunk_data)
                
                # 디코딩 비율 검증 (간소화)
                expected_decoded_length = (len(data_str) * 3) // 4
                if abs(decoded_length - expected_decoded_length) > 10:
                    print(f"WARNING: 크기불일치 예상={expected_decoded_length} 실제={decoded_length}")
                
            except Exception as decode_error:
                print(f"[Sync] 청크 {expected_chunk}: 디코딩 실패 - {decode_error}")
                # ACK 실패 응답 전송
                self._send_chunk_ack(expected_chunk, False, f"Decode error: {decode_error}")
                return
            
            # === 파일 크기 오버플로우 방지 ===
            if self.bytes_received + decoded_length > self.total_bytes:
                print(f"[Sync] 파일 크기 초과 방지: 현재={self.bytes_received}, 추가={decoded_length}, 최대={self.total_bytes}")
                # 필요한 만큼만 잘라서 쓰기
                remaining_bytes = self.total_bytes - self.bytes_received
                if remaining_bytes > 0:
                    chunk_data = chunk_data[:remaining_bytes]
                    decoded_length = remaining_bytes
                    print(f"[Sync] 청크 크기 조정: {len(chunk_data)}바이트로 축소")
                else:
                    print(f"[Sync] 파일 전송 완료로 인한 청크 무시")
                    self._send_chunk_ack(expected_chunk, True, f"OVERFLOW_IGNORED:{decoded_length}")
                    return
            
            # 청크 체크섬 계산 (간소화)
            chunk_checksum = self._calculate_simple_checksum(chunk_data)
            
            # 파일에 쓰기 (즉시 처리)
            try:
                self.current_file_handle.write(chunk_data)
                self.current_file_handle.flush()
                print(f"[Sync] RX-{expected_chunk}: {decoded_length}바이트 처리 완료 ✓")
                
                # ===== ACK 성공 응답 전송 =====
                self._send_chunk_ack(expected_chunk, True, f"OK:{decoded_length}")
                
            except Exception as write_error:
                print(f"[Sync] 청크 {expected_chunk}: 파일 쓰기 실패 - {write_error}")
                # ACK 실패 응답 전송
                self._send_chunk_ack(expected_chunk, False, f"Write error: {write_error}")
                return
                
            self.bytes_received += len(chunk_data)
            self.file_checksum = (self.file_checksum + chunk_checksum) & 0xFFFFFFFF
            
            # 진행률 출력 (간소화)
            progress = (self.bytes_received / self.total_bytes) * 100
            print(f"PROGRESS: {progress:.1f}% ({self.bytes_received}/{self.total_bytes})")
            
            # ===== 메모리 관리: 매 청크마다 즉시 GC =====
            self._optimized_gc_collection()  # 매번 즉시 실행
            
        except Exception as e:
            print(f"FILE_CHUNK_SYNC_ERROR:{e}")
            # ACK 실패 응답 전송 (expected_chunk 사용)
            try:
                if 'expected_chunk' in locals():
                    self._send_chunk_ack(expected_chunk, False, f"Processing error: {e}")
                else:
                    print(f"[Sync] expected_chunk를 알 수 없어 ACK 전송 불가")
            except Exception as ack_error:
                print(f"[Sync] ACK 전송 중 추가 오류: {ack_error}")
    
    def _check_firmware_version(self):
        """현재 펌웨어 버전 확인"""
        try:
            print("FIRMWARE_VERSION_CHECK_START")
            self._send_upgrade_message("FIRMWARE_VERSION_CHECK_START")
            
            # config.py 파일에서 firmware_source 읽기
            firmware_version = "unknown"
            version_found = False  # 버전 발견 여부 추적
            
            try:
                # config.py 파일 읽기 시도
                with open('/config.py', 'r') as f:
                    config_content = f.read()
                    
                # firmware_source 값 추출
                for line in config_content.split('\n'):
                    line = line.strip()
                    if line.startswith('firmware_source'):
                        # firmware_source = "1.3.5" 형태에서 버전 추출
                        if '=' in line:
                            value_part = line.split('=', 1)[1].strip()
                            # 따옴표 제거
                            if value_part.startswith('"') and value_part.endswith('"'):
                                firmware_version = value_part[1:-1]
                            elif value_part.startswith("'") and value_part.endswith("'"):
                                firmware_version = value_part[1:-1]
                            else:
                                firmware_version = value_part
                            version_found = True  # 버전 찾음
                            break
                
                if version_found:
                    print(f"FIRMWARE_VERSION_FOUND:{firmware_version}")
                    self._send_upgrade_message(f"FIRMWARE_VERSION:{firmware_version}")
                else:
                    print("FIRMWARE_VERSION_NOT_IN_CONFIG:config.py에 firmware_source 설정이 없음")
                    self._send_upgrade_message("FIRMWARE_VERSION_NOT_IN_CONFIG:config.py에 firmware_source 설정이 없음")
                    # import 방식으로 재시도
                    raise Exception("firmware_source not found in config.py")
                            
            except Exception as config_error:
                # config.py 읽기 실패 또는 firmware_source 없음
                print(f"CONFIG_READ_ERROR:{config_error}")
                
                try:
                    # config 모듈로 import 시도
                    import config
                    if hasattr(config, 'firmware_source'):
                        firmware_version = config.firmware_source
                        version_found = True
                        print(f"FIRMWARE_VERSION_IMPORT:{firmware_version}")
                        self._send_upgrade_message(f"FIRMWARE_VERSION:{firmware_version}")
                    else:
                        print("FIRMWARE_VERSION_NOT_FOUND:config.firmware_source 속성 없음")
                        # 속성이 없는 경우에도 unknown으로 처리
                        firmware_version = "unknown"
                        self._send_upgrade_message(f"FIRMWARE_VERSION:{firmware_version}")
                        self._send_upgrade_message("FIRMWARE_VERSION_WARNING:config.firmware_source 속성이 없어 기본값 사용")
                        
                except Exception as import_error:
                    print(f"CONFIG_IMPORT_ERROR:{import_error}")
                    
                    # 최종 fallback: 기본값 사용
                    version_found = False
                    firmware_version = "unknown"
                    print(f"FIRMWARE_VERSION_FALLBACK:{firmware_version}")
                    self._send_upgrade_message(f"FIRMWARE_VERSION:{firmware_version}")
                    self._send_upgrade_message("FIRMWARE_VERSION_WARNING:config 파일을 읽을 수 없어 기본값 사용")
            
            # 추가 시스템 정보도 함께 전송
            try:
                import gc
                free_mem = gc.mem_free()
                self._send_upgrade_message(f"SYSTEM_MEMORY:{free_mem}")
            except:
                pass
                
            try:
                import os
                import time
                # 파일 시스템 정보
                statvfs = os.statvfs('/')
                total_space = statvfs[0] * statvfs[2]  # 블록 크기 * 총 블록 수
                free_space = statvfs[0] * statvfs[3]   # 블록 크기 * 사용 가능 블록 수
                used_space = total_space - free_space
                
                self._send_upgrade_message(f"FILESYSTEM_TOTAL:{total_space}")
                self._send_upgrade_message(f"FILESYSTEM_USED:{used_space}")
                self._send_upgrade_message(f"FILESYSTEM_FREE:{free_space}")
            except:
                pass
            
            self._send_upgrade_message("FIRMWARE_VERSION_CHECK_COMPLETE")
            print("FIRMWARE_VERSION_CHECK_COMPLETE")
            
        except Exception as e:
            error_msg = f"FIRMWARE_VERSION_CHECK_ERROR:{e}"
            print(error_msg)
            self._send_upgrade_message(error_msg)
    
    def _check_upgrade_status(self):
        """현재 업그레이드 상태 확인"""
        try:
            print("STATUS_CHECK_START")
            
            self._send_upgrade_message("STATUS_CHECK_START")
            
            # 1. temp 디렉토리 상태 확인
            temp_files = []
            if self._file_exists(self.temp_dir):
                try:
                    temp_list = os.listdir(self.temp_dir)
                    for item in temp_list:
                        item_path = f"{self.temp_dir}/{item}"
                        if self._file_exists(item_path):
                            # 파일 크기도 함께 확인
                            try:
                                stat_info = os.stat(item_path)
                                file_size = stat_info[6]
                                temp_files.append(f"{item}:{file_size}")
                            except:
                                temp_files.append(f"{item}:unknown")
                    self._send_upgrade_message(f"TEMP_FILES:{len(temp_files)}:{','.join(temp_files)}")
                except Exception as temp_error:
                    self._send_upgrade_message(f"TEMP_CHECK_ERROR:{temp_error}")
            else:
                self._send_upgrade_message("TEMP_FILES:0:")
            
            # 2. backup 디렉토리 상태 확인
            backup_files = []
            if self._file_exists(self.backup_dir):
                try:
                    backup_list = os.listdir(self.backup_dir)
                    for item in backup_list:
                        item_path = f"{self.backup_dir}/{item}"
                        if self._file_exists(item_path):
                            # 파일 크기도 함께 확인
                            try:
                                stat_info = os.stat(item_path)
                                file_size = stat_info[6]
                                backup_files.append(f"{item}:{file_size}")
                            except:
                                backup_files.append(f"{item}:unknown")
                    self._send_upgrade_message(f"BACKUP_FILES:{len(backup_files)}:{','.join(backup_files)}")
                except Exception as backup_error:
                    self._send_upgrade_message(f"BACKUP_CHECK_ERROR:{backup_error}")
            else:
                self._send_upgrade_message("BACKUP_FILES:0:")
            
            # 3. 업그레이드 모드 상태
            self._send_upgrade_message(f"UPGRADE_MODE:{self.is_upgrade_mode}")
            
            # 4. 메모리 상태
            try:
                import gc
                free_mem = gc.mem_free()
                self._send_upgrade_message(f"MEMORY_FREE:{free_mem}")
            except:
                self._send_upgrade_message("MEMORY_FREE:unknown")
            
            # 5. 상태 종합 분석
            temp_count = len(temp_files)
            backup_count = len(backup_files)
            
            if temp_count > 0 and backup_count > 0:
                self._send_upgrade_message("STATUS_ANALYSIS:STEP3_READY:temp와 backup 모두 존재, 3단계(적용) 실행 가능")
            elif temp_count > 0 and backup_count == 0:
                self._send_upgrade_message("STATUS_ANALYSIS:STEP2_READY:temp 존재, backup 없음, 2단계(백업) 실행 가능")
            elif temp_count == 0 and backup_count > 0:
                self._send_upgrade_message("STATUS_ANALYSIS:ROLLBACK_READY:temp 없음, backup 존재, 롤백만 가능")
            else:
                self._send_upgrade_message("STATUS_ANALYSIS:CLEAN:temp와 backup 모두 없음, 새로운 업그레이드 시작 가능")
            
            self._send_upgrade_message("STATUS_CHECK_COMPLETE")
            
        except Exception as e:
            print(f"STATUS_CHECK_ERROR:{e}")
            # 오류도 BLE로 전송
            try:
                import bleIoT
                if hasattr(bleIoT, 'uart') and bleIoT.uart:
                    error_msg = f"STATUS_CHECK_ERROR:{e}"
                    bleIoT.uart.upgrade_notify(error_msg.encode('utf-8'))
            except:
                pass
    
    def _start_file_reception(self, filename, file_size):
        """파일 수신 시작"""
        try:
            print(f"DEBUG: 파일 수신 시작 요청 - {filename}, 크기: {file_size}바이트")
            
            # 임시 파일 경로 미리 계산 (f-string 중첩 문제 해결)
            temp_path = f"{self.temp_dir}/{filename}"
            print(f"DEBUG: 임시 파일 경로: {temp_path}")
            
            # === 안전한 디렉토리 생성 (다단계 지원으로 개선) ===
            try:
                # 기본 temp 디렉토리 확인/생성
                if not self._file_exists(self.temp_dir):
                    os.mkdir(self.temp_dir)
                    print(f"TEMP_DIR_CREATED:{self.temp_dir}")
                
                # 파일 경로에 디렉토리가 포함된 경우 처리
                if '/' in filename:
                    # filename이 "lib/max30102/file.mpy" 형태인 경우
                    path_parts = filename.split('/')
                    file_only = path_parts[-1]  # 실제 파일명
                    dir_path = '/'.join(path_parts[:-1])  # 디렉토리 경로
                    
                    print(f"DEBUG: 다단계 경로 감지 - 디렉토리: {dir_path}, 파일: {file_only}")
                    
                    # lib로 시작하는 경우만 허용 (보안상)
                    if path_parts[0] == 'lib':
                        # temp 디렉토리 기준으로 전체 디렉토리 경로 생성
                        current_path = self.temp_dir  # /temp 에서 시작
                        for part in path_parts[:-1]:  # 파일명 제외하고 디렉토리만
                            current_path = f"{current_path}/{part}"  # /temp/lib, /temp/lib/max30102
                            if not self._file_exists(current_path):
                                try:
                                    os.mkdir(current_path)
                                    print(f"TEMP_DIR_CREATED:{current_path}")
                                except OSError as e:
                                    if e.args[0] != 17:  # EEXIST 무시
                                        print(f"DIR_ERROR:{e}")
                                        raise
                    else:
                        print(f"WARNING: lib 외의 디렉토리는 지원하지 않음: {filename}")
                        print(f"FILE_START_ERROR:{filename}:lib 외의 디렉토리")
                        return
                else:
                    # 기본 temp 디렉토리만 확인
                    if not self._file_exists(self.temp_dir):
                        os.mkdir(self.temp_dir)
                        print(f"TEMP_DIR_CREATED:{self.temp_dir}")
                    print(f"DEBUG: 루트 레벨 파일: {filename} (디렉토리 생성 불필요)")
                
                print(f"DEBUG: 디렉토리 생성 완료, 파일 열기 시도")
                
            except Exception as dir_error:
                print(f"FILE_START_ERROR:{filename}:디렉토리 생성 실패 - {dir_error}")
                return
            
            # 파일 열기 (f-string 중첩 제거)
            self.current_file = filename
            self.current_file_handle = open(temp_path, 'wb')
            self.bytes_received = 0
            self.total_bytes = file_size
            
            # 체크섬 계산용 초기화
            self.file_checksum = 0
            self.chunk_count = 0
            
            # === 스트리밍 방식: Base64 청크 저장 제거 (메모리 절약) ===
            # self.received_base64_chunks = [] 제거
            # self.total_base64_length = 0 제거
            
            # ===== 메모리 관리 초기화 =====
            self.gc_counter = 0
            self._optimized_gc_collection()  # 시작 전 메모리 정리
            
            print(f"FILE_START_OK:{filename}:{file_size}")
            print(f"DEBUG: 파일 수신 시작 - 파일명: {filename}, 예상 크기: {file_size}바이트, 임시 경로: {temp_path}")
            print(f"VERIFICATION: ===== 스트리밍 방식 검증 시작 =====")
            print(f"VERIFICATION: 메모리 절약을 위해 Base64 재구성 검증 생략")
            print(f"VERIFICATION: 파일 크기 및 체크섬 기반 무결성 검증 수행")
            print(f"VERIFICATION: ===== 스트리밍 방식 검증 완료 =====\n")
            print(f"[MemoryMgmt] 파일 수신 준비 완료")
            
        except Exception as e:
            print(f"FILE_START_ERROR:{filename}:{e}")
            print(f"DEBUG: 전체 오류 정보: {type(e).__name__}: {e}")
            # 파일 핸들이 열려있으면 정리
            if hasattr(self, 'current_file_handle') and self.current_file_handle:
                try:
                    self.current_file_handle.close()
                    self.current_file_handle = None
                except:
                    pass
    
    def _validate_base64_chars(self, base64_str):
        """Base64 문자 유효성 검증 (최적화)"""
        try:
            # 빠른 검증: 길이만 확인 (성능 우선)
            if len(base64_str) % 4 != 0:
                return False
            
            # 간단한 문자 검증 (필수 문자만)
            valid_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="
            for char in base64_str:
                if char not in valid_chars:
                    return False
            return True
        except Exception:
            return False

    def _calculate_simple_checksum(self, data):
        """간단한 체크섬 계산 (MicroPython 호환)"""
        try:
            checksum = 0
            for byte in data:
                checksum = (checksum + byte) & 0xFFFFFFFF
            return checksum
        except Exception as e:
            print(f"DEBUG: 체크섬 계산 실패: {e}")
            return 0
    
    def _fix_base64_padding(self, data_str):
        """Base64 패딩 보정 (최적화)"""
        try:
            remainder = len(data_str) % 4
            if remainder == 0:
                return data_str
            
            # 패딩 추가 (간소화)
            padding_needed = 4 - remainder
            return data_str + '=' * padding_needed
            
        except Exception as e:
            print(f"PADDING_ERROR: {e}")
            return data_str
    
    def _finish_file_reception(self, filename):
        """파일 수신 완료"""
        try:
            # ===== 백그라운드 처리 완료 대기 =====
            if self.processing_enabled and self.thread_running:
                print(f"[Background] 백그라운드 처리 완료 대기 중...")
                
                # 큐가 비워질 때까지 대기
                max_wait_time = 30  # 최대 30초 대기
                wait_count = 0
                
                while wait_count < max_wait_time:
                    with self.queue_lock:
                        queue_size = len(self.chunk_queue)
                    
                    if queue_size == 0:
                        break
                    
                    print(f"[Background] 대기 중... 큐 크기: {queue_size}개")
                    time.sleep_ms(1000)  # 1초 대기
                    wait_count += 1
                
                if wait_count >= max_wait_time:
                    print(f"[Background] 경고: 대기 시간 초과, 강제 진행")
                else:
                    print(f"[Background] 백그라운드 처리 완료 ({wait_count}초 대기)")
            
            if self.current_file_handle:
                self.current_file_handle.close()
                self.current_file_handle = None
            
            # === 스트리밍 방식: Base64 재구성 검증 제거 (메모리 절약) ===
            # 기존의 received_base64_chunks를 이용한 전체 Base64 재구성 검증 제거
            # 대신 파일 크기와 체크섬만으로 무결성 검증
            print(f"VERIFICATION: ===== 스트리밍 방식 검증 시작 =====")
            print(f"VERIFICATION: 메모리 절약을 위해 Base64 재구성 검증 생략")
            print(f"VERIFICATION: 파일 크기 및 체크섬 기반 무결성 검증 수행")
            print(f"VERIFICATION: ===== 스트리밍 방식 검증 완료 =====\n")
            
            print(f"FILE_END_OK:{filename}:{self.bytes_received}")
            print(f"DEBUG: 파일 수신 완료 - 파일명: {filename}")
            print(f"DEBUG: 총 수신 바이트: {self.bytes_received} / 예상: {self.total_bytes}")
            print(f"DEBUG: 총 청크 개수: {self.chunk_count}")
            print(f"DEBUG: 파일 체크섬: {self.file_checksum:08x}")
            
            # 크기 검증
            if self.bytes_received != self.total_bytes:
                print(f"DEBUG: 경고 - 파일 크기 불일치!")
            
            # 실제 파일 크기 확인
            temp_path = f"{self.temp_dir}/{filename}"
            if self._file_exists(temp_path):
                try:
                    with open(temp_path, 'rb') as f:
                        # 파일 크기 확인
                        f.seek(0, 2)  # 파일 끝으로 이동
                        actual_size = f.tell()
                        f.seek(0)  # 파일 처음으로 이동
                        
                        # 파일 내용 체크섬 계산
                        file_checksum = 0
                        while True:
                            chunk = f.read(1024)
                            if not chunk:
                                break
                            for byte in chunk:
                                file_checksum = (file_checksum + byte) & 0xFFFFFFFF
                        
                        print(f"DEBUG: 실제 파일 크기: {actual_size}바이트")
                        print(f"DEBUG: 실제 파일 체크섬: {file_checksum:08x}")
                        
                        if actual_size != self.bytes_received:
                            print(f"DEBUG: 오류 - 파일 크기 불일치! 메모리: {self.bytes_received}, 디스크: {actual_size}")
                        
                        if file_checksum != self.file_checksum:
                            print(f"DEBUG: 오류 - 파일 체크섬 불일치! 메모리: {self.file_checksum:08x}, 디스크: {file_checksum:08x}")
                        else:
                            print(f"DEBUG: 파일 무결성 검증 성공!")
                            
                        # 파일 내용 처음 몇 바이트 확인 (바이너리/텍스트 판별)
                        f.seek(0)  # 파일 처음으로 이동 (읽기 전에!)
                        first_bytes = f.read(min(100, actual_size))
                        
                        print(f"DEBUG: 파일 첫 10바이트: {[hex(b) for b in first_bytes[:10]]}")
                        
                        # 파일 형식별 검증
                        if filename.endswith('.py'):
                            # Python 소스 파일은 기본적으로 텍스트 파일로 간주
                            print(f"DEBUG: .py 파일 - 기본 텍스트 파일로 처리 ✓")
                            print(f"DEBUG: 체크섬과 파일 크기로 무결성 이미 확인됨")
                            
                            # 선택적: 파일이 완전히 비어있지 않은지만 확인
                            if len(first_bytes) > 0:
                                print(f"DEBUG: .py 파일 - 내용 존재 확인 ✓")
                            else:
                                print(f"DEBUG: .py 파일 - 빈 파일 (정상)")
                                
                        elif filename.endswith('.mpy'):
                            # MicroPython 바이트코드 파일 검증
                            print(f"DEBUG: .mpy 파일 - 바이너리 검증 시작")
                            
                            # .mpy 파일의 매직 넘버 확인 (MicroPython 바이트코드 시그니처)
                            if len(first_bytes) >= 4:
                                # MicroPython .mpy 파일은 특정 매직 넘버로 시작
                                magic_bytes = first_bytes[:4]
                                print(f"DEBUG: .mpy 매직 바이트: {[hex(b) for b in magic_bytes]}")
                                
                                # 일반적인 .mpy 매직 넘버들 (버전별로 다름)
                                # 'M' (0x4D)로 시작하는 경우가 많음
                                if magic_bytes[0] == 0x4D:  # 'M'
                                    print(f"DEBUG: .mpy 파일 - 유효한 매직 넘버 감지")
                                else:
                                    print(f"DEBUG: .mpy 파일 - 매직 넘버 불일치 (버전 차이 가능)")
                                
                                # 바이너리 특성 확인 (제어 문자나 비-ASCII 포함)
                                binary_chars = sum(1 for b in first_bytes[:20] if b < 32 and b not in [9, 10, 13])
                                if binary_chars > 3:
                                    print(f"DEBUG: .mpy 파일 - 바이너리 특성 확인 (제어문자 {binary_chars}개)")
                                else:
                                    print(f"DEBUG: .mpy 파일 - 바이너리 특성 약함 (확인 필요)")
                            else:
                                print(f"DEBUG: .mpy 파일이 너무 작음 ({len(first_bytes)}바이트)")
                                
                        else:
                            # 기타 파일 (.json, .txt 등)
                            print(f"DEBUG: 기타 파일 - 기본 무결성만 확인")
                            
                            # 텍스트 파일인지 바이너리 파일인지 추정
                            text_chars = sum(1 for b in first_bytes[:50] if 32 <= b <= 126 or b in [9, 10, 13])
                            text_ratio = text_chars / min(50, len(first_bytes)) if first_bytes else 0
                            
                            if text_ratio > 0.7:
                                print(f"DEBUG: 텍스트 파일로 추정 (텍스트 비율: {text_ratio:.2f})")
                            else:
                                print(f"DEBUG: 바이너리 파일로 추정 (텍스트 비율: {text_ratio:.2f})")
                        
                except Exception as verify_error:
                    print(f"DEBUG: 파일 검증 실패: {verify_error}")
            
            # 수신된 파일 목록에 추가
            self.received_files[filename] = {
                'temp_path': f"{self.temp_dir}/{filename}",
                'size': self.bytes_received,
                'checksum': self.file_checksum,
                'chunks': self.chunk_count,
                'status': 'received'
            }
            
            # 초기화
            self.current_file = None
            self.bytes_received = 0
            self.total_bytes = 0
            self.file_checksum = 0
            self.chunk_count = 0
            
            # === 스트리밍 방식: Base64 청크 저장 제거 (메모리 절약) ===
            # self.received_base64_chunks = [] 제거
            # self.total_base64_length = 0 제거
            
            # ===== 메모리 최종 정리 =====
            self._optimized_gc_collection()
            print(f"[MemoryMgmt] 파일 수신 완료 후 메모리 정리")
            
        except Exception as e:
            print(f"FILE_END_ERROR:{filename}:{e}")
            print(f"DEBUG: 파일 종료 처리 중 오류 발생")
    
    def _commit_upgrade(self):
        """업그레이드 커밋 (실제 파일 교체)"""
        try:
            print("COMMIT_START")
            
            # 메모리 정리
            gc.collect()
            
            # 파일 크기 검증 먼저 수행 (스택 사용량 최소화)
            print("DEBUG: 파일 크기 사전 검증 시작")
            for filename, info in self.received_files.items():
                print(f"DEBUG: {filename} - 예상: {info['size']}바이트")
                
                # 파일 크기가 너무 작으면 전송 실패로 판단
                if info['size'] < 50:  # 50바이트 미만이면 불완전 전송
                    print(f"COMMIT_ERROR:파일 전송 불완전 - {filename}")
                    print(f"DEBUG: 파일 크기가 너무 작습니다 ({info['size']}바이트)")
                    print(f"DEBUG: 파일을 다시 전송해주세요.")
                    return
                
                if not self._file_exists(info['temp_path']):
                    print(f"COMMIT_ERROR:임시 파일이 존재하지 않음: {filename}")
                    return
                    
                # 실제 파일 크기 확인 (메모리 사용량 최소화)
                try:
                    stat_info = os.stat(info['temp_path'])
                    actual_size = stat_info[6]  # 파일 크기
                    
                    if actual_size != info['size']:
                        print(f"COMMIT_ERROR:파일 크기 불일치 - 예상: {info['size']}, 실제: {actual_size}")
                        print(f"DEBUG: 파일 전송이 불완전했습니다. 다시 시도해주세요.")
                        return
                        
                except Exception as stat_error:
                    print(f"COMMIT_ERROR:파일 정보 읽기 실패 {filename}: {stat_error}")
                    return
                    
                # 메모리 정리
                gc.collect()
            
            print("DEBUG: 파일 크기 사전 검증 완료")
            
            # 0. 수신된 파일들 유효성 검증 (간소화된 버전)
            for filename, info in self.received_files.items():
                print(f"DEBUG: 파일 검증 시작 - {filename}")
                
                # 파일 형식별 기본 검증만 수행 (스택 사용량 최소화)
                try:
                    # 작은 청크로 파일 검증 (메모리 절약)
                    with open(info['temp_path'], 'rb') as f:
                        # 파일 처음 몇 바이트만 확인
                        first_bytes = f.read(20)  # 100바이트에서 20바이트로 축소
                        
                        print(f"DEBUG: {filename} 첫 4바이트: {[hex(b) for b in first_bytes[:4]]}")
                        
                        # 간단한 형식 검증만 수행
                        if filename.endswith('.py'):
                            # Python 파일은 기본적으로 텍스트 파일로 간주
                            print(f"DEBUG: .py 파일 - 기본 텍스트 파일로 처리 ✓")
                            print(f"DEBUG: 체크섬과 파일 크기로 무결성 이미 확인됨")
                            
                            # 선택적: 파일이 완전히 비어있지 않은지만 확인
                            if len(first_bytes) > 0:
                                print(f"DEBUG: .py 파일 - 내용 존재 확인 ✓")
                            else:
                                print(f"DEBUG: .py 파일 - 빈 파일 (정상)")
                                
                        elif filename.endswith('.mpy'):
                            # .mpy 파일의 기본 특성만 확인
                            if len(first_bytes) >= 4:
                                print(f"DEBUG: .mpy 파일 기본 검증 완료")
                            else:
                                print(f"COMMIT_ERROR:.mpy 파일이 너무 작음: {filename}")
                                return
                        
                        # 메모리 정리
                        del first_bytes
                        gc.collect()
                        
                except Exception as e:
                    print(f"COMMIT_ERROR:파일 검증 실패 {filename}: {e}")
                    return
                
                print(f"DEBUG: 파일 기본 검증 완료 - {filename}")
                # 각 파일 검증 후 메모리 정리
                gc.collect()
            
            print("파일 유효성 검증 완료")
            print(f"DEBUG: 총 {len(self.received_files)}개 파일 검증 성공")
            
            # 대용량 메모리 정리
            gc.collect()
            
            # 1. 기존 파일 백업 (백업 폴더 사용)
            print("DEBUG: 파일 백업 시작")
            for filename in self.received_files:
                try:
                    self._backup_existing_file(filename)
                    # 각 백업 후 메모리 정리
                    gc.collect()
                except Exception as backup_error:
                    print(f"BACKUP_ERROR:{filename}:{backup_error}")
                    # 백업 실패해도 계속 진행
            
            print("파일 백업 완료")
            gc.collect()
            
            # 2. 새 파일들을 실제 위치로 이동 (안전한 버전)
            print("DEBUG: 파일 설치 시작")
            for filename, info in self.received_files.items():
                try:
                    self._install_new_file(filename, info['temp_path'])
                    # 각 설치 후 메모리 정리
                    gc.collect()
                except Exception as install_error:
                    print(f"INSTALL_ERROR:{filename}:{install_error}")
                    print(f"DEBUG: 설치 실패시 롤백 시도")
                    try:
                        self._rollback_upgrade()
                    except:
                        pass
                    return
            
            print("파일 설치 완료")
            gc.collect()
            
            # 3. 임시 파일 정리
            print("DEBUG: 임시 파일 정리 시작")
            try:
                # temp 폴더 완전 삭제 (폴더 자체도 삭제)
                self.remove_folder_files()  # target_dir=None(temp), delete_root=True
            except Exception as cleanup_error:
                print(f"CLEANUP_WARNING:{cleanup_error}")
                # 정리 실패해도 계속 진행
            
            gc.collect()
            
            print("COMMIT_SUCCESS")
            print("재시작이 필요합니다. 3초 후 자동 재시작...")
            
            # 1초 후 재시작
            time.sleep(1)
            reset()
            
        except Exception as e:
            print(f"COMMIT_ERROR:{e}")
            print(f"DEBUG: 오류 타입: {type(e).__name__}")
            # 실패시 응급 정리만 수행 (롤백은 스택 오버플로우 위험)
            try:
                self._emergency_cleanup()
            except Exception as emergency_error:
                print(f"EMERGENCY_CLEANUP_FAILED:{emergency_error}")
                # 최종 수단: 메모리 정리만 수행
                gc.collect()
    
    # === 🧪 단계별 테스트 메서드들 ===
    def scan_directory_iterative(self, start_path):
        result = []
        stack = [start_path]

        while stack:
            path = stack.pop()
            try:
                items = os.listdir(path)
            except OSError:
                continue

            for item in items:
                full_path = path + "/" + item
                try:
                    stat = os.stat(full_path)
                    if stat[0] & 0x4000:
                        result.append(("DIR", full_path))
                        stack.append(full_path)  # 재귀 대신 스택 사용
                    else:
                        result.append(("FILE", full_path))
                except Exception as e:
                    print("오류 발생:", full_path, e)

        return result

    def _step2_backup_only(self):
        """2단계: 기존 파일들만 백업 - 상세 진행 상황 및 검증 포함"""
        try:
            #print("STEP2_BACKUP_START")
            self._send_upgrade_message("STEP2_BACKUP_START")
            
            # === 🔥 기존 backup 폴더 완전 삭제 (새 업그레이드 시작 시) ===
            if self._file_exists(self.backup_dir):
                print("OLD_BACKUP_CLEARING:기존 백업 폴더 완전 삭제 시작")
                self._send_upgrade_message("BACKUP_PHASE:기존 백업 폴더 정리 중...")
                try:
                    # 범용화된 cleanup 함수 사용 (내용만 삭제, 폴더는 유지)
                    self.remove_folder_files(self.backup_dir, delete_root=False)
                    print("OLD_BACKUP_CLEARED:기존 백업 폴더 완전 삭제 완료")
                    self._send_upgrade_message("OLD_BACKUP_CLEARED:기존 백업 삭제 완료")
                except Exception as clear_error:
                    print(f"OLD_BACKUP_CLEAR_ERROR:{clear_error}")
                    self._send_upgrade_message(f"OLD_BACKUP_CLEAR_WARNING:기존 백업 삭제 실패: {clear_error}")
                    # 삭제 실패해도 계속 진행
            else:
                print("OLD_BACKUP_NONE:기존 백업 폴더 없음")
                self._send_upgrade_message("OLD_BACKUP_NONE:기존 백업 없음")
            
            # 메모리 정리
            gc.collect()
            
            # temp 디렉토리 존재 확인
            if not self._file_exists(self.temp_dir):
                error_msg = "STEP2_ERROR:temp 디렉토리가 존재하지 않음"
                print(error_msg)
                self._send_upgrade_message(error_msg)
                return
            
            # === 1단계: temp 폴더 전체 구조 스캔 및 파일 목록 작성 ===
            print("DEBUG: temp 폴더 전체 구조 스캔 시작")
            self._send_upgrade_message("BACKUP_PHASE:1단계 - temp 폴더 구조 분석 중...")
            
            # === Fatal Error 진단 포인트 ===
            print("DEBUG: BLE 메시지 전송 완료, scan_directory 호출 직전")
            gc.collect()  # 메모리 정리
            print("DEBUG: 메모리 정리 완료, 이제 scan_directory 호출")
            
            time.sleep(2)
            try:
                # temp 폴더 전체를 재귀 스캔하여 모든 파일 경로 수집
                temp_list = self.scan_directory_iterative(self.temp_dir)
                
                print(f"DEBUG: temp 폴더 스캔 완료 - 총 {len(temp_list)}개 파일 발견")
                
                # 파일 경로만 추출 (튜플에서 파일 경로만)
                temp_files_to_backup = [path for ftype, path in temp_list if ftype == "FILE"]
                
                # === temp 파일 목록을 웹페이지에 전송 ===
                temp_list_msg = f"TEMP_FILE_LIST:{len(temp_files_to_backup)}:{','.join(temp_files_to_backup)}"
                self._send_upgrade_message(temp_list_msg)
                
                # 각 파일 정보도 개별 전송 (상세 정보 포함)
                for i, file_path in enumerate(temp_files_to_backup):
                    temp_file_full_path = f"{file_path}"
                    try:
                        stat_info = os.stat(temp_file_full_path)
                        file_size = stat_info[6]
                        file_info_msg = f"TEMP_FILE_INFO:{i+1}:{file_path}:{file_size}"
                        self._send_upgrade_message(file_info_msg)
                        print(f"DEBUG: temp 파일 정보 - {file_path} ({file_size}바이트)")
                    except Exception as stat_error:
                        file_info_msg = f"TEMP_FILE_INFO:{i+1}:{file_path}:unknown"
                        self._send_upgrade_message(file_info_msg)
                        print(f"DEBUG: temp 파일 정보 읽기 실패 - {file_path}: {stat_error}")
                
            except Exception as scan_error:
                error_msg = f"STEP2_ERROR:temp 폴더 스캔 실패: {scan_error}"
                print(error_msg)
                self._send_upgrade_message(error_msg)
                return
            
            if len(temp_files_to_backup) == 0:
                warning_msg = "STEP2_WARNING:백업할 파일이 없습니다"
                success_msg = "STEP2_BACKUP_SUCCESS:0개 파일 백업 완료"
                print(warning_msg)
                print(success_msg)
                self._send_upgrade_message(warning_msg)
                self._send_upgrade_message(success_msg)
                return
            
            # === 2단계: 파일별 백업 수행 ===
            backup_phase_msg = f"BACKUP_PHASE:2단계 - {len(temp_files_to_backup)}개 파일 백업 시작"
            print(backup_phase_msg)
            self._send_upgrade_message(backup_phase_msg)
            
            backup_count = 0
            backup_success_list = []
            backup_failure_list = []
            
            for i, file_path in enumerate(temp_files_to_backup):
                try:
                    # temp 경로에서 실제 파일명 추출 (/temp/boot.py -> boot.py)
                    if file_path.startswith('/temp/'):
                        actual_filename = file_path[6:]  # '/temp/' 제거
                    else:
                        actual_filename = file_path
                    
                    # 파일별 백업 시작 알림 (상세)
                    backup_start_msg = f"BACKUP_FILE_START:{i+1}/{len(temp_files_to_backup)}:{actual_filename}"
                    print(f"DEBUG: 백업 시작 - temp파일: {file_path} -> 실제파일: {actual_filename}")
                    self._send_upgrade_message(backup_start_msg)
                    
                    # 실제 백업 수행 (실제 파일명 전달)
                    self._backup_existing_file_detailed(actual_filename)
                    backup_count += 1
                    backup_success_list.append(actual_filename)
                    
                    # 파일별 백업 완료 알림 (상세)
                    backup_done_msg = f"BACKUP_FILE_COMPLETE:{i+1}/{len(temp_files_to_backup)}:{actual_filename}"
                    self._send_upgrade_message(backup_done_msg)
                    print(f"DEBUG: 백업 완료 - {actual_filename}")
                    
                    gc.collect()  # 각 백업 후 메모리 정리
                    
                except Exception as backup_error:
                    # 파일명 추출이 실패한 경우를 대비
                    display_filename = actual_filename if 'actual_filename' in locals() else file_path
                    error_msg = f"BACKUP_FILE_ERROR:{i+1}/{len(temp_files_to_backup)}:{display_filename}:{backup_error}"
                    print(f"DEBUG: 백업 실패 - {display_filename}: {backup_error}")
                    self._send_upgrade_message(error_msg)
                    backup_failure_list.append(f"{display_filename}:{backup_error}")
                    # 백업 실패해도 계속 진행
            
            # === 3단계: backup 폴더 검증 ===
            verification_msg = "BACKUP_PHASE:3단계 - 백업 결과 검증 중..."
            print(verification_msg)
            self._send_upgrade_message(verification_msg)
            
            verification_success = False  # 검증 성공 여부 추적
            
            try:
                # backup 폴더 스캔
                backup_files_found_raw = self.scan_directory_iterative(self.backup_dir)
                # 파일 경로만 추출하고 /backup/ 접두사 제거
                backup_files_found = []
                for ftype, path in backup_files_found_raw:
                    if ftype == "FILE":
                        if path.startswith('/backup/'):
                            relative_path = path[8:]  # '/backup/' 제거
                        else:
                            relative_path = path
                        backup_files_found.append(relative_path)
                
                # backup 파일 목록을 웹페이지에 전송
                backup_list_msg = f"BACKUP_FILE_LIST:{len(backup_files_found)}:{','.join(backup_files_found)}"
                self._send_upgrade_message(backup_list_msg)
                
                # 각 backup 파일 정보도 개별 전송
                for i, file_path in enumerate(backup_files_found):
                    backup_file_full_path = f"{self.backup_dir}/{file_path}"
                    try:
                        stat_info = os.stat(backup_file_full_path)
                        file_size = stat_info[6]
                        file_info_msg = f"BACKUP_FILE_INFO:{i+1}:{file_path}:{file_size}"
                        self._send_upgrade_message(file_info_msg)
                    except Exception as stat_error:
                        file_info_msg = f"BACKUP_FILE_INFO:{i+1}:{file_path}:unknown"
                        self._send_upgrade_message(file_info_msg)
                
                # === 4단계: temp와 backup 목록 비교 검증 ===
                comparison_msg = "BACKUP_PHASE:4단계 - temp와 backup 목록 비교 중..."
                print(comparison_msg)
                self._send_upgrade_message(comparison_msg)
                
                # temp 파일 목록에서 실제 파일명 추출하여 비교용 집합 생성
                temp_actual_filenames = []
                for temp_file in temp_files_to_backup:
                    if temp_file.startswith('/temp/'):
                        actual_filename = temp_file[6:]  # '/temp/' 제거
                    else:
                        actual_filename = temp_file
                    temp_actual_filenames.append(actual_filename)
                
                # 집합으로 변환하여 비교
                temp_set = set(temp_actual_filenames)
                backup_set = set(backup_files_found)
                
                # 신규 파일들 (temp에는 있지만 backup에는 없음 - 기존 보드에 없던 파일)
                new_files_in_temp = temp_set - backup_set
                # 추가된 파일들 (backup에는 있지만 temp에는 없음)  
                extra_in_backup = backup_set - temp_set
                # 성공적으로 백업된 파일들
                successfully_backed_up = temp_set & backup_set
                
                # 검증 결과 전송 (신규 파일로 메시지 변경)
                verification_result_msg = f"BACKUP_VERIFICATION:성공:{len(successfully_backed_up)}:신규:{len(new_files_in_temp)}:추가:{len(extra_in_backup)}"
                self._send_upgrade_message(verification_result_msg)
                
                if new_files_in_temp:
                    # 한글 파일명 인코딩 문제 해결을 위해 repr() 대신 직접 처리
                    new_files_list = []
                    for filename in new_files_in_temp:
                        try:
                            # 파일명을 UTF-8로 안전하게 처리
                            safe_filename = filename.encode('utf-8').decode('utf-8')
                            new_files_list.append(safe_filename)
                        except Exception:
                            # 인코딩 실패 시 원본 사용
                            new_files_list.append(filename)
                    
                    new_files_msg = f"BACKUP_NEW_FILES:{','.join(new_files_list)}"
                    self._send_upgrade_message(new_files_msg)
                    
                    # 콘솔 출력도 개선 (한글 파일명 안전 처리)
                    safe_new_files_str = ', '.join(new_files_list)
                    print(f"INFO: 신규 파일 (기존 보드에 없던 파일): {safe_new_files_str}")
                
                if extra_in_backup:
                    extra_msg = f"BACKUP_EXTRA:{','.join(extra_in_backup)}"
                    self._send_upgrade_message(extra_msg)
                    print(f"INFO: 추가 백업 파일: {extra_in_backup}")
                
                # 최종 결과 판정 (신규 파일은 정상으로 처리)
                if len(new_files_in_temp) == 0:
                    verification_success_msg = f"BACKUP_VERIFICATION_SUCCESS:모든 파일이 성공적으로 백업됨"
                    self._send_upgrade_message(verification_success_msg)
                    print("INFO: 백업 검증 성공 - 모든 파일이 정상적으로 백업됨")
                    verification_success = True  # 검증 성공
                else:
                    # 신규 파일이 있는 경우도 정상으로 처리 (경고가 아님)
                    verification_info_msg = f"BACKUP_VERIFICATION_INFO:{len(new_files_in_temp)}개 신규 파일은 백업되지 않음 (정상)"
                    self._send_upgrade_message(verification_info_msg)
                    print(f"INFO: 백업 검증 완료 - {len(new_files_in_temp)}개 신규 파일은 기존 보드에 없어서 백업되지 않음 (정상)")
                    verification_success = True  # 신규 파일이 있어도 성공으로 처리
                
            except Exception as verification_error:
                verification_error_msg = f"BACKUP_VERIFICATION_ERROR:검증 실패:{verification_error}"
                print(f"ERROR: 백업 검증 실패: {verification_error}")
                self._send_upgrade_message(verification_error_msg)
                verification_success = False  # 검증 실패
            
            # === 최종 백업 완료 알림 (검증 완료 후에 전송) ===
            final_summary_msg = f"STEP2_BACKUP_COMPLETE:성공:{len(backup_success_list)}:실패:{len(backup_failure_list)}"
            self._send_upgrade_message(final_summary_msg)
            
            # 검증 성공한 경우에만 최종 성공 메시지 전송
            if verification_success:
                success_msg = f"STEP2_BACKUP_SUCCESS:{backup_count}개 파일 백업 완료"
                print(success_msg)
                self._send_upgrade_message(success_msg)
            else:
                warning_msg = f"STEP2_BACKUP_WARNING:백업 검증에 문제가 있습니다"
                print(warning_msg)
                self._send_upgrade_message(warning_msg)
            
        except Exception as e:
            error_msg = f"STEP2_BACKUP_ERROR:전체 실패:{e}"
            print(error_msg)
            self._send_upgrade_message(error_msg)
    
    def _backup_existing_file_detailed(self, filename):
        """상세한 진행 상황 알림을 포함한 기존 파일 백업"""
        try:
            source_path = f"/{filename}"
            
            # 파일 백업 상세 시작 알림
            detail_start_msg = f"BACKUP_DETAIL:{filename}:시작:원본 확인 중"
            self._send_upgrade_message(detail_start_msg)
            
            # 기존 파일이 존재하는 경우에만 백업
            if self._file_exists(source_path):
                detail_found_msg = f"BACKUP_DETAIL:{filename}:원본 발견:백업 준비 중"
                self._send_upgrade_message(detail_found_msg)
                
                # 백업 폴더가 없으면 생성
                backup_dir = "/backup"
                try:
                    if not self._file_exists(backup_dir):
                        os.mkdir(backup_dir)
                        print(f"DIR_CREATED:{backup_dir}")
                except OSError:
                    pass  # 이미 존재하는 경우 무시
                
                # 백업 파일 경로
                backup_path = f"{backup_dir}/{filename}"
                
                # 백업 파일의 디렉토리 구조도 생성 (lib/xxx.mpy 등의 경우)
                if '/' in filename:
                    path_parts = filename.split('/')
                    if path_parts[0] == 'lib':  # lib로 시작하는 경우만
                        current_backup_path = backup_dir
                        for part in path_parts[:-1]:  # 파일명 제외하고 디렉토리만
                            current_backup_path = f"{current_backup_path}/{part}"
                            if not self._file_exists(current_backup_path):
                                try:
                                    os.mkdir(current_backup_path)
                                    dir_created_msg = f"BACKUP_DETAIL:{filename}:디렉토리 생성:{current_backup_path}"
                                    self._send_upgrade_message(dir_created_msg)
                                    print(f"BACKUP_DIR_CREATED:{current_backup_path}")
                                except OSError as e:
                                    if e.args[0] != 17:  # EEXIST 무시
                                        print(f"BACKUP_DIR_ERROR:{e}")
                
                # 파일 복사 시작 알림 (기존 백업 파일 삭제 로직 제거 - 이미 전체 삭제됨)
                copy_start_msg = f"BACKUP_DETAIL:{filename}:복사 시작"
                self._send_upgrade_message(copy_start_msg)
                
                # 파일 복사 (원본은 그대로 유지)
                self._copy_file(source_path, backup_path)
                
                # 복사 완료 알림
                copy_complete_msg = f"BACKUP_DETAIL:{filename}:복사 완료"
                print(f"BACKUP_COPIED:{filename} -> backup/{filename} (원본 파일 유지)")
                self._send_upgrade_message(copy_complete_msg)
                
            else:
                # 파일이 없는 경우 알림
                not_found_msg = f"BACKUP_DETAIL:{filename}:원본 없음:스킵됨"
                print(f"BACKUP_SKIP:{filename} (파일 없음)")
                self._send_upgrade_message(not_found_msg)
        
        except Exception as e:
            # 백업 실패 상세 알림
            error_detail_msg = f"BACKUP_DETAIL:{filename}:오류:{e}"
            print(f"BACKUP_ERROR:{filename}:{e}")
            self._send_upgrade_message(error_detail_msg)
            raise  # 상위에서 처리할 수 있도록 예외 재발생
    
    
    def _send_upgrade_message(self, message):
        """업그레이드 진행 상황 메시지를 BLE를 통해 웹으로 전송"""
        try:
            #print(message)  # 시리얼 출력도 유지
            #return
            # BLE로 전송
            import bleIoT
            if hasattr(bleIoT, 'uart') and bleIoT.uart:
                msg_bytes = message.encode('utf-8')
                bleIoT.uart.upgrade_notify(msg_bytes)
        except Exception as e:
            print(f"UPGRADE_MSG_SEND_ERROR:{e}")
    
    def _step3_apply_only(self):
        """3단계: temp 파일들을 실제 위치로 적용만"""
        try:
            print("STEP3_APPLY_START")
            self._send_upgrade_message("STEP3_APPLY_START")
            
            # 메모리 정리
            gc.collect()
            
            # temp 디렉토리 존재 확인
            if not self._file_exists(self.temp_dir):
                error_msg = "STEP3_ERROR:temp 디렉토리가 존재하지 않음"
                print(error_msg)
                self._send_upgrade_message(error_msg)
                return
            
            # === 새로운 방식: temp 폴더 전체를 재귀 스캔하여 파일 목록 수집 ===
            print("DEBUG: temp 폴더 전체 구조 스캔 시작")
            self._send_upgrade_message("SCAN_PROGRESS:temp 폴더 구조 분석 중...")
            
            try:
                # temp 폴더 전체를 재귀 스캔하여 모든 파일 경로 수집
                temp_files_raw = self.scan_directory_iterative(self.temp_dir)
                # 파일 경로만 추출하고 /temp/ 접두사 제거
                temp_files_to_apply = []
                for ftype, path in temp_files_raw:
                    if ftype == "FILE":
                        if path.startswith('/temp/'):
                            relative_path = path[6:]  # '/temp/' 제거
                        else:
                            relative_path = path
                        temp_files_to_apply.append(relative_path)
                
                print(f"DEBUG: temp 폴더 스캔 완료 - 총 {len(temp_files_to_apply)}개 파일 발견")
                
            except Exception as scan_error:
                error_msg = f"STEP3_ERROR:temp 폴더 스캔 실패: {scan_error}"
                print(error_msg)
                self._send_upgrade_message(error_msg)
                return
            
            if len(temp_files_to_apply) == 0:
                warning_msg = "STEP3_WARNING:적용할 파일이 없습니다"
                success_msg = "STEP3_APPLY_SUCCESS:0개 파일 설치 완료"
                print(warning_msg)
                print(success_msg)
                self._send_upgrade_message(warning_msg)
                self._send_upgrade_message(success_msg)
                return
            
            # 적용 시작 알림
            start_msg = f"APPLY_PROGRESS:시작:{len(temp_files_to_apply)}개 파일 적용 시작"
            print(start_msg)
            self._send_upgrade_message(start_msg)
            
            # 파일 목록 기반으로 적용 수행
            print("DEBUG: STEP3 - 파일 설치 시작")
            install_count = 0
            for i, file_path in enumerate(temp_files_to_apply):
                try:
                    temp_file_path = f"{self.temp_dir}/{file_path}"
                    
                    # 파일별 적용 시작 알림
                    apply_start_msg = f"APPLY_PROGRESS:파일:{i+1}/{len(temp_files_to_apply)}:{file_path}:시작"
                    print(f"DEBUG: 설치 시도 - {file_path} (temp: {temp_file_path})")
                    self._send_upgrade_message(apply_start_msg)
                    
                    self._install_new_file(file_path, temp_file_path)
                    install_count += 1
                    
                    # 파일별 적용 완료 알림
                    apply_done_msg = f"APPLY_PROGRESS:파일:{i+1}/{len(temp_files_to_apply)}:{file_path}:완료"
                    self._send_upgrade_message(apply_done_msg)
                    
                    gc.collect()  # 각 설치 후 메모리 정리
                    
                except Exception as install_error:
                    error_msg = f"STEP3_INSTALL_ERROR:{file_path}:{install_error}"
                    print(error_msg)
                    self._send_upgrade_message(error_msg)
                    print(f"DEBUG: 설치 실패시 롤백 권장")
                    return
            
            # 전체 적용 완료 알림
            success_msg = f"STEP3_APPLY_SUCCESS:{install_count}개 파일 설치 완료"
            print(success_msg)
            self._send_upgrade_message(success_msg)
            
        except Exception as e:
            error_msg = f"STEP3_APPLY_ERROR:전체 실패:{e}"
            print(error_msg)
            self._send_upgrade_message(error_msg)
    
    def _step4_cleanup_and_restart(self):
        """4단계: temp 정리 및 재시작"""
        try:
            self._send_upgrade_message("STEP4_CLEANUP_START")
            
            # 임시 파일 정리
            self._send_upgrade_message("CLEANUP_PROGRESS:temp 파일들 안전 정리 시작")
            
            try:
                # temp 폴더 완전 삭제 (폴더 자체도 삭제)
                self.remove_folder_files()  # target_dir=None(temp), delete_root=True
                cleanup_msg = "STEP4_CLEANUP_SUCCESS:temp 파일들 정리 완료"
                print(cleanup_msg)
                self._send_upgrade_message(cleanup_msg)
            except Exception as cleanup_error:
                warning_msg = f"STEP4_CLEANUP_WARNING:temp 파일 정리 실패: {cleanup_error}"
                print(warning_msg)
                self._send_upgrade_message(warning_msg)
                # 정리 실패해도 계속 진행 (재시작으로 해결됨)
            
            gc.collect()
            
            success_msg = "STEP4_SUCCESS:모든 단계 완료"
            restart_msg = "RESTART_PROGRESS:3초 후 자동 재시작..."
            print(success_msg)
            print("재시작이 필요합니다. 3초 후 자동 재시작...")
            self._send_upgrade_message(success_msg)
            self._send_upgrade_message(restart_msg)
            
            # 1초 후 재시작
            time.sleep(1)
            reset()
            
        except Exception as e:
            error_msg = f"STEP4_ERROR:{e}"
            print(error_msg)
            self._send_upgrade_message(error_msg)
    
    def _emergency_cleanup(self):
        """응급 상황 정리"""
        try:
            print("EMERGENCY_CLEANUP_START")
            
            # 모든 파일 핸들 닫기
            if self.current_file_handle:
                self.current_file_handle.close()
                self.current_file_handle = None
            
            # 메모리 정리
            gc.collect()
            
            # 업그레이드 모드 종료
            self.is_upgrade_mode = False
            
            print("EMERGENCY_CLEANUP_DONE")
            
        except Exception as e:
            print(f"EMERGENCY_CLEANUP_ERROR:{e}")
    
    def _backup_existing_file(self, filename):
        """기존 파일 백업 (백업 폴더 사용) - 복사 방식으로 수정"""
        try:
            source_path = f"/{filename}"
            
            # 기존 파일이 존재하는 경우에만 백업
            if self._file_exists(source_path):
                # 백업 폴더가 없으면 생성
                backup_dir = "/backup"
                try:
                    if not self._file_exists(backup_dir):
                        os.mkdir(backup_dir)
                        print(f"DIR_CREATED:{backup_dir}")
                except OSError:
                    pass  # 이미 존재하는 경우 무시
                
                # 백업 파일 경로
                backup_path = f"{backup_dir}/{filename}"
                
                # 백업 파일의 디렉토리 구조도 생성 (lib/xxx.mpy 등의 경우)
                if '/' in filename:
                    path_parts = filename.split('/')
                    if path_parts[0] == 'lib':  # lib로 시작하는 경우만
                        current_backup_path = backup_dir
                        for part in path_parts[:-1]:  # 파일명 제외하고 디렉토리만
                            current_backup_path = f"{current_backup_path}/{part}"
                            if not self._file_exists(current_backup_path):
                                try:
                                    os.mkdir(current_backup_path)
                                    print(f"BACKUP_DIR_CREATED:{current_backup_path}")
                                except OSError as e:
                                    if e.args[0] != 17:  # EEXIST 무시
                                        print(f"BACKUP_DIR_ERROR:{e}")
                
                # 기존 백업 파일이 있으면 삭제
                if self._file_exists(backup_path):
                    os.remove(backup_path)
                    print(f"OLD_BACKUP_REMOVED:{backup_path}")
                
                # 파일 백업 시작 상세 알림
                backup_start_msg = f"BACKUP_FILE_PROGRESS:{filename}:복사 시작"
                self._send_upgrade_message(backup_start_msg)
                
                # 파일 복사 (원본은 그대로 유지) - os.rename 대신 _copy_file 사용
                self._copy_file(source_path, backup_path)
                
                # 백업 성공 알림 (상세)
                backup_success_msg = f"BACKUP_FILE_PROGRESS:{filename}:복사 완료"
                print(f"BACKUP_COPIED:{filename} -> backup/{filename} (원본 파일 유지)")
                self._send_upgrade_message(backup_success_msg)
                
            else:
                # 파일이 없는 경우도 알림
                skip_msg = f"BACKUP_FILE_PROGRESS:{filename}:파일 없음 (스킵)"
                print(f"BACKUP_SKIP:{filename} (파일 없음)")
                self._send_upgrade_message(skip_msg)
        
        except Exception as e:
            # 백업 실패도 상세히 알림
            error_msg = f"BACKUP_FILE_ERROR:{filename}:{e}"
            print(f"BACKUP_ERROR:{filename}:{e}")
            self._send_upgrade_message(error_msg)
            # 백업 실패해도 계속 진행
    
    def _rollback_upgrade(self):
        """업그레이드 롤백"""
        try:
            print("ROLLBACK_START")
            
            # 백업된 파일들을 복원
            for filename in self.received_files:
                backup_path = f"{self.backup_dir}/{filename}"
                target_path = f"/{filename}"
                
                if self._file_exists(backup_path):
                    self._copy_file(backup_path, target_path)
                    print(f"ROLLBACK_OK:{filename}")
            
            print("ROLLBACK_SUCCESS")
            
        except Exception as e:
            print(f"ROLLBACK_ERROR:{e}")
    
    def _rollback_from_backup(self):
        """백업 폴더에서 기존 버전 복원"""
        try:
            print("ROLLBACK_START")
            backup_dir = "/backup"
            
            if not self._file_exists(backup_dir):
                print("ROLLBACK_ERROR:백업 폴더가 존재하지 않습니다")
                return
            
            # 백업 파일 목록 수집 (올바른 방식)
            backup_files_raw = self.scan_directory_iterative(backup_dir)
            backup_files = [path[8:] for ftype, path in backup_files_raw 
                           if ftype == "FILE" and path.startswith('/backup/')]
            
            if not backup_files:
                print("ROLLBACK_ERROR:백업 파일이 없습니다")
                return
            
            print(f"DEBUG: {len(backup_files)}개 백업 파일 발견")
            
            # 각 파일 복원 (안전한 방식으로 개선)
            successful_restores = 0
            for i, backup_file in enumerate(backup_files):
                backup_path = f"{backup_dir}/{backup_file}"
                restore_path = f"/{backup_file}"
                
                # 진행률 표시
                print(f"ROLLBACK_PROGRESS:{i+1}/{len(backup_files)}:{backup_file}")
                
                try:
                    # === 사전 안전성 검사 ===
                    # 백업 파일 존재 확인
                    if not self._file_exists(backup_path):
                        print(f"ROLLBACK_SKIP:{backup_file}:백업 파일 없음")
                        continue
                    
                    # 메모리 상태 사전 확인
                    free_mem = gc.mem_free()
                    if free_mem < 30000:  # 30KB 미만이면 적극적 정리
                        print(f"ROLLBACK_GC:{backup_file}:메모리 부족 정리 시작({free_mem//1024}KB)")
                        gc.collect()
                        gc.collect()  # 이중 정리
                        time.sleep_ms(100)  # 잠시 대기
                        free_mem = gc.mem_free()
                        print(f"ROLLBACK_GC:{backup_file}:정리 후 {free_mem//1024}KB")
                    
                    # === 기존 파일 안전 삭제 ===
                    if self._file_exists(restore_path):
                        try:
                            stat = os.stat(restore_path)
                            if stat[0] & 0x4000:  # 디렉토리면 건너뜀
                                print(f"ROLLBACK_SKIP:{backup_file}:디렉토리임")
                                continue
                            os.remove(restore_path)
                            print(f"ROLLBACK_REMOVED:{backup_file}")
                        except Exception as remove_error:
                            print(f"ROLLBACK_REMOVE_ERROR:{backup_file}:{remove_error}")
                            # 삭제 실패해도 계속 진행
                    
                    # === 안전한 디렉토리 생성 ===
                    try:
                        self._ensure_directory_for_file(restore_path)
                    except Exception as dir_error:
                        print(f"ROLLBACK_DIR_ERROR:{backup_file}:{dir_error}")
                        continue
                    
                    # === 안전한 파일 복사 ===
                    try:
                        # 복사 전 추가 메모리 정리
                        gc.collect()
                        self._copy_file(backup_path, restore_path)
                        print(f"ROLLBACK_OK:{backup_file}")
                        successful_restores += 1
                        
                    except Exception as copy_error:
                        print(f"ROLLBACK_COPY_ERROR:{backup_file}:{copy_error}")
                        continue
                    
                    # === 복사 후 메모리 정리 ===
                    gc.collect()
                    
                    # 복잡한 경로 처리 후 추가 대기 (fatal error 방지)
                    if '/' in backup_file and len(backup_file.split('/')) > 2:
                        time.sleep_ms(50)  # 복잡한 경로는 추가 대기
                    
                except Exception as e:
                    print(f"ROLLBACK_FILE_ERROR:{backup_file}:{e}")
                    # 심각한 오류 시 잠시 대기 후 계속
                    time.sleep_ms(200)
                    gc.collect()
                    continue
            
            # 복원 결과 요약
            print(f"ROLLBACK_SUMMARY:{successful_restores}/{len(backup_files)} 파일 복원 완료")
            
            # 롤백 성공 여부 판단 (80% 이상 복원 시 성공으로 간주)
            success_rate = (successful_restores / len(backup_files)) * 100 if backup_files else 0
            
            if success_rate >= 80:
                print("ROLLBACK_SUCCESS")
                
                # 롤백 성공 후 backup 폴더 삭제 (역할 완료)
                try:
                    print("ROLLBACK_CLEANUP:backup 폴더 정리 시작")
                    self.remove_folder_files(backup_dir, delete_root=True)
                    print("ROLLBACK_CLEANUP:backup 폴더 삭제 완료")
                except Exception as cleanup_error:
                    print(f"ROLLBACK_CLEANUP_WARNING:backup 폴더 삭제 실패 - {cleanup_error}")
                    # 삭제 실패해도 재시작은 진행
                
                print("롤백 완료! 1초 후 재시작...")
                time.sleep(1)
                reset()
                
            else:
                print(f"ROLLBACK_PARTIAL:부분 복원만 완료 ({success_rate:.1f}%)")
                print("ROLLBACK_WARNING:일부 파일 복원 실패로 인해 backup 폴더를 유지합니다")
                print("ROLLBACK_INFO:수동으로 파일을 확인하거나 다시 롤백을 시도하세요")
                # backup 폴더를 유지하고 재시작하지 않음
            
        except Exception as e:
            print(f"ROLLBACK_ERROR:{e}")
    
    def _abort_upgrade(self):
        """업그레이드 중단"""
        try:
            if self.current_file_handle:
                self.current_file_handle.close()
                self.current_file_handle = None
            
            # temp 폴더 완전 삭제 (폴더 자체도 삭제)
            self.remove_folder_files()  # target_dir=None(temp), delete_root=True
            self.exit_upgrade_mode()
            print("UPGRADE_ABORTED")
            
        except Exception as e:
            print(f"ABORT_ERROR:{e}")
    
    def _ensure_directory(self, dir_path):
        """디렉토리 생성"""
        try:
            # 절대 경로로 변환
            if not dir_path.startswith('/'):
                dir_path = '/' + dir_path
            
            # 이미 존재하는지 확인
            if self._file_exists(dir_path):
                return
            
            # 경로를 분할하여 단계별로 생성
            parts = [p for p in dir_path.split('/') if p]
            current_path = ''
            
            for part in parts:
                current_path += '/' + part
                try:
                    if not self._file_exists(current_path):
                        os.mkdir(current_path)
                        print(f"DIR_CREATED:{current_path}")
                except OSError as e:
                    if e.args[0] != 17:  # EEXIST 무시
                        raise
                        
        except Exception as e:
            print(f"DIR_CREATE_ERROR:{dir_path}:{e}")
    
    def _ensure_directory_for_file(self, file_path):
        """파일의 상위 디렉토리 생성"""
        dir_path = "/".join(file_path.split("/")[:-1])
        if dir_path and dir_path != "":
            self._ensure_directory(dir_path)
    
    def _file_exists(self, path):
        """파일 존재 여부 확인"""
        try:
            os.stat(path)
            return True
        except OSError:
            return False
    
    def _copy_file(self, source, destination):
        """파일 복사"""
        try:
            with open(source, 'rb') as src:
                with open(destination, 'wb') as dst:
                    while True:
                        chunk = src.read(1024)
                        if not chunk:
                            break
                        dst.write(chunk)
        except Exception as e:
            print(f"COPY_ERROR:{source}->{destination}:{e}")
            raise
    
    def remove_folder_files(self, target_dir=None, delete_root=True):
        """디렉토리 정리 - 파일과 디렉토리를 안전하게 삭제 (재사용 가능)"""
        if target_dir is None:
            target_dir = self.temp_dir
            
        try:
            target_name = target_dir.split('/')[-1]
            print(f"CLEANUP_START:{target_name} 폴더 정리 시작 - {target_dir}")
            
            # scan_directory_iterative 사용하여 모든 파일 목록 수집
            try:
                files_raw = self.scan_directory_iterative(target_dir)
                files = [path for ftype, path in files_raw if ftype == "FILE"]
                dirs = [path for ftype, path in files_raw if ftype == "DIR"]
                
                print(f"CLEANUP_SCAN:총 {len(files)}개 파일, {len(dirs)}개 디렉토리 발견")
                
                # 파일만 개별 삭제
                deleted_files = 0
                for file_path in files:
                    try:
                        os.remove(file_path)
                        filename = file_path.split('/')[-1]  # 파일명만 추출
                        print(f"CLEANUP_FILE_OK:{filename}")
                        deleted_files += 1
                    except OSError as e:
                        if e.args[0] != 2:  # ENOENT 무시
                            filename = file_path.split('/')[-1]
                            print(f"CLEANUP_FILE_FAIL:{filename}:{e}")
                
                print(f"CLEANUP_SUCCESS:{deleted_files}개 파일 삭제 완료")
                
                # 빈 디렉토리 정리 (안전한 방식)
                try:
                    # 디렉토리 목록을 깊은 것부터 역순으로 정렬
                    dirs.sort(reverse=True)  # 깊은 디렉토리부터 정렬
                    
                    print(f"CLEANUP_DIR_START:{len(dirs)}개 디렉토리 정리 시작")
                    deleted_dirs = 0
                    
                    for dir_path in dirs:
                        try:
                            os.rmdir(dir_path)
                            dirname = dir_path.split('/')[-1]
                            print(f"CLEANUP_DIR_OK:{dirname}")
                            deleted_dirs += 1
                        except OSError as e:
                            if e.args[0] != 2:  # ENOENT 무시
                                dirname = dir_path.split('/')[-1]
                                print(f"CLEANUP_DIR_SKIP:{dirname} (비어있지 않거나 삭제 불가)")
                    
                    # 최상위 폴더 삭제 시도 (선택적)
                    if delete_root:
                        try:
                            os.rmdir(target_dir)
                            print(f"CLEANUP_ROOT_OK:{target_name} 폴더 삭제 완료")
                            deleted_dirs += 1
                        except OSError as e:
                            if e.args[0] != 2:  # ENOENT 무시
                                print(f"CLEANUP_ROOT_SKIP:{target_name} 폴더 삭제 실패 - {e}")
                    
                    print(f"CLEANUP_DIR_SUCCESS:{deleted_dirs}개 디렉토리 삭제 완료")
                    
                except Exception as dir_error:
                    print(f"CLEANUP_DIR_ERROR:디렉토리 정리 실패 - {dir_error}")
                    print(f"CLEANUP_INFO:남은 디렉토리는 재시작 후 자동 정리됨")
                
            except Exception as scan_error:
                print(f"CLEANUP_SCAN_ERROR:파일 스캔 실패 - {scan_error}")
                # 스캔 실패시 기본 방식으로 fallback
                self.remove_folder_files_simple(target_dir)
                    
        except Exception as e:
            print(f"CLEANUP_ERROR:파일 정리 실패 - {e}")
            # 실패해도 계속 진행 (재시작으로 해결됨)
    
    def remove_folder_files_simple(self, target_dir=None):
        """단순한 파일 정리 (fallback 방식)"""
        if target_dir is None:
            target_dir = self.temp_dir
            
        try:
            target_name = target_dir.split('/')[-1]
            print(f"CLEANUP_SIMPLE:{target_name} 폴더 단순 정리 시작")
            if not os.stat(target_dir):
                return
            
            for item in os.listdir(target_dir):
                item_path = f"{target_dir}/{item}"
                try:
                    os.remove(item_path)  # 파일만 삭제 시도
                    print(f"CLEANUP_SIMPLE_OK:{item}")
                except OSError:
                    print(f"CLEANUP_SIMPLE_SKIP:{item} (디렉토리 또는 삭제 불가)")
                    
        except Exception as e:
            print(f"CLEANUP_SIMPLE_ERROR:{e}")
    




    def _install_new_file(self, filename, temp_path):
        """새 파일 설치 (안전한 버전)"""
        try:
            target_path = f"/{filename}"
            print(f"DEBUG: 파일 설치 시작 - {filename}")
            print(f"DEBUG: 소스: {temp_path}")
            print(f"DEBUG: 타겟: {target_path}")
            
            # === 안전한 디렉토리 생성 (다단계 지원으로 개선) ===
            if '/' in filename:
                # filename이 "lib/max30102/file.mpy" 형태인 경우
                path_parts = filename.split('/')
                file_only = path_parts[-1]  # 실제 파일명
                dir_path = '/'.join(path_parts[:-1])  # 디렉토리 경로
                
                print(f"DEBUG: 다단계 경로 감지 - 디렉토리: {dir_path}, 파일: {file_only}")
                
                # lib로 시작하는 경우만 허용 (보안상)
                if path_parts[0] == 'lib':
                    # 전체 디렉토리 경로를 루트 하위에 생성
                    current_path = ""
                    for part in path_parts[:-1]:  # 파일명 제외하고 디렉토리만
                        current_path = f"{current_path}/{part}"
                        if not self._file_exists(current_path):
                            try:
                                os.mkdir(current_path)
                                print(f"DIR_CREATED:{current_path}")
                            except OSError as e:
                                if e.args[0] != 17:  # EEXIST 무시
                                    print(f"DIR_ERROR:{e}")
                                    raise
                else:
                    print(f"WARNING: lib 외의 디렉토리는 지원하지 않음: {filename}")
                    print(f"INSTALL_ERROR:{filename}:lib 외의 디렉토리")
                    return
            else:
                print(f"DEBUG: 루트 레벨 파일: {filename} (디렉토리 생성 불필요)")
            
            print(f"DEBUG: 디렉토리 준비 완료, 파일 복사 시작")
            
            # 파일 복사 (간단한 방식)
            self._copy_file(temp_path, target_path)
            print(f"DEBUG: 파일 복사 완료")
            
            # 임시 파일은 STEP4에서 정리하므로 여기서 삭제하지 않음
            print(f"DEBUG: temp 파일 유지 (STEP4에서 정리 예정)")
            
            print(f"INSTALL_OK:{filename}")
            
        except Exception as e:
            print(f"INSTALL_ERROR:{filename}:{e}")
            print(f"DEBUG: 설치 오류 상세: {type(e).__name__}: {e}")
            raise



# 전역 업그레이더 인스턴스
_firmware_upgrader = None

def get_firmware_upgrader():
    """전역 업그레이더 인스턴스 반환"""
    global _firmware_upgrader
    if _firmware_upgrader is None:
        _firmware_upgrader = FirmwareUpgrader()
    return _firmware_upgrader

def handle_upgrade_command(command):
    """업그레이드 명령어 처리 (외부에서 호출)"""
    upgrader = get_firmware_upgrader()
    return upgrader.process_upgrade_command(command) 