from camera import Camera, GrabMode, PixelFormat, FrameSize
import time
import array

cam = Camera(
    data_pins=[11,9,8,10,12,18,17,16],
    vsync_pin=6,
    href_pin=7,
    sda_pin=4,
    scl_pin=5,
    pclk_pin=13,
    xclk_pin=15,
    xclk_freq=20000000,
    powerdown_pin=-1,
    reset_pin=-1,
)
cam.reconfigure(pixel_format=PixelFormat.JPEG,frame_size=FrameSize.QVGA,grab_mode=GrabMode.LATEST, fb_count=2)
cam.set_vflip(True)
cam.set_hmirror(True)
cam.init()
time.sleep(1)
buf = cam.capture()
img = array.array('B', buf)
print('img size: ', len(img))
cam.deinit()
