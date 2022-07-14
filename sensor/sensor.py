#### Sensor.py description####
#### Author: Hans Bethge and Patrick Lüdeke
#### Description: Read sensors with Raspberry Pi 4 and network access of these function & data via FastAPI 
#### Required libraries:
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from time import sleep
from fastapi.logger import logger
from picamera import PiCamera
from datetime import datetime, timedelta
from fastapi.responses import FileResponse, JSONResponse
import picamera
from picamera import mmal, mmalobj, exc
from picamera.mmalobj import to_rational
import time
import logging
import glob
import serial
import cv2
import numpy as np
from flirpy.camera.lepton import Lepton

try:
  from queue import Queue
except ImportError:
  from Queue import Queue
import platform


#### Set PiCamera HQ Gain controll
#### Credits to github.com/rwb27/set_picamera_gain.py
MMAL_PARAMETER_ANALOG_GAIN = mmal.MMAL_PARAMETER_GROUP_CAMERA + 0x59
MMAL_PARAMETER_DIGITAL_GAIN = mmal.MMAL_PARAMETER_GROUP_CAMERA + 0x5A
def setCameraGain(camera, gain, value):
    """Set the analog gain of a PiCamera.
    camera: the picamera.PiCamera() instance you are configuring
    gain: either MMAL_PARAMETER_ANALOG_GAIN or MMAL_PARAMETER_DIGITAL_GAIN
    value: a numeric value that can be converted to a rational number.
    """
    if gain not in [MMAL_PARAMETER_ANALOG_GAIN, MMAL_PARAMETER_DIGITAL_GAIN]:
        raise ValueError("The gain parameter was not valid")
    ret = mmal.mmal_port_parameter_set_rational(camera._camera.control._port, 
                                                    gain,
                                                    to_rational(value))
    if ret == 4:
        raise exc.PiCameraMMALError(ret, "Are you running the latest version of the userland libraries? Gain setting was introduced in late 2017.")
    elif ret != 0:
        raise exc.PiCameraMMALError(ret)

def setCameraAnalogGain(camera, value):
    """Set the gain of a PiCamera object to a given value."""
    setCameraGain(camera, MMAL_PARAMETER_ANALOG_GAIN, value)

def setCameraDigitalGain(camera, value):
    """Set the digital gain of a PiCamera object to a given value."""
    setCameraGain(camera, MMAL_PARAMETER_DIGITAL_GAIN, value)
#### Initialize PiCamera HQ with corresponsing device settings
def camera_initializing():
   camera.resolution = (4054, 3040) 
   time.sleep(1)
   camera.awb_mode = 'off'
   time.sleep(1)
   camera.awb_gains = (3.3,1.5) #### Fixed Gain settings (R,B)
   camera.exposure_mode = 'off'
   time.sleep(1)
   camera.shutter_speed = 2500
   time.sleep(1)
   print("Attempting to set analogue gain to 1")
   setCameraAnalogGain(camera, 1)
   print("Attempting to set digital gain to 1")
   setCameraDigitalGain(camera, 1)
   sleep(2)

def takePhoto(name):
   camera.capture('./' + name)

def takeNPArrayImage(name):
    #### Capture Image as NP-Array
    output = np.empty((3040 * 4064 * 3,), dtype=np.uint8)
    camera.capture(output, 'bgr')
    output = output.reshape(3040, 4064, 3)
    output = output[:3040, :4054, :]
    cv2.imwrite('./temp.png', output)

camera = PiCamera()
camera_initializing()


gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
if __name__ != "main":
    logger.setLevel(gunicorn_logger.level)
else:
    logger.setLevel(logging.DEBUG)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#### Identification of peripheral USB-Controller (Wemos with Laser-Distance-Sensor and other light sources)
wemosSerial = None
def getWemosSerial():
    global wemosSerial
    if wemosSerial != None:
        print("wemosSerial is none")
        wemosSerial.write(b"WHO.IS?\n")
        deviceName = wemosSerial.readline()
        print(deviceName)
        if deviceName.startswith(b'LIGHT AND LASER'):
            return wemosSerial

    print(glob.glob("/dev/ttyUSB*"))
    for device in glob.glob("/dev/ttyUSB*"):
        try:
            print(device)
            currentDevice = serial.Serial(device,115200)
            currentDevice.write(b"WHO.IS?\n")
            deviceName = currentDevice.readline()
            print(deviceName)
            if deviceName.startswith(b'LIGHT AND LASER'):
                print("Found device")
                wemosSerial = currentDevice
                return wemosSerial
        except Exception as e:
            print(e)
            continue

    raise HTTPException(status_code=500, detail="Wemos USB Device for Distance sensor and Ring light not found!")

