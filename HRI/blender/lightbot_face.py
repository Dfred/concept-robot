#
# A few things to remember:
#  * defining classes in toplevel scripts (like here) leads to scope problems (imports...)
#

ADDR_EMO=("141.163.186.16",1110)
ADDR_VIS=("localhost", '/tmp/vision')
PREFIX="OB"
#AU_MAP= {"O" : { "": , },
#       	"C" : { "": , },
#         "E" : { "": , },
#         "A" : { "": , },
#         "N" : { "": , }
#        }
#



if not hasattr(GameLogic, "emo_client"):
	# for init, imports are done on demand since the standalone BGE has issues.
	import sys
	print "LIGHTBOT face synthesis, using python version:", sys.version

	import comm

	import logging
	logging.basicConfig(level=logging.WARNING, format=comm.FORMAT)

	import emo_client
	import vision_client
	GameLogic.emo_client = emo_client.EmoClient(ADDR_EMO)
	GameLogic.vision_client = vision_client.VisionClient(ADDR_VIS)

	objs = GameLogic.getCurrentScene().objects
	GameLogic.eyes = (objs[PREFIX+"eye-R"], objs[PREFIX+"eye-L"])
	GameLogic.empty_e = objs[PREFIX+"Empty-eyes"]
	GameLogic.eYorient = 0.0

	cont = GameLogic.getCurrentController()
	cont.activate(cont.actuators["- wakeUp -"])

else:
	import comm
	comm.loop(0.01, count=1)
	# setting focus point for the eyes
	if GameLogic.vision_client and GameLogic.vision_client.connected:
		GameLogic.empty_e.worldPosition = GameLogic.vision_client.focus_pos
	
cont= GameLogic.getCurrentController()
own = cont.owner

# eyelid correction
tmp = float(GameLogic.eYorient) + .505
own['frame'] = 41 - tmp*50
#print tmp, own['frame'], cont.actuators
act = cont.actuators["eyelids-gaze-follow"]
act.frame = own['frame']
cont.activate(act)
