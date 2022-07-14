#### Server.py description####
#### Author: Hans Bethge and Patrick Lüdeke
#### Description: Serial communication between Raspberry Pi 4 and Openbuilds BlackBox Motion Control System (MotionController) and network access of these function via FastAPI 
#### Required libraries:
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from time import sleep
from fastapi.logger import logger
import serial 
import logging

#### G-Code Functions #####
def waitForOK():
   #### MotionController: Confirmation of received command 
   time = 0.0
   while time < 30.0:
      if serial.inWaiting():
         response = serial.readline()
         #print(response)
         if response == str.encode("ok\r\n"):
            return True
      else:
         time = time + 0.1
         sleep(0.1)
   return False

def waitForIdle():
   #### MotionController: Confirmation of reaching new position
   sleep(0.1)
   time = 0.0
   while time < 30.0:
      serial.write(str.encode('$?\n'))
      sleep(0.1)
      time = time + 0.1
      while serial.inWaiting():
         response = serial.readline()
         #print(response)
         if response.decode().find("Idle") != -1:
            return

def unlock():
   #### MotionController: unlock 
   serial.write(str.encode("$X\n"))

def zeroXYZ ():
   #### MotionController: set new coordinate system
   serial.write(str.encode("G10 P1 L20 X0 Y0 Z0\n"))

def goToHome():
   #### MotionController: Homeing to limit switches 
   serial.write(str.encode("$H\n"))

def setLight(turnOn):
   #### MotionController: turn 24v-Relay/lights on or off
   if turnOn:
      serial.write(str.encode("M8\n"))
   else:
      serial.write(str.encode("M9\n"))

def moveX(steps):
   #### MotionController: relative motion in X axis
   serial.write(str.encode("G91 X{0}\n".format(steps)))

def moveY(steps):
   #### MotionController: relative motion in Y axis
   serial.write(str.encode("G91 Y{0}\n".format(steps)))

def moveZ(steps):
   #### MotionController: relative motion in Z axis
   serial.write(str.encode("G91 Z{0}\n".format(steps)))

def goToX(pos):
   #### MotionController: Absolute positioning of X axis
   serial.write(str.encode("G90 X{0}\n".format(pos)))

def goToY(pos):
   #### MotionController: Absolute positioning of Y axis
   serial.write(str.encode("G90 Y{0}\n".format(pos)))

def goToZ(pos):
   #### MotionController: Absolute positioning of Z axis
   serial.write(str.encode("G90 Z{0}\n".format(pos)))

def goToXY(xpos,ypos):
   #### MotionController: Absolute positioning of X & Y axes simultaneously
   serial.write(str.encode("G90 X{0} Y{1}\n".format(xpos,ypos)))

def goToXYZ(xpos,ypos,zpos):
   #### MotionController: Absolute positioning of X & Y & Z axes simultaneously
   serial.write(str.encode("G90 X{0} Y{1} Z{2}\n".format(xpos,ypos,zpos)))

gunicorn_logger = logging.getLogger('gunicorn.error')
logger.handlers = gunicorn_logger.handlers
if __name__ != "main":
    logger.setLevel(gunicorn_logger.level)
else:
    logger.setLevel(logging.INFO) #logging.DEBUG

#### Open Serial port and start API
serial = serial.Serial('/dev/ttyUSB0', 115200)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/unlock")
#### FASTAPI: Unlock MotionController
async def pathUnlock():
   unlock()
   waitForOK()
   return {"message": "Controller unlocked!"}

@app.get("/api/v1/home")
#### FASTAPI: Set new origin of the coordinate system after Homeing of MotionController
async def pathHome():
   print("Homing...")
   goToHome()
   waitForOK()
   waitForIdle()
   print("Zeroing...")
   zeroXYZ()
   waitForOK()
   waitForIdle()
   return {"message": "Going Home!"}

