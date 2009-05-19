#
# You should have received a copy of the GNU General Public License
# along with comm module.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Communication client to emotional module.
#

import comm

X_FACTOR=10
X_OFFSET=-4
Y_FACTOR=-4
Y_OFFSET=2
Z_FACTOR=0.13
Z_OFFSET=-40.38

class FaceClient(comm.BasicHandler):
	"""Our connection to a target server"""
	
	def __init__(self, addr_port):
		comm.BasicHandler.__init__(self)
		self.connect_to(addr_port, 3) # force blocking using timeout
		self.face_pos = (0., -5., 0.)

	def cmd_face(self, args):
		"""receives face coordinates relative to camera"""
		args = args.split()
		coords = args[0].split(',')
		# Y, for "right hand" space orientation
		# and we are mirrored 
		self.face_pos = (X_FACTOR*float(coords[0])+X_OFFSET,
						 Z_FACTOR*float(args[1]) + Z_OFFSET,
						 Y_FACTOR*float(coords[1])+Y_OFFSET )

FaceClient.process = comm.process
