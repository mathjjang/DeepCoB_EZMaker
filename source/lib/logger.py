# logger.py - 간단한 로깅 시스템
import time
import sys
import os

# 상위 경로 추가 (MicroPython 호환)
sys.path.append('../')  # 상위 디렉토리 경로 직접 지정
import config

# 로그 레벨 정의
DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40
CRITICAL = 50

# 현재 로그 레벨 (이 레벨 이상만 출력)
try:
    current_level = config.current_level
except AttributeError:
    # config에 current_level이 없을 경우 기본값으로 INFO 사용
    current_level = INFO
    print("Warning: config.current_level not found, using default INFO level")

# ANSI 색상 코드 (REPL 또는 시리얼 콘솔에서 색상 표시)
COLORS = {
    DEBUG: '\033[94m',     # 파란색
    INFO: '\033[30m',      # 검정색
    WARNING: '\033[93m',   # 노란색
    ERROR: '\033[91m',     # 빨간색
    CRITICAL: '\033[95m',  # 보라색
    'RESET': '\033[0m'     # 리셋
}

# 로그 레벨 이름
LEVEL_NAMES = {
    DEBUG: 'DEBUG',
    INFO: 'INFO',
    WARNING: 'WARNING',
    ERROR: 'ERROR',
    CRITICAL: 'CRITICAL'
}

# 로그 출력 활성화/비활성화 설정
use_colors = True
show_time = True
show_module = True

def set_level(level):
    """로그 레벨 설정"""
    global current_level
    current_level = level

def log(level, message, module=None):
    """기본 로그 함수"""
    if level < current_level:
        return
    
    # 현재 시간 포맷팅
    timestamp = ""
    if show_time:
        t = time.localtime()
        timestamp = f"{t[3]:02d}:{t[4]:02d}:{t[5]:02d} "
    
    # 모듈명 포맷팅
    module_str = ""
    if show_module and module:
        module_str = f"[{module}] "
    
    # 로그 레벨 이름
    level_name = LEVEL_NAMES.get(level, 'UNKNOWN')
    
    # 색상 적용
    if use_colors:
        color = COLORS.get(level, COLORS['RESET'])
        print(f"{timestamp}{color}{level_name}: {module_str}{message}{COLORS['RESET']}")
    else:
        print(f"{timestamp}{level_name}: {module_str}{message}")

# 편의 함수
def debug(message, module=None):
    log(DEBUG, message, module)

def info(message, module=None):
    log(INFO, message, module)

def warning(message, module=None):
    log(WARNING, message, module)

def error(message, module=None):
    log(ERROR, message, module)

def critical(message, module=None):
    log(CRITICAL, message, module) 