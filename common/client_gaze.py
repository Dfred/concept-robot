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

class GazeClient(comm.BasicHandler):
	"""Our connection to a target server"""
	
	def __init__(self):
		comm.BasicHandler.__init__(self)
		self.focus_pos = (0., -5., 0.)
		self.diameter = 1	# normalized

		# force blocking using timeout
		self.connect_to(conf.gaze_addr, 3)
                if not self.connected:
                        comm.LOG.warning("gaze_client could not connect!")

	def cmd_focus(self, args):
		"""receives focus 3D coordinates"""
		coords = [ float(arg) for arg in args.split(',') ]
		# Y, for "right hand" space orientation + we are mirrored 
		self.focus_pos = (X_FACTOR*coords[0]+X_OFFSET,
				  Y_FACTOR*coords[1]+Y_OFFSET,
				  Z_FACTOR*coords[2]+Z_OFFSET)
		print "focus coords:", self.focus_pos

	def cmd_iris(self, args):
		"""receives [normalized] iris diameter"""
		diameter = float(args[0])
		print "iris diameter:", diameter

GazeClient.process = comm.process
