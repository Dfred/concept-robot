#
# A few things to remember:
#  * defining classes in toplevel scripts (like here) leads to scope problems (imports...)
#

PREFIX="OB"
	
def	initialize():
	# for init, imports are done on demand since the standalone BGE has issues.
	import sys
	print "LIGHTBOT face synthesis, using python version:", sys.version

	import logging
	logging.basicConfig(level=logging.WARNING, format=comm.FORMAT)

	objs = GameLogic.getCurrentScene().objects
	GameLogic.eyes = (objs[PREFIX+"eye-R"], objs[PREFIX+"eye-L"])
	GameLogic.empty_e = objs[PREFIX+"Empty-eyes"]

	import conf
	import gaze
	GameLogic.srv_gaze = gaze.Gaze(conf.gaze_addr)
	
#	import client_face
#	GameLogic.client = client_face.FaceClient()

	GameLogic.initialized = True	
	cont = GameLogic.getCurrentController()
	cont.activate(cont.actuators["- wakeUp -"])
	

def set_AUs(args):
	pass

import comm

cont= GameLogic.getCurrentController()
own = cont.owner

if not hasattr(GameLogic, "initialized"):
	try:
		initialize()
	except Exception, e:
		print "exception received:",e
		cont.activate(cont.actuators["QUITTER"])
	
comm.loop(.01, count=1) # block for max 10ms and 1 packet
# setting focus point for the eyes
if hasattr(GameLogic, "srv_gaze") and GameLogic.srv_gaze.connected:
		GameLogic.empty_e.worldPosition = GameLogic.client_gaze.focus_pos


# eyelid correction
tmp = float(GameLogic.eyes[0].orientation[2][1]) + .505
own['frame'] = 41 - tmp*40
#print tmp, own['frame'], cont.actuators
act = cont.actuators["eyelids-gaze-follow"]
act.frame = own['frame']
cont.activate(act)