#### Identification of peripheral USB-Controller (Wemos with Mini-Spectrometer)
specSerial = None
def getSpecSerial():
    global specSerial

    if specSerial != None:
        print("specSerial is none")
        specSerial.write(b"WHO.IS?\n")
        deviceName = specSerial.readline()
        print(deviceName)
        if deviceName.startswith(b'SPECTROMETER'):
            return specSerial

    print(glob.glob("/dev/ttyUSB*"))
    for device in glob.glob("/dev/ttyUSB*"):
        try:
            print(device)
            currentDevice = serial.Serial(device,115200)
            currentDevice.write(b"WHO.IS?\n")
            deviceName = currentDevice.readline()
            print(deviceName)
            if deviceName.startswith(b'SPECTROMETER'):
                print("Found device")
                specSerial = currentDevice
                return specSerial
        except Exception as e:
            print(e)
            continue

    raise HTTPException(status_code=500, detail="Spectrometer USB Device not found!")
    
#### Identification of peripheral USB-Controller (PureThermal-Board)
def getThermalDevice():
    for i in range(1,11,1):
        cv2_cap = cv2.VideoCapture(i)
        print("Camera video port:", i)
        if cv2_cap.isOpened():
            return cv2_cap
    raise HTTPException(status_code=500, detail="Thermal Camera USB Device not found!")

def setSpecWhiteLED(turnOn, serial):
   #### Turn White LED of Spectrometer/C128880 Breakout Board on/off
   if turnOn:
      serial.write(str.encode("SPEC.WHITE_LED? 1\n"))
   else:
      serial.write(str.encode("SPEC.WHITE_LED? 0\n"))

def setSpecUVLED(turnOn, serial):
   #### Turn UV LED of Spectrometer/C128880 Breakout Board on/off
   if turnOn:
      serial.write(str.encode("SPEC.UV_LED? 1\n"))
   else:
      serial.write(str.encode("SPEC.UV_LED? 0\n"))

def setLightWhiteLED(turnOn, serial):
   #### Turn White LEDs of Ringlight on/off
   if turnOn:
      serial.write(str.encode("LIGHT.WHITE_LED? 1\n"))
   else:
      serial.write(str.encode("LIGHT.WHITE_LED? 0\n"))

def setLightUVLED(turnOn, serial):
   #### Turn UV LEDs of Ringlight on/off
   if turnOn:
      serial.write(str.encode("LIGHT.UV_LED? 1\n"))
   else:
      serial.write(str.encode("LIGHT.UV_LED? 0\n"))

def setLightRedLED(turnOn, serial):
   #### Turn Red LEDs of Ringlight on/off
   if turnOn:
      serial.write(str.encode("LIGHT.RED_LED? 1\n"))
   else:
      serial.write(str.encode("LIGHT.RED_LED? 0\n"))



@app.get("/api/v1/thermal/Test")
#### Get raw thermal image as tif
async def getThermalTest():
    try:
     cam = Lepton()
     image = cam.grab()
     cv2.imwrite("thermal_temp.tif", image.astype(np.uint16))
    except Exception as e:
     raise HTTPException(status_code=500, detail="Failed to capture thermal image!" + e)
    finally:
     cam.close()
     sleep(1)

    return FileResponse("thermal_temp.tif")

@app.get("/api/v1/thermal/jpg")
#### FASTAPI: Get raw thermal image as false color jpg
async def getThermalJpg():
    try:
     cam = Lepton()
     img = cam.grab().astype(np.float32)
     img= img/100-273.15
     img = cv2.rotate(img,cv2.ROTATE_180)
     # Rescale to 8 bit
     img = 255*(img - img.min())/(img.max()-img.min())
    
     # Apply colourmap - try COLORMAP_JET if INFERNO doesn't work.
     # You can also try PLASMA or MAGMA
     img_col = cv2.applyColorMap(img.astype(np.uint8), cv2.COLORMAP_INFERNO)

     cv2.imwrite("thermal_temp.jpg", img_col)
    except Exception as e:
     print(e)
     raise HTTPException(status_code=500, detail="Failed to capture thermal image!")
    finally:
     cam.close()
     sleep(1)

    return FileResponse("thermal_temp.jpg")
    
@app.get("/api/v1/rgb/jpg")
#### FASTAPI: Get PiCamera HQ image as jpg
async def getRgbJpg():
    takePhoto("temp.jpg")
    return FileResponse("temp.jpg")


@app.get("/api/v1/rgb/png")
#### FASTAPI: Get PiCamera HQ image as png
async def getRgbPng():
    takeNPArrayImage("temp.png")
    return FileResponse("temp.png")

