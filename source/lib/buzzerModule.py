# buzzerModule.py
# 버저 제어를 위한 간단한 라이브러리

import machine
import time
import _thread

# 음표 주파수 (3옥타브 ~ 5옥타브)
# 3옥타브 (낮은 옥타브)
NOTE_C3 = 131
NOTE_CS3 = 139
NOTE_D3 = 147
NOTE_DS3 = 156
NOTE_E3 = 165
NOTE_F3 = 175
NOTE_FS3 = 185
NOTE_G3 = 196
NOTE_GS3 = 208
NOTE_A3 = 220
NOTE_AS3 = 233
NOTE_B3 = 247

# 4옥타브 (중간 옥타브)
NOTE_C4 = 262
NOTE_CS4 = 277
NOTE_D4 = 294
NOTE_DS4 = 311
NOTE_E4 = 330
NOTE_F4 = 349
NOTE_FS4 = 370
NOTE_G4 = 392
NOTE_GS4 = 415
NOTE_A4 = 440
NOTE_AS4 = 466
NOTE_B4 = 494

# 5옥타브 (높은 옥타브)
NOTE_C5 = 523
NOTE_CS5 = 554
NOTE_D5 = 587
NOTE_DS5 = 622
NOTE_E5 = 659
NOTE_F5 = 698
NOTE_FS5 = 740
NOTE_G5 = 784
NOTE_GS5 = 831
NOTE_A5 = 880
NOTE_AS5 = 932
NOTE_B5 = 988

# 미리 정의된 멜로디
MELODY_TWINKLE_TWINKLE = [
    (NOTE_C4, '4'), (NOTE_C4, '4'), (NOTE_G4, '4'), (NOTE_G4, '4'),
    (NOTE_A4, '4'), (NOTE_A4, '4'), (NOTE_G4, '2'),
    (NOTE_F4, '4'), (NOTE_F4, '4'), (NOTE_E4, '4'), (NOTE_E4, '4'),
    (NOTE_D4, '4'), (NOTE_D4, '4'), (NOTE_C4, '2')
]

MELODY_FUR_ELISE = [
    (NOTE_E5, '8'), (NOTE_DS5, '8'), (NOTE_E5, '8'), (NOTE_DS5, '8'),
    (NOTE_E5, '8'), (NOTE_B4, '8'), (NOTE_D5, '8'), (NOTE_C5, '8'),
    (NOTE_A4, '4'), (0, '8'), (NOTE_C4, '8'), (NOTE_E4, '8'), (NOTE_A4, '8'),
    (NOTE_B4, '4'), (0, '8'), (NOTE_E4, '8'), (NOTE_GS4, '8'), (NOTE_B4, '8'),
    (NOTE_C5, '4')
]

# 멜로디: 학교종이 땡땡땡
MELODY_SCHOOL_BELL = [
    (NOTE_G4, '4'), (NOTE_G4, '4'), (NOTE_A4, '4'), (NOTE_A4, '4'),
    (NOTE_G4, '4'), (NOTE_G4, '4'), (NOTE_E4, '2'),
    (NOTE_G4, '4'), (NOTE_G4, '4'), (NOTE_E4, '4'), (NOTE_E4, '4'),
    (NOTE_D4, '2'), (0, '2')
]

# 간단한 효과음
SOUND_BEEP = [(NOTE_C5, '8')]
SOUND_SUCCESS = [(NOTE_C4, '8'), (NOTE_E4, '8'), (NOTE_G4, '4')]
SOUND_ERROR = [(NOTE_A4, '8'), (NOTE_E4, '8'), (NOTE_A3, '4')]
SOUND_ALERT = [(NOTE_A4, '16'), (NOTE_A4, '16'), (NOTE_A4, '8')]