@app.get("/api/v1/DiffuseRingLight/on")
#### FASTAPI: Turn Lights on
async def pathLightOn():
   print("Turning DiffuseRingLight on!")
   setLight(True)
   print("Waiting for OK...")
   if waitForOK() == True:
      return {"message": "Turning DiffuseRingLight on!"}
   else:
      return {"message": "Waiting for OK timed out. Is device unlocked?"}

@app.get("/api/v1/DiffuseRingLight/off")
#### FASTAPI: Turn Lights off
async def pathLightOff():
   setLight(False)
   if waitForOK() == True:
      return {"message": "Turning DiffuseRingLight off!"}
   else:
      return {"message": "Waiting for OK timed out. Is device unlocked?"}

@app.get("/api/v1/axis/x/rel/{steps}")
#### FASTAPI: Move X Axis relative
async def pathXStep(steps):
   print("Moving X axis by {0} steps.".format(steps))
   moveX(steps)
   waitForOK()
   waitForIdle()
   return {"message": "Moving X axis by {0} steps.".format(steps)}

@app.get("/api/v1/axis/y/rel/{steps}")
#### FASTAPI: Move Y Axis relative
async def pathYStep(steps):
   print("Moving Y axis by {0} steps.".format(steps))
   moveY(steps)
   waitForOK()
   waitForIdle()
   return {"message": "Moving Y axis by {0} steps.".format(steps)}

@app.get("/api/v1/axis/z/rel/{steps}")
#### FASTAPI: Move Z Axis relative
async def pathZStep(steps):
   print("Moving Z axis by {0} steps.".format(steps))
   moveZ(steps)
   waitForOK()
   waitForIdle()
   return {"message": "Moving Z axis by {0} steps.".format(steps)}

@app.get("/api/v1/axis/x/abs/{pos}")
#### FASTAPI: Move X Axis absolute
async def pathXGoTo(pos):
   print("Going to X pos {0}.".format(pos))
   goToX(pos)
   waitForOK()
   waitForIdle()
   return {"message": "Going to X pos {0}.".format(pos)}

@app.get("/api/v1/axis/y/abs/{pos}")
#### FASTAPI: Move Y Axis absolute
async def pathYGoTo(pos):
   print("Going to Y pos {0}.".format(pos))
   goToY(pos)
   waitForOK()
   waitForIdle()
   return {"message": "Going to Y pos {0}.".format(pos)}

@app.get("/api/v1/axis/z/abs/{pos}")
#### FASTAPI: Move Z Axis absolute
async def pathZGoTo(pos):
   #### Travel limits of added Z-Axis
   if -60<int(pos)<0.1:
      print("Going to Z pos {0}.".format(pos))
      goToZ(pos)
      waitForOK()
      waitForIdle()
      return {"message": "Going to Z pos {0}.".format(pos)}
   else:
      print("Z out of possible range")
      return {"message": "Z out of possible range"}

@app.get("/api/v1/axis/xy/abs/{xpos}/{ypos}")
#### FASTAPI: Move X & Y Axes absolute simultaneously
async def pathXYGoTo(xpos,ypos):
   print("Going to X pos {0} and Y pos {1}.".format(xpos,ypos))
   goToXY(xpos,ypos)
   waitForOK()
   waitForIdle()
   return {"message": "Going to X pos {0} and Y pos {1}.".format(xpos,ypos)}

@app.get("/api/v1/axis/xyz/abs/{xpos}/{ypos}/{zpos}")
#### FASTAPI: Move X & Y & Z Axes absolute simultaneously
async def pathXYZGoTo(xpos,ypos,zpos):
   print("Going to X pos {0} and Y pos {1} and Z pos {2}.".format(xpos,ypos,zpos))
   goToXYZ(xpos,ypos,zpos)
   waitForOK()
   waitForIdle()
   return {"message": "Going to X pos {0} and Y pos {1} and Z pos {2}.".format(xpos,ypos,zpos)}
