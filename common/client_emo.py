#!/usr/bin/python

#
# You should have received a copy of the GNU General Public License
# along with comm module. If not, see <http://www.gnu.org/licenses/>.
#

#
# Communication client to emotional module.
#
import comm

class EmoClient(comm.BasicHandler):
	"""Our connection to a target server"""
	
	def __init__(self, addr_port):
			comm.BasicHandler.__init__(self)
			self.connect_to(addr_port, 3) # force blocking using timeout
			self.sinks = {}

	def process(self, args):
		return comm.process(self, args)
		
	def cmd_emo(self, args):
		"""receives emotional module values"""
		for s in args.split():
				self.sinks[s[0]] = float(s[2:])
