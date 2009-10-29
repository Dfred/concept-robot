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

	import client_gaze
	GameLogic.client_gaze = client_gaze.GazeClient()
	
	import client_face
	GameLogic.client = client_face.FaceClient()
	
	objs = GameLogic.getCurrentScene().objects
	GameLogic.eyes = (objs[PREFIX+"eye-R"], objs[PREFIX+"eye-L"])
	GameLogic.empty_e = objs[PREFIX+"Empty-eyes"]

	cont = GameLogic.getCurrentController()
	cont.activate(cont.actuators["- wakeUp -"])
	

def set_AUs(args):
	pass

import comm

cont= GameLogic.getCurrentController()
own = cont.owner

if not hasattr(GameLogic, "client_gaze"):
#	try:
	initialize()
#	except Exception, e:
#		print "exception received:",e
#		cont.activate(cont.actuators["QUITTER"])
	
comm.loop(count=1) # TODO: check that ?!
# setting focus point for the eyes
if GameLogic.client_gaze and GameLogic.client_gaze.connected:
		GameLogic.empty_e.worldPosition = GameLogic.client_gaze.focus_pos
	

# eyelid correction
tmp = float(GameLogic.eyes[0].orientation[2][1]) + .505
own['frame'] = 41 - tmp*40
#print tmp, own['frame'], cont.actuators
act = cont.actuators["eyelids-gaze-follow"]
act.frame = own['frame']
cont.activate(act)