@app.get("/api/v1/spec/led/white/on")
#### FASTAPI: Turn White LED of spectrometer on
async def setSpecWhiteLEDOn():
    print("Turning white led on...")
    serial = getSpecSerial()
    setSpecWhiteLED(True, serial)
    return {"message": "Turning white led on!"}

@app.get("/api/v1/spec/led/white/off")
#### FASTAPI: Turn White LED of spectrometer off
async def setSpecWhiteLEDOff():
    print("Turning white led off...")
    serial = getSpecSerial()
    setSpecWhiteLED(False, serial)
    return {"message": "Turning white led off!"}

@app.get("/api/v1/spec/led/uv/on")
#### FASTAPI: Turn UV LED of spectrometer on
async def setSpecUVLEDOn():
    print("Turning UV led on...")
    serial = getSpecSerial()
    setSpecUVLED(True, serial)
    return {"message": "Turning UV led on!"}

@app.get("/api/v1/spec/led/uv/off")
#### FASTAPI: Turn UV LED of spectrometer off
async def setSpecUVLEDOff():
    print("Turning UV led off...")
    serial = getSpecSerial()
    setSpecUVLED(False,serial)
    return {"message": "Turning UV led off!"}

@app.get("/api/v1/light/white/on")
#### FASTAPI: Turn White LEDs of RingLight on
async def setLightWhiteLEDOn():
    print("Turning white led on...")
    serial = getWemosSerial()
    setLightWhiteLED(True, serial)
    return {"message": "Turning white led on!"}

@app.get("/api/v1/light/white/off")
#### FASTAPI: Turn White LEDs of RingLight off
async def setLightWhiteLEDOff():
    print("Turning white led off...")
    serial = getWemosSerial()
    setLightWhiteLED(False, serial)
    return {"message": "Turning white led off!"}

@app.get("/api/v1/light/uv/on")
#### FASTAPI: Turn UV LEDs of RingLight on
async def setLightUVLEDOn():
    print("Turning UV led on...")
    serial = getWemosSerial()
    setLightUVLED(True, serial)
    return {"message": "Turning UV led on!"}

@app.get("/api/v1/light/uv/off")
#### FASTAPI: Turn UV LEDs of RingLight off
async def setLightUVLEDOff():
    print("Turning UV led off...")
    serial = getWemosSerial()
    setLightUVLED(False, serial)
    return {"message": "Turning UV led off!"}

@app.get("/api/v1/light/red/on")
#### FASTAPI: Turn Red LEDs of RingLight on
async def setLightRedLEDOn():
    print("Turning RED led on...")
    serial = getWemosSerial()
    setLightRedLED(True, serial)
    return {"message": "Turning RED led on!"}

@app.get("/api/v1/light/red/off")
#### FASTAPI: Turn Red LEDs of RingLight off
async def setLightRedLEDOff():
    print("Turning RED led off...")
    serial = getWemosSerial()
    setLightRedLED(False, serial)
    return {"message": "Turning RED led off!"}

@app.get("/api/v1/laser/read")
#### FASTAPI: Read Laser-Distance-Sensor value
async def getLaserRead():
    print("Getting Laser Reads...")
    serial = getWemosSerial()
    serial.write(b"LASER.READ?\n")
    sdata = serial.readline()
    ##sdata = [int(p) for p in sdata.split(b",")]
    return [int(sdata)]

@app.get("/api/v1/spec/spec")
#### FASTAPI: Read Spectrometer Array
async def getSpec():
    print("Getting spec...")
    serial = getSpecSerial()
    serial.write(b"SPEC.READ?\n")
    sdata = serial.readline()
    sdata = [int(p) for p in sdata.split(b",")]
    return JSONResponse(content=sdata)


@app.get("/api/v1/spec/timing")
#### FASTAPI: Set Spectrometer timing
async def getSpecTiming():
    print("Getting spec timing...")
    serial = getSpecSerial()
    serial.write(b"SPEC.TIMING?\n")
    sdata = serial.readline()
    sdata = [int(p) for p in sdata.split(b",")]
    return JSONResponse(content=sdata)


@app.get("/api/v1/spec/integration/{msec}")
#### FASTAPI: Set Spectrometer integration time in milliseconds
async def setSpecIntegrationTime(msec):
    serial = getSpecSerial()
    print("Setting integration time to {:0.6f} seconds.".format(int(msec) / 1000.0))
    cmd = "SPEC.INTEG {:0.6f}\n".format(int(msec) / 1000.0)
    print(cmd)
    serial.write(cmd.encode('utf8'))
    return {"message": "Set integration time to {:0.6f} seconds.".format(int(msec) / 1000.0)}