# 버저 컨트롤러 클래스
class BuzzerController:
    def __init__(self, pin=42):
        # Ensure attribute exists even if init fails
        self._current_melody_name = None
        try:
            self.is_continuous = False
            self._initialized = True
            self._completion_callback = None
            
            # 멜로디 재생을 위한 스레드 변수
            self._melody_thread = None
            self._melody_stop_flag = False
            self._melody_thread_lock = _thread.allocate_lock()
            self.pin = machine.Pin(pin, machine.Pin.OUT)
            # Some boards can't use default PWM freq (often 5000Hz).
            # Try safe frequency first, then fall back.
            try:
                self.pwm = machine.PWM(self.pin, freq=2000)
                self.pwm.duty_u16(0)  # 시작 시 음소거
            except Exception:
                self.pwm = machine.PWM(self.pin)
                self.pwm.freq(2000)
                self.pwm.duty_u16(0)  # 시작 시 음소거
            
            print(f"[Buzzer] Initialized on pin {pin}")
        except Exception as e:
            self._initialized = False
            print(f"[Buzzer] Error initializing: {e}")
    
    def beep(self, count=1, frequency=2000, duration_ms=100, interval_ms=100):
        """일반 비프음 재생"""
        if not self._initialized:
            return False
            
        # 이미 재생 중인 멜로디가 있으면 중지
        if not self._stop_all_threads():
            print("[Buzzer] SAFETY: Cannot beep - thread still active")
            return False
            
        try:
            self.is_continuous = False
            print(f"[Buzzer] Beeping {count} times at {frequency}Hz")
            
            for i in range(count):
                self.pwm.freq(frequency)
                self.pwm.duty_u16(32767)  # 50% 듀티 사이클
                time.sleep_ms(duration_ms)
                self.pwm.duty_u16(0)  # 음소거
                if i < count-1:
                    time.sleep_ms(interval_ms)
                    
            return True
        except Exception as e:
            print(f"[Buzzer] Error in beep: {e}")
            self.pwm.duty_u16(0)  # 오류 발생 시 음소거
            return False
    
    def _melody_thread_function(self, melody, tempo):
        """멜로디 재생을 위한 스레드 함수 - IRQ 최적화"""
        if not self._initialized:
            return
            
        try:
            # 멜로디 재생
            for note, note_type in melody:
                # 중지 플래그 확인 (덜 빈번하게)
                with self._melody_thread_lock:
                    if self._melody_stop_flag:
                        break
                
                try:
                    duration_ms = self._calculate_duration(tempo, note_type)
                    if note > 0:
                        # PWM 비활성화 상태 확인
                        if not self._initialized:
                            break
                        
                        try:
                            self.pwm.freq(note)
                            self.pwm.duty_u16(32767)
                        except (RuntimeError, OSError) as e:
                            print(f"[Buzzer] PWM operation failed, stopping melody: {e}")
                            break
                        
                        # 긴 음표는 큰 청크로 나누어 IRQ 부하 감소
                        if duration_ms > 200:
                            # 200ms 이상은 100ms 청크로
                            total_chunks = max(1, int(duration_ms / 100))
                            chunk_ms = duration_ms / total_chunks
                        else:
                            # 짧은 음표는 그냥 한번에 재생
                            total_chunks = 1
                            chunk_ms = duration_ms
                        
                        for chunk in range(total_chunks):
                            time.sleep_ms(int(chunk_ms))
                            # 중지 플래그 확인 (청크당 한 번만)
                            if total_chunks > 1:  # 긴 음표에서만 중간 체크
                                with self._melody_thread_lock:
                                    if self._melody_stop_flag:
                                        break
                            # PWM 비활성화 상태 확인
                            if not self._initialized:
                                break
                        
                        # 최종 중지 플래그 확인
                        with self._melody_thread_lock:
                            if self._melody_stop_flag or not self._initialized:
                                break
                        
                        try:
                            self.pwm.duty_u16(0)
                        except (RuntimeError, OSError):
                            # PWM이 이미 비활성화됨
                            break
                    else:
                        # 쉼표 - 간단하게 처리
                        if duration_ms > 200:
                            # 긴 쉼표만 중간 체크
                            chunks = int(duration_ms / 100)
                            for _ in range(chunks):
                                time.sleep_ms(100)
                                with self._melody_thread_lock:
                                    if self._melody_stop_flag:
                                        break
                            remainder = duration_ms % 100
                            if remainder > 0:
                                time.sleep_ms(remainder)
                        else:
                            # 짧은 쉼표는 한번에
                            time.sleep_ms(duration_ms)
                
                except Exception as e:
                    print(f"[Buzzer] Error playing note: {e}")
                    # 노트 재생 중 오류 발생 시 다음 노트로 계속 진행
                    
                # 중지 플래그 확인 (노트 사이에만)
                with self._melody_thread_lock:
                    if self._melody_stop_flag or not self._initialized:
                        break
                    
                # 노트 간 간격 줄임
                time.sleep_ms(5)
            
            # 모든 소리 중지 시도
            try:
                if self._initialized:
                    self.pwm.duty_u16(0)
            except Exception:
                # PWM이 이미 비활성화됨
                pass
            
            # 스레드 변수 초기화
            with self._melody_thread_lock:
                self._melody_thread = None
                self._melody_stop_flag = False
                self._current_melody_name = None
                    
        except Exception as e:
            print(f"[Buzzer] Error in melody thread: {e}")
            # 오류 발생 시 소리 중지 시도
            try:
                if self._initialized:
                    self.pwm.duty_u16(0)
            except Exception:
                # PWM이 이미 비활성화됨
                pass
            
            # 스레드 변수 초기화
            with self._melody_thread_lock:
                self._melody_thread = None
                self._melody_stop_flag = False
                self._current_melody_name = None
    
    def _stop_all_threads(self):
        """실행 중인 모든 스레드 중지 (멜로디, 비프음 등) - IRQ 최적화"""
        # 스레드 중지 플래그 설정
        with self._melody_thread_lock:
            if self._melody_thread is not None:
                self._melody_stop_flag = True
                print("[Buzzer] Stop signal sent to thread")
            else:
                # 스레드가 없으면 바로 리턴
                return True
        
        # 소리 즉시 중지 (하드웨어 안전 우선)
        if self._initialized:
            try:
                self.pwm.duty_u16(0)
                print("[Buzzer] PWM stopped")
            except Exception as e:
                print(f"[Buzzer] PWM stop error: {e}")
        
        # 스레드가 자연스럽게 종료될 때까지 대기 (IRQ 부하 감소)
        max_wait = 20  # 20 × 25ms = 500ms (간격을 늘림)
        while max_wait > 0:
            with self._melody_thread_lock:
                if self._melody_thread is None:
                    print("[Buzzer] Thread stopped naturally")
                    return True
            time.sleep_ms(25)  # 25ms로 늘림 (IRQ 부하 감소)
            max_wait -= 1
        
        # 스레드가 여전히 존재하면 강제 정리하지 않음
        print("[Buzzer] WARNING: Thread still running, keeping it safe")
        return False  # 정리 실패 표시
    
    def play_melody(self, melody_name, tempo=120):
        """스마트 멜로디 재생 - 안전 우선"""
        if not self._initialized:
            return False
        
        melody_name_upper = melody_name.upper()
        
        # 먼저 이전 스레드가 있는지 확인 (안전 우선)
        thread_exists = False
        current_melody = None
        
        with self._melody_thread_lock:
            if self._melody_thread is not None:
                thread_exists = True
                current_melody = self._current_melody_name
        
        # 이전 스레드가 있으면 정리 시도
        if thread_exists:
            if current_melody == melody_name_upper:
                print(f"[Buzzer] {melody_name} already playing, stopping first")
            else:
                print(f"[Buzzer] Changing melody to {melody_name}")
            
            cleanup_success = self._stop_all_threads()
            
            if not cleanup_success:
                print(f"[Buzzer] SAFETY: Cannot start {melody_name} - previous thread still active")
                return False  # 안전을 위해 새 재생 거부
        
        try:
            self.is_continuous = False
            
            # 멜로디 선택
            melody = None
            if melody_name_upper == "TWINKLE":
                melody = MELODY_TWINKLE_TWINKLE
                print("[Buzzer] Playing Twinkle Twinkle")
            elif melody_name_upper == "FUR_ELISE":
                melody = MELODY_FUR_ELISE
                print("[Buzzer] Playing Fur Elise")
            elif melody_name_upper == "SCHOOL_BELL":
                melody = MELODY_SCHOOL_BELL
                print("[Buzzer] Playing School Bell")
            elif melody_name_upper == "BEEP":
                melody = SOUND_BEEP
                print("[Buzzer] Playing Beep")
            elif melody_name_upper == "SUCCESS":
                melody = SOUND_SUCCESS
                print("[Buzzer] Playing Success sound")
            elif melody_name_upper == "ERROR":
                melody = SOUND_ERROR
                print("[Buzzer] Playing Error sound")
            elif melody_name_upper == "ALERT":
                melody = SOUND_ALERT
                print("[Buzzer] Playing Alert sound")
            else:
                print(f"[Buzzer] Unknown melody: {melody_name}")
                return False
            
            # 멜로디 스레드 시작 (이중 안전 체크)
            with self._melody_thread_lock:
                # 마지막 순간에 다시 한번 스레드 상태 확인
                if self._melody_thread is not None:
                    print(f"[Buzzer] CRITICAL: Thread found at start time! Aborting {melody_name}")
                    return False
                
                self._melody_stop_flag = False
                self._current_melody_name = melody_name_upper
                
                try:
                    self._melody_thread = _thread.start_new_thread(self._melody_thread_function, (melody, tempo))
                    print(f"[Buzzer] Thread started safely for {melody_name_upper}")
                except Exception as e:
                    print(f"[Buzzer] CRITICAL: Thread start failed: {e}")
                    self._melody_thread = None
                    self._melody_stop_flag = False
                    self._current_melody_name = None
                    return False
                
            return True
        except Exception as e:
            print(f"[Buzzer] Error starting melody thread: {e}")
            self.pwm.duty_u16(0)
            return False
    
    def _calculate_duration(self, tempo, note_type):
        """음표 지속 시간 계산"""
        try:
            # 4분 음표 하나의 지속 시간 (ms)
            quarter_note_ms = 60000 / tempo
            
            # 음표 유형에 따른 지속 시간
            durations = {
                '1': quarter_note_ms * 4,    # 온음표
                '2': quarter_note_ms * 2,    # 2분 음표
                '4': quarter_note_ms,        # 4분 음표
                '8': quarter_note_ms / 2,    # 8분 음표
                '16': quarter_note_ms / 4,   # 16분 음표
                '32': quarter_note_ms / 8    # 32분 음표
            }
            
            return durations.get(note_type, quarter_note_ms)
        except Exception as e:
            print(f"[Buzzer] Error calculating duration: {e}")
            return 500  # 기본값
    
    def play_tone(self, frequency=2000, duration_ms=500):
        """단일 톤 재생"""
        # 이미 재생 중인 멜로디가 있으면 중지
        if not self._stop_all_threads():
            print("[Buzzer] SAFETY: Cannot play tone - thread still active")
            return False
        
        if not self._initialized:
            return False
            
        try:
            self.is_continuous = False
            print(f"[Buzzer] Playing tone {frequency}Hz for {duration_ms}ms")
            
            self.pwm.freq(frequency)
            self.pwm.duty_u16(32767)
            time.sleep_ms(duration_ms)
            self.pwm.duty_u16(0)
            
            return True
        except Exception as e:
            print(f"[Buzzer] Error in play_tone: {e}")
            self.pwm.duty_u16(0)  # 오류 발생 시 음소거
            return False
    
    def play_continuous(self, frequency=2000):
        """연속 비프음 시작"""
        # 이미 재생 중인 멜로디가 있으면 중지
        if not self._stop_all_threads():
            print("[Buzzer] SAFETY: Cannot play continuous - thread still active")
            return False
        
        if not self._initialized:
            return False
            
        try:
            print(f"[Buzzer] Starting continuous beep at {frequency}Hz")
            self.pwm.freq(frequency)
            self.pwm.duty_u16(32767)
            self.is_continuous = True
            return True
        except Exception as e:
            print(f"[Buzzer] Error in play_continuous: {e}")
            self.pwm.duty_u16(0)  # 오류 발생 시 음소거
            return False
    
    def stop(self):
        """모든 소리 중지 (멜로디, 비프음, 연속음 등 모든 스레드 정리)"""
        if not self._initialized:
            return False
            
        try:
            print("[Buzzer] Stopping all sound")
            # 모든 스레드 중지 (안전 우선)
            cleanup_success = self._stop_all_threads()
            
            # 모든 소리 중지 및 상태 초기화
            self.pwm.duty_u16(0)
            self.is_continuous = False
            
            if cleanup_success:
                print("[Buzzer] All stopped successfully")
            else:
                print("[Buzzer] Sound stopped, but thread cleanup incomplete")
            
            return cleanup_success
        except Exception as e:
            print(f"[Buzzer] Error in stop: {e}")
            return False
    
    def is_active(self):
        """현재 활성 상태인지 확인"""
        if not self._initialized:
            return False
            
        # 멜로디 스레드가 실행 중이거나 연속 모드이거나 소리가 나고 있으면 활성 상태
        is_melody_active = False
        with self._melody_thread_lock:
            is_melody_active = self._melody_thread is not None
            
        return is_melody_active or self.is_continuous or self.pwm.duty_u16() > 0
    
    def set_completion_callback(self, callback):
        """완료 콜백 설정"""
        self._completion_callback = callback
    
    def deinit(self):
        """리소스 해제 - 완전한 정리"""
        if not self._initialized:
            return False
            
        try:
            print("[Buzzer] Starting complete deinitialization")
            
            # 1단계: 모든 재생 중지 (스레드 정리 포함)
            self.stop()
            
            # 2단계: 스레드가 완전히 종료될 때까지 강제 대기
            max_wait = 12  # 12 × 25ms = 300ms 대기
            while max_wait > 0:
                with self._melody_thread_lock:
                    if self._melody_thread is None:
                        break
                print(f"[Buzzer] Waiting for thread cleanup... ({max_wait*25}ms left)")
                time.sleep_ms(25)  # IRQ 부하 감소
                max_wait -= 1
            
            # 3단계: 강제 변수 초기화 (최후의 수단)
            with self._melody_thread_lock:
                if self._melody_thread is not None:
                    print("[Buzzer] WARNING: Forcing thread cleanup")
                self._melody_thread = None
                self._melody_stop_flag = False
                self._current_melody_name = None
            
            # 4단계: 하드웨어 완전 해제
            try:
                self.pwm.duty_u16(0)
                time.sleep_ms(10)  # PWM 안정화 대기
                self.pwm.deinit()
                print("[Buzzer] PWM deinitialized")
            except Exception as e:
                print(f"[Buzzer] PWM deinit error: {e}")
            
            # 5단계: 상태 완전 초기화
            self._initialized = False
            self.is_continuous = False
            
            print("[Buzzer] Complete deinitialization finished")
            return True
            
        except Exception as e:
            print(f"[Buzzer] Error during deinitialization: {e}")
            # 에러가 발생해도 상태는 초기화
            self._initialized = False
            return False

    def beep_async(self, count=1, frequency=2000, duration_ms=100, interval_ms=100):
        """비동기 비프음 재생"""
        if not self._initialized:
            return False
        
        # 기존 재생 중지
        if not self._stop_all_threads():
            print("[Buzzer] SAFETY: Cannot start beep - thread still active")
            return False
        
        # beep을 위한 간단한 멜로디 생성
        beep_melody = []
        for i in range(count):
            beep_melody.append((frequency, duration_ms))
            if i < count-1:
                beep_melody.append((0, interval_ms))  # 쉼표
        
        # 스레드로 실행
        try:
            with self._melody_thread_lock:
                self._melody_stop_flag = False
                self._current_melody_name = "BEEP"
                self._melody_thread = _thread.start_new_thread(self._beep_thread_function, (beep_melody,))
            
            return True
        except Exception as e:
            print(f"[Buzzer] Error starting beep thread: {e}")
            return False

    def _beep_thread_function(self, beep_melody):
        """비프음 재생을 위한 스레드 함수"""
        if not self._initialized:
            return
            
        try:
            for note, duration_ms in beep_melody:
                # 중지 플래그 확인
                with self._melody_thread_lock:
                    if self._melody_stop_flag:
                        break
                
                if note > 0:
                    # 비프음 재생
                    if not self._initialized:
                        break
                    
                    try:
                        self.pwm.freq(note)
                        self.pwm.duty_u16(32767)
                    except (RuntimeError, OSError):
                        break
                    
                    # 지속시간을 청크로 나누어 중지 확인
                    total_chunks = max(1, int(duration_ms / 50))
                    chunk_ms = duration_ms / total_chunks
                    
                    for _ in range(total_chunks):
                        time.sleep_ms(int(chunk_ms))
                        with self._melody_thread_lock:
                            if self._melody_stop_flag:
                                break
                        if not self._initialized:
                            break
                    
                    # 중지 플래그 확인
                    with self._melody_thread_lock:
                        if self._melody_stop_flag or not self._initialized:
                            break
                    
                    try:
                        self.pwm.duty_u16(0)
                    except (RuntimeError, OSError):
                        break
                else:
                    # 쉼표 (무음)
                    total_chunks = max(1, int(duration_ms / 50))
                    chunk_ms = duration_ms / total_chunks
                    
                    for _ in range(total_chunks):
                        time.sleep_ms(int(chunk_ms))
                        with self._melody_thread_lock:
                            if self._melody_stop_flag:
                                break
                        if not self._initialized:
                            break
                
                # 중지 플래그 확인
                with self._melody_thread_lock:
                    if self._melody_stop_flag or not self._initialized:
                        break
            
            # 모든 소리 중지
            try:
                if self._initialized:
                    self.pwm.duty_u16(0)
            except Exception:
                pass
            
            # 스레드 변수 초기화
            with self._melody_thread_lock:
                self._melody_thread = None
                self._melody_stop_flag = False
                self._current_melody_name = None
            
            # 완료 콜백 호출 - IRQ 충돌 방지를 위해 제거됨
            # if self._completion_callback:
            #     self._completion_callback("COMPLETED")
                    
        except Exception as e:
            print(f"[Buzzer] Error in beep thread: {e}")
            try:
                if self._initialized:
                    self.pwm.duty_u16(0)
            except Exception:
                pass
            
            # 스레드 변수 초기화
            with self._melody_thread_lock:
                self._melody_thread = None
                self._melody_stop_flag = False
                self._current_melody_name = None

