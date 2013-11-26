#!/usr/bin/python

from time import time

from utils.vision import CamUtils
from utils import conf
from utils.comm_CHLAS_ARAS import ChlasComm as Comm

conf.set_name('lighty')
try:
  conf.load()
except utils.conf.LoadException,e:
  filename, errmsg = e
  print (filename and filename+':' or ''), errmsg

import logging
from utils import comm, conf, LOGFORMATINFO
logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
LOG = logging.getLogger()

# Sends gaze packets to the CHLAS and chat the user if he's close enough

LOGFILE = "follow_face.log"
DB_STORY = [('happy',"Thanks!"),
            ('',"My name is Lighty and I am the 1st robot from Syntheligence."),
            ('',"I can display lots of facial expressions,"),
            ('',"which help people understand what I think."),
            ('',"I can also change my face,"),
            ('',"but you will need to ask my 2 fathers for this trick!"),
            ('',"That's all I can say for now..."),
            ('',"Bye bye!")]




if __name__ == "__main__":

  ##
  ## Define
  ##
  curr_face = None

  class User():
    """Represent an interaction with a user."""
    def __init__(self, pyvision_rect):
      self.found = time()
      self.seen = time()
      self.closer = None
      self.spoken = 0
      self.story_i = 0
      #TDL find user in LOGFILE from pyvision_rect

    def write_logFile(self, entry):
      """For further analysis."""
      with open(LOGFILE, 'a') as f:
        f.write(entry)

    def set_visible(self, area):
      self.seen = time()
      self.area = area

    ## tests

    def is_tooFar(self, ):
      self.area < 15000 
     
    def is_lost(self):
      return (time() - self.seen) > 3

    def is_listening(self):
      return self.story_i < len(DB_STORY)

    ## utterances

    def interact_lost(self):
      lost = time()
      write_logFile("%i;%i;%i;%i"% (self.found, lost, self.closer, self.spoken))

    def interact_disappear(self):
      comm_chlas.set_fExpression("worried", 2.0)
      self.dont_wait = True

    def interact_init(self):
      comm_chlas.set_instinct("enable:chat-gaze|chat-gaze:speaking")
      comm_chlas.set_instinct("blink:new-mental-state|blink:look-at-face")
      comm_chlas.set_text("Hello there!")

    def interact_too_far(self):
      if (time() - self.found) < 1:                     ## recently found
        comm_chlas.set_fExpression("squint")
        comm_chlas.set_text("Come closer so I can see you better..")
      elif (time() - self.found) > 5:                   ## didn't get closer
        comm_chlas.set_fExpression("smile", .25)
        comm_chlas.set_text("I won't bite you, I simply cannot!")
      elif (time() - self.found) > 10:                  ## last chance
        comm_chlas.set_fExpression("sad", .8)
        comm_chlas.set_text("Too bad.. I'll speak to you later then.")
      else:
        comm_chlas.set_fExpression("neutral", .8)
        comm_chlas.set_text("Too bad.. I'll speak to you later then.")
        comm_chlas.set_instinct("blink:new-mental-state|"
                                "blink:look-away-face")

    def interact_story(self):
      fe, txt = DB_STORY[self.story_i]
      comm_chlas.set_fExpression(fe)
      comm_chlas.set_text(txt)
      self.story_i += 1

    def interact_random(self):                                #TDL behaviour?
      pass

  def OnConnection():
    comm_chlas.set_fExpression("surprised", duration=0.3)
    comm_chlas.set_text("Oh I can see now!")
    comm_chlas.set_instinct("blink:new-mental-state|blink:expression-on")
    comm_chlas.sendDB_waitReply()

    comm_chlas.set_fExpression("neutral", duration=1.0)
    comm_chlas.set_instinct("blink:new-mental-state|blink:look-away-face")
    comm_chlas.sendDB_waitReply()

    cap.toggle_face_detection(True)
    cap.toggle_fps(True)

  def OnDisconnection():
    print "disconnected!", comm_chlas.connected
    comm_chlas.done()

  def work_step(cap):
    global curr_face

    if not comm_chlas.connected:
      LOG.error("could not connect?")
      cap.gui.mirror_image = False
      cap.gui_write("            [ --- D I S C O N N E C T E D --- ]")
      return False
    if not hasattr(comm_chlas,'thread'):
      comm_chlas.read_once(0)
    if comm_chlas.connected:
      faces = cap.find_faces()
      if faces:
        cap.mark_rects(faces)
        LOG.info("Width: {0:.6f} measure cam - face distance (in m.)".format(
            faces[0].w/float(cap.camera.size[0])))
        try:
          vect = cap.get_face_3Dfocus(faces)
        except AssertionError, e:
          print e
        print vect[0]
        vector = (-vect[0][0]+.1)*1.1, vect[0][1], vect[0][2]
        comm_chlas.set_gaze(vector)
        comm_chlas.dont_wait = False

#        import pdb; pdb.set_trace()
        if not curr_face:                               ## nobody found before
          curr_face = User(faces[0])                    ## create new User
          curr_face.interact_init()
        else:                                           ## user already detected
          curr_face.set_visible(faces[0].area())
          if curr_face.is_tooFar():                     ## if user too far
            curr_face.interact_too_far()
                #TDL change gaze vector ?
          else:                                         ## user is close
            if curr_face.is_listening():
              curr_face.interact_story()                ## tell our story
            else:
              curr_face.interact_random()               ## keep user amused
      else:                                             ## no face in this frame
        if curr_face:                                   ## there was a user
          if curr_face.is_lost():                       ## user lost ?
            curr_face.interact_lost()
            curr_face = None
          else:
            curr_face.interact_disappear()              ## temporary undetected

      if ( any(comm_chlas.datablock) and                ## send anything pending
           not comm_chlas.dont_wait ):
        comm_chlas.sendDB_waitReply()

  ##
  ## Initialize
  ##
  comm_chlas = Comm(conf.CHLAS_server, fct_connected=OnConnection)
  setattr(comm_chlas, 'dont_wait', False)
  cap = CamUtils('laptop')
  cap.gui_create()

  ##
  ## Execute
  ##
  try:
    comm_chlas.connect_timeout = .5
    comm_chlas.connect()
    cap.gui_loop(work_step, [cap])
  except KeyboardInterrupt:
    pass
  finally:
    comm_chlas.disconnect()
  print("done")
