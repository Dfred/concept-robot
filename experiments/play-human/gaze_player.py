#
# You should have received a copy of the GNU General Public License
# along with comm module.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Communication client to gazing module.
#

import comm
import conf

X_FACTOR=1
X_OFFSET=0
Y_FACTOR=1
Y_OFFSET=0
Z_FACTOR=1
Z_OFFSET=0

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
		gaze, head = GazeConnection(), HeadConnection()
		

	def read_and_play(self, file):
		f = open(file)
		for line in f.readlines():
			info = line.split()
			
			self.send_gaze()



if __name__ == "__main__":
	p = Player()
	p.read_and_play(sys.argv[1])
