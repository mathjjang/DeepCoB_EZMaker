# 버저 모듈 예제 

ESP32에서 버저(쉴드 상 PWM 발생기)를 사용하는 다양한 예제 코드입니다.

## 샘플 파일 목록

1. **sample1.py**: 기본 비프음 재생
2. **sample2.py**: 내장 멜로디 재생 
3. **sample3.py**: 사용자 정의 멜로디 만들기
4. **sample4.py**: 효과음 재생
5. **sample5.py**: 단일 음표 및 톤 재생
6. **sample6.py**: 재생 중지 및 리소스 정리
7. **runner.py**: 모든 예제를 함수로 실행할 수 있는 종합 실행기

## 사용 방법

### 방법 1: 직접 실행 (권장)
MicroPython에서 예제 파일을 직접 실행합니다.
```python
%Run -c $EDITOR_CONTENT
```

### 방법 2: 모듈 임포트 후 run() 함수 사용
각 모듈의 run() 함수를 호출하여 실행합니다.
```python
import buzzer_example.sample1 as s1
s1.run()  # 반복 실행 가능
```

### 방법 3: runner.py 모듈 사용
종합 실행기를 통해 모든 예제를 실행할 수 있습니다.
```python
import buzzer_example.runner as buzzer_runner
buzzer_runner.run_sample1()  # 샘플 1 실행
buzzer_runner.run_sample2()  # 샘플 2 실행
# ...
```

## 중요 사항

- **PWM 핀**: 버저는 GPIO 42번 핀에 연결되어 있습니다.
- **리소스 관리**: 모든 예제는 실행 후 리소스를 해제합니다 (`buzzer_obj.deinit()` 호출).
- **스레드 안전성**: sample6.py는 스레드를 활용한 예제이므로 주의가 필요합니다.
- **Ctrl+C 처리**: 모든 예제는 Ctrl+C 키 입력으로 안전하게 중단할 수 있습니다.

## 문제 해결

실행 중 오류가 발생하면:
1. `buzzer.reset_instance()` 호출로 싱글톤 인스턴스 초기화
2. run() 함수 또는 runner.py의 함수를 사용하여 재실행 