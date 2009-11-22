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


class GazeConnection(comm.BasicHandler):
  """Connection to gaze server"""
  process = comm.process
  
  def __init__(self):
    comm.BasicHandler.__init__(self)
    self.focus_pos = (0., -5., 0.)
    self.diameter = .5	# normalized
    # force blocking using timeout
    self.connect_to(conf.gaze_addr, 3)
    if not self.connected:
      comm.LOG.warning("gaze player could not connect!")
      
      
class HeadConnection(comm.BasicHandler):
  """Connection to head server"""
  def __init__(self):
    comm.BasicHandler.__init__(self)
    self.connect_to(conf.head_addr, 3)
    if not self.connected:
      comm.LOG.warning("head player could not connect!")


class Player():
  """Reads a data file got from xml2ldp.py and"""
  """ sends contents to appropriate endpoints."""

  def __init__(self):
    self.gaze, self.head = GazeConnection(), HeadConnection()
    if not self.gaze.connected and not self.head.connected:
      raise Exception("No remote module could be reached.")
    
  def read_and_play(self, file, jump_first):
    """Small bufferized player"""

    def read_and_parse(self, f):
      line, bIndex = "", f.tell()
      while not line.strip():
        line = f.readline()
      if bIndex == f.tell():
        return None
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

#       play_time = time.time()- start_time
#       if play_time > frame_time:
#         print "congestion detected **!!!**"
#         continue

    while self.playing and self.gaze.connected:
      print "sleep for", ftime - last_ftime, "s."
      time.sleep(ftime - last_ftime)
      fct(args)
      comm.loop(0.1, count=1)
      last_ftime = ftime
      ftime, fct, args = read_and_parse(self,f)
    f.close()

  def set_eyes(self, argline):
    """set gaze: vector3 normalized_angle time_in_s"""
    print "orientation",argline
    self.gaze.send_msg("orientation "+argline)
      
  def set_fexpr(self, argline):
    """set facial expression"""
    pass


if __name__ == "__main__":
  p = Player()
  jump_first = len(sys.argv) > 1 and sys.argv[1] == '--jump'
  try:
    ifilename = sys.argv[jump_first +1]
  except IndexError:
    print "pld data file ?"
  p.read_and_play(ifilename, jump_first)

