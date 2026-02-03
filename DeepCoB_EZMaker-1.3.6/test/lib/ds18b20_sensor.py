"""
DS18B20 Water Temperature Sensor Library for MicroPython
=========================================================

DS18B20 1-Wire 방식 수중 온도 센서 MicroPython 드라이버 라이브러리

주요 기능:
- 1-Wire 프로토콜 통신
- 온도 측정 (-55°C ~ +125°C)
- 다중 센서 지원 (하나의 핀에 여러 센서 연결 가능)
- 센서 자동 스캔
- 12비트 해상도 (0.0625°C)

사용 예:
    from machine import Pin
    from ds18b20_sensor import WaterTempSensor
    
    sensor = WaterTempSensor(pin=21)
    print(f"센서 개수: {sensor.get_sensor_count()}")
    
    temp = sensor.read_temp()
    print(f"온도: {temp:.2f} C")

연결:
- DATA (D0) -> GPIO 21
- VCC, GND
- 4.7kΩ 풀업 저항 필요 (DATA - VCC 사이)

참고:
- Maxim Integrated DS18B20 Digital Thermometer
- MicroPython onewire, ds18x20 모듈 사용
"""

from machine import Pin
import onewire
import ds18x20
import time

class WaterTempSensor:
    """DS18B20 수중 온도 센서 드라이버"""
    
    def __init__(self, pin):
        self.pin = pin
        self.ow = onewire.OneWire(Pin(pin))
        self.ds = ds18x20.DS18X20(self.ow)
        self.roms = []
        self.scan()
        
    def scan(self):
        """연결된 센서 스캔"""
        self.roms = self.ds.scan()
        return len(self.roms)
    
    def get_sensor_count(self):
        """연결된 센서 개수"""
        return len(self.roms)
    
    def get_sensor_ids(self):
        """센서 ID 목록 (ROM 주소)"""
        return [self._rom_to_hex(rom) for rom in self.roms]
    
    def _rom_to_hex(self, rom):
        """ROM을 16진수 문자열로 변환"""
        return ''.join('{:02X}'.format(b) for b in rom)
    
    def read_temp(self, index=0):
        """온도 읽기 (섭씨)"""
        if not self.roms:
            return None
        if index >= len(self.roms):
            return None
            
        self.ds.convert_temp()
        time.sleep_ms(750)  # 변환 대기 (12bit 해상도)
        
        return self.ds.read_temp(self.roms[index])
    
    def read_all_temps(self):
        """모든 센서 온도 읽기"""
        if not self.roms:
            return []
            
        self.ds.convert_temp()
        time.sleep_ms(750)
        
        temps = []
        for rom in self.roms:
            try:
                temp = self.ds.read_temp(rom)
                temps.append(temp)
            except:
                temps.append(None)
        return temps