# 전역 버저 인스턴스
_buzzer = None

def init(pin=42):
    """버저 초기화"""
    global _buzzer
    # 기존 인스턴스가 있다면 정리 후 새로 생성
    if _buzzer is not None:
        try:
            _buzzer.stop()
            if hasattr(_buzzer, 'deinit'):
                _buzzer.deinit()
        except:
            pass
    
    # 항상 새 인스턴스 생성
    _buzzer = BuzzerController(pin)
    return _buzzer._initialized

def beep(count=1, frequency=2000, duration_ms=100, interval_ms=100):
    """비프음 재생"""
    global _buzzer
    if _buzzer is None:
        init()
    return _buzzer.beep(count, frequency, duration_ms, interval_ms)

def beep_async(count=1, frequency=2000, duration_ms=100, interval_ms=100):
    """비동기 비프음 재생"""
    global _buzzer
    if _buzzer is None:
        init()
    return _buzzer.beep_async(count, frequency, duration_ms, interval_ms)

def play_melody(melody_name, tempo=120):
    """멜로디 재생"""
    global _buzzer
    if _buzzer is None:
        init()
    return _buzzer.play_melody(melody_name, tempo)

def play_tone(frequency, duration_ms=500):
    """단일 톤 재생"""
    global _buzzer
    if _buzzer is None:
        init()
    return _buzzer.play_tone(frequency, duration_ms)

