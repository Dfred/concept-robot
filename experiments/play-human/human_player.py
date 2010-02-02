#!/usr/bin/python
#
# You should have received a copy of the GNU General Public License
# along with comm module.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Playing custom datafiles (.lpd) to remote submodules.
# The .lpd entries shall be sorted according to their 1st field (time).
#

import sys
import time
import comm
import conf

import logging
logging.basicConfig(level=logging.INFO, format=comm.FORMAT)

conf.load()

class GazeConnection(comm.BasicHandler):
  """Connection to gaze server"""
  process = comm.process
  
  def __init__(self):
    comm.BasicHandler.__init__(self)
    self.focus_pos = (0., -5., 0.)
    self.diameter = .5	# normalized
    # force blocking using timeout
    self.connect_to(conf.conn_gaze, 3)


class FaceConnection(comm.BasicHandler):
  """Connection to face server"""
  def __init__(self):
    comm.BasicHandler.__init__(self)
    self.connect_to(conf.conn_face, 3)

      
class HeadConnection(comm.BasicHandler):
  """Connection to head server"""
  def __init__(self):
    comm.BasicHandler.__init__(self)
    self.connect_to(conf.conn_head, 3)


class Player():
  """Reads a data file got from xml2ldp.py and"""
  """ sends contents to appropriate endpoints."""

  def __init__(self):
    self.gaze = GazeConnection()
    self.face = FaceConnection()
    self.head = HeadConnection()
    if not self.gaze.connected and \
          not self.head.connected and \
          not self.face.connected:
      raise Exception("No remote module could be reached.")
    
  def read_and_play(self, file, jump_first):
    """Small bufferized player"""

    def read_and_parse(self, f):
      line, bIndex = "", f.tell()
      while not line.strip():
        line = f.readline()
      if bIndex == f.tell():
        return (0,None,None)
      frame_time, cmdline = line.split(':')
      cmd, argline = cmdline.split(None, 1)
      try:
        fct = getattr(self, "set_"+cmd)
      except AttributeError:
        print "command not available:", cmd
      return (float(frame_time), fct, argline)

    self.playing = True
    f = open(file)
    last_ftime = 0
    ftime, fct, args = read_and_parse(self,f)
    if jump_first:
      print "jumping to", ftime, "s."
      last_ftime = ftime
    start_time = time.time()
    start_time -= last_ftime

    while self.gaze.connected and fct:
      if (time.time() - start_time) > ftime:
        print "**!!!** congestion detected at frame time", ftime

      print "sleep for", ftime - last_ftime, "s."
      time.sleep(ftime - last_ftime)
      fct(args)
      comm.loop(0.1, count=1)
      last_ftime = ftime
      ftime, fct, args = read_and_parse(self,f)
    f.close()

  def set_eyes(self, argline):
    """set gaze: vector3 normalized_angle time_in_s"""
    self.gaze.send_msg("orientation "+argline)

  def set_blink(self, argline):
    """set blink: duration in seconds"""
    self.face.send_msg("blink "+argline)
      
  def set_f_expr(self, argline):
    """set facial expression"""
    self.face.send_msg("f_expr "+argline)


if __name__ == "__main__":
  p = Player()
  jump_first = len(sys.argv) > 1 and sys.argv[1] == '--jump'
  try:
    ifilename = sys.argv[jump_first +1]
  except IndexError:
    print "what is your .pld data file ?"
    exit(-1)
  p.read_and_play(ifilename, jump_first)
  print "done"
