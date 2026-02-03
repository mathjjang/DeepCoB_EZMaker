from machine import Pin
from time import sleep

# GPIO 14 핀을 디지털 출력으로 초기화

pin_39 = Pin(39, Pin.OUT)
pin_39.off()
pin_14 = Pin(14, Pin.OUT)
pin_14.off()  # 초기 상태: OFF

pin_46 = Pin(46, Pin.OUT)
pin_46.on()


for i in [21,47,48,38,40,41,2,1,3,42]:
  temp = Pin(i, Pin.OUT)
  temp.off()
