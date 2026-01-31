# HeartRateMonitor.py
# 심박수 계산을 위한 헬퍼 클래스

from utime import ticks_diff, ticks_ms

class HeartRateMonitor:
    """A simple heart rate monitor that uses a moving window to smooth the signal and find peaks."""

    def __init__(self, sample_rate=100, window_size=20, smoothing_window=10):
        # 윈도우 크기 증가: 10 → 20, 평활화 윈도우: 5 → 10
        self.sample_rate = sample_rate
        self.window_size = window_size
        self.smoothing_window = smoothing_window
        self.samples = []
        self.timestamps = []
        self.filtered_samples = []
        self.last_heart_rates = []  # 최근 심박수 기록 저장
        self.max_rates_history = 5  # 최근 5개 측정값 저장

    def add_sample(self, sample):
        """Add a new sample to the monitor."""
        timestamp = ticks_ms()
        
        # 명확한 이상치 제거 (매우 큰 값이나 음수 값 무시)
        if sample < 0 or sample > 100000:
            return
            
        self.samples.append(sample)
        self.timestamps.append(timestamp)

        # 이동 평균 필터로 신호 평활화 개선
        if len(self.samples) >= self.smoothing_window:
            # 중앙값 기준 가중 평균 적용 (가운데 값에 더 높은 가중치)
            weights = [0.5 + 0.5 * (1 - abs(i - self.smoothing_window//2) / (self.smoothing_window//2)) 
                      for i in range(self.smoothing_window)]
            total_weight = sum(weights)
            
            smoothed_sample = sum(self.samples[-self.smoothing_window+i] * weights[i] 
                                 for i in range(self.smoothing_window)) / total_weight
            self.filtered_samples.append(smoothed_sample)
        else:
            self.filtered_samples.append(sample)

        # Maintain the size of samples and timestamps
        if len(self.samples) > self.window_size:
            self.samples.pop(0)
            self.timestamps.pop(0)
            self.filtered_samples.pop(0)

    def find_peaks(self):
        """Find peaks in the filtered samples with improved peak detection algorithm."""
        peaks = []

        if len(self.filtered_samples) < 5:  # 최소 5개 샘플 필요
            return peaks

        # 계산 기준 변경: 최근 데이터에 더 높은 가중치를 둔 동적 임계값
        recent_samples = self.filtered_samples[-self.window_size:]
        min_val = min(recent_samples)
        max_val = max(recent_samples)
        
        # 에지 케이스 처리: 노이즈가 매우 적은 경우
        if max_val - min_val < 100:  # 신호 변동이 너무 작으면 감지 민감도 증가
            threshold = min_val + (max_val - min_val) * 0.3  # 임계값 낮춤 (50% → 30%)
        else:
            threshold = min_val + (max_val - min_val) * 0.4  # 임계값 조정 (50% → 40%)

        # 첨두값(peak) 감지 알고리즘 개선
        for i in range(2, len(self.filtered_samples) - 2):
            # 더 엄격한 피크 감지: 전후 2개 샘플과 비교
            if (self.filtered_samples[i] > threshold and
                self.filtered_samples[i] > self.filtered_samples[i-1] and
                self.filtered_samples[i] > self.filtered_samples[i-2] and
                self.filtered_samples[i] > self.filtered_samples[i+1] and
                self.filtered_samples[i] > self.filtered_samples[i+2]):
                
                peak_time = self.timestamps[i]
                peaks.append((peak_time, self.filtered_samples[i]))

        return peaks

    def calculate_heart_rate(self, previous_bpm=None):
        """Calculate the heart rate in beats per minute (BPM) with improved consistency checks."""
        peaks = self.find_peaks()

        if len(peaks) < 2:
            return None  # Not enough peaks to calculate heart rate

        # 피크 간 간격 계산 및 이상치 제거
        intervals = []
        for i in range(1, len(peaks)):
            interval = ticks_diff(peaks[i][0], peaks[i - 1][0])
            
            # 비정상적으로 짧거나 긴 간격 제외 (0.3초~2초 범위만 허용)
            if 300 <= interval <= 2000:
                intervals.append(interval)
        
        # 유효한 간격이 부족하면 결과 없음
        if len(intervals) < 1:
            return None
            
        # 필터링된 간격으로 평균 계산
        average_interval = sum(intervals) / len(intervals)

        # 심박수 계산
        heart_rate = 60000 / average_interval  # BPM으로 변환
        
        # 심박수 범위 검증 (30~200 BPM 범위를 넘어가면 이상한 값으로 간주)
        if heart_rate < 30 or heart_rate > 200:
            if self.last_heart_rates and len(self.last_heart_rates) > 0:
                # 이전 유효한 값이 있으면 그 값 사용
                return self.last_heart_rates[-1]
            return None
            
        # 이전 측정값과의 급격한 변화 감지 및 필터링 (기존 코드)
        if previous_bpm and abs(heart_rate - previous_bpm) > 20:
            # 급격한 변화 감지 시 가중 평균 적용
            heart_rate = previous_bpm * 0.7 + heart_rate * 0.3
        
        # 최근 측정값 기록 업데이트
        self.last_heart_rates.append(heart_rate)
        if len(self.last_heart_rates) > self.max_rates_history:
            self.last_heart_rates.pop(0)
            
        # 최근 N개 측정값의 평균 반환하여 안정성 향상
        if len(self.last_heart_rates) >= 3:
            # 중앙값 기준 이상치 제거 후 평균 계산
            sorted_rates = sorted(self.last_heart_rates)
            median = sorted_rates[len(sorted_rates) // 2]
            valid_rates = [r for r in self.last_heart_rates if abs(r - median) <= 15]
            
            if valid_rates:
                return sum(valid_rates) / len(valid_rates)
        
        return heart_rate 