def play_continuous(frequency=2000):
    """연속 비프음 재생"""
    global _buzzer
    if _buzzer is None:
        init()
    return _buzzer.play_continuous(frequency)

def stop():
    """모든 소리 중지"""
    global _buzzer
    if _buzzer is None:
        return True
    return _buzzer.stop()

def is_active():
    """버저가 현재 활성 상태인지 확인"""
    global _buzzer
    if _buzzer is None:
        return False
    return _buzzer.is_active()

def set_completion_callback(callback):
    """버저 재생 완료 시 호출할 콜백 함수 설정"""
    global _buzzer
    if _buzzer is None:
        init()
    _buzzer.set_completion_callback(callback)

def deinit():
    """모든 리소스 완전 정리"""
    global _buzzer
    if _buzzer is None:
        return True
    
    try:
        print("[Buzzer] Global deinitialization starting")
        
        # 먼저 모든 재생 중지
        _buzzer.stop()
        
        # 충분한 시간을 주고 완전히 정리
        max_wait = 12  # 12 × 25ms = 300ms 대기
        while max_wait > 0:
            try:
                is_thread_active = _buzzer._melody_thread is not None
                if not is_thread_active:
                    break
            except:
                break
            time.sleep_ms(25)  # IRQ 부하 감소
            max_wait -= 1
        
        # 리소스 해제
        result = _buzzer.deinit()
        
        # 전역 변수 완전 정리
        _buzzer = None
        
        print("[Buzzer] Global deinitialization complete")
        return result
        
    except Exception as e:
        print(f"[Buzzer] Error in global deinit: {e}")
        _buzzer = None  # 에러가 발생해도 변수는 정리
        return False

# 모듈 사용 예시
if __name__ == "__main__":
    # 버저 초기화
    init(pin=42)
    print("Testing continuous beep...")
    
    # 연속 비프음 테스트
    play_continuous()
    time.sleep(1)
    stop()
    time.sleep(1)
    play_continuous()
    time.sleep(1)
    stop()
    time.sleep(1)
    
    print("Testing beep sequence...")
    # 비프음 시퀀스 테스트
    beep(count=3, frequency=1000, duration_ms=100, interval_ms=150)
    time.sleep(0.5)
    
    print("Testing melody...")
    # 멜로디 테스트
    play_melody("TWINKLE", tempo=120)
    time.sleep(5)
    
    # 재생 중지
    stop()
    
    # 리소스 정리
    deinit()
    print("Test completed")