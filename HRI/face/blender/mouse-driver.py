#!/usr/bin/python

import Rasterizer as R

LOCAL_COORDINATES = 1
MF = (10, 5)		# set (x,y) mouse mouse_factor

# get controller
controller = GameLogic.getCurrentController()
# get the object this script is attached to
own = controller.owner
# Get sensor named Mouse
mouse = controller.sensors["Mouse"]

#R.showMouse(1)

# normalize mouse position
x = float(mouse.position[0])/R.getWindowWidth()
z = float(mouse.position[1])/R.getWindowHeight()
y = own.position[1]

# Set our eyes driver location but mapping scene origin to mouse origin
own.localPosition = ([ (x-.5)*MF[0], y, (-z+.5)*MF[1] ])
own['updated'] = True
