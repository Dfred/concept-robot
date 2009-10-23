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
	GameLogic.gaze_client = client_gaze.GazeClient()
	
	objs = GameLogic.getCurrentScene().objects
	GameLogic.eyes = (objs[PREFIX+"eye-R"], objs[PREFIX+"eye-L"])
	GameLogic.empty_e = objs[PREFIX+"Empty-eyes"]

	cont = GameLogic.getCurrentController()
	cont.activate(cont.actuators["- wakeUp -"])


import comm

cont= GameLogic.getCurrentController()
own = cont.owner

if not hasattr(GameLogic, "gaze_client"):
	try:
		initialize()
	except Exception, e:
		print e
		cont.activate(cont.actuators["QUITTER"])
	
comm.loop(count=1) # TODO: check that ?!
# setting focus point for the eyes
if GameLogic.gaze_client and GameLogic.gaze_client.connected:
		GameLogic.empty_e.worldPosition = GameLogic.gaze_client.focus_pos
	

# eyelid correction
tmp = float(GameLogic.eyes[0].orientation[2][1]) + .505
own['frame'] = 41 - tmp*50
#print tmp, own['frame'], cont.actuators
act = cont.actuators["eyelids-gaze-follow"]
act.frame = own['frame']
cont.activate(act)