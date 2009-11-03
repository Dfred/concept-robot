#!/usr/bin/python
#
# You should have received a copy of the GNU General Public License
# along with comm module.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Communication client to gazing module.
#

import sys
import comm
import conf




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

  def send_gaze(self, direction, distance, speed):
      """Set relative eye movements: orientation for both eyes."""
      self.send()


class HeadConnection(comm.BasicHandler):
  """Connection to head server"""
  def __init__(self):
    comm.BasicHandler.__init__(self)
    self.connect_to(conf.head_addr, 3)
    if not self.connected:
      comm.LOG.warning("head player could not connect!")

  def send_head(self):
    """Set relative head movement."""
    pass


class Player():
  """Reads a data file got from xml2ldp.py and"""
  """ sends contents to appropriate endpoints."""
  def __init__(self):
    self.gaze, self.head = GazeConnection(), HeadConnection()
		
  def read_and_play(self, file):
    f = open(file)
    for line in f.readlines():
      time, cmd = line.split(':')
      args = cmd.split()
      print args
      try:
        fct = getattr(self, "parse_"+args[0])
      except AttributeError:
        print "command not available:", args[0]

      fct(args[1:])

  def parse_eyes(


if __name__ == "__main__":
  p = Player()
  try:
    p.read_and_play(sys.argv[1])
  except IndexError:
    print "pld data file ?"

