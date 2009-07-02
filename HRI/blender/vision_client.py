#
# You should have received a copy of the GNU General Public License
# along with comm module.  If not, see <http://www.gnu.org/licenses/>.
#

#
# Communication client to emotional module.
#

import comm

X_FACTOR=1
X_OFFSET=0
Y_FACTOR=1
Y_OFFSET=0
Z_FACTOR=1
Z_OFFSET=0

class VisionClient(comm.BasicHandler):
	"""Our connection to a target server"""
	
	def __init__(self, addr_port):
		comm.BasicHandler.__init__(self)
		self.connect_to(addr_port, 3)	# force blocking using timeout
		self.focus_pos = (0., -5., 0.)
		print "initial coords:", self.focus_pos

	def cmd_focus(self, args):
		"""receives focus 3D coordinates"""
		coords = [ float(arg) for arg in args.split(',') ]
		# Y, for "right hand" space orientation + we are mirrored 
		self.focus_pos = (X_FACTOR*coords[0]+X_OFFSET,
				  Y_FACTOR*coords[1]+Y_OFFSET,
				  Z_FACTOR*coords[2]+Z_OFFSET)
		print "focus coords:", self.focus_pos
VisionClient.process = comm.process
