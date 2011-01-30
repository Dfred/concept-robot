# -*- coding: utf-8 -*-

# This file is part of lightHead.
#
# lightHead is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# lightHead is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with lightHead.  If not, see <http://www.gnu.org/licenses/>.

import math

import control

__author__ = "Frédéric Delaunay"
__copyright__ = "Copyright 2011, University of Plymouth, lightHead system"
__credits__ = [""]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__status__ = "Prototype" # , "Development" or "Production"


def read_section(inp, out, memory=[]):
    """
    Returns: 'EOSECTION','STOPPED'
    """

def listenTo_participant(inp, out):
    """
    Returns: 'P_QUESTION', 'P_STATEMENT', 'P_TIMEOUT'
    """

def answer_participant(inp, out):
    """
    Returns: 'REPLIED'
    """

def nodTo_participant(inp, out):
    """
    Returns: 'REPLIED'
    """

def interrupt_participant(inp, out):
    """
    Returns: 'REPLIED'
    """

def search_participant(inp, out):
    """
    Returns: 'FOUND_PART'
    """

def adjust_head(inp, out):
    """
    Returns: 'ADJUSTED'
    """


class IntelligentPlayer():
    """
    """

    PLAYER_DEF = ( (('FOUND_PART', 'REPLIED'), 
                    read_section),

                   ('EOSECTION',  
                    listenTo_participant),

                   ('P_QUESTION',  
                    answer_participant),

                   ('P_STATEMENT',
                    nodTo_participant),

                   ('P_TIMEOUT',
                    interrupt_participant) )
    
    FACETRACKER_DEF = ( (('STARTED', 'ADJUSTED'),
                         search_participant),

                        ('FOUND_PART',
                         adjust_head) )
                      
    def __init__(self):
        """
        """
        self.player = control.Behaviour(self.PLAYER_DEF)
        self.tracker = control.Behaviour(self.FACETRACKER_DEF, self.player)

    def run(self):
        try:
            self.player.run()
        except KeyboardInterrupt:
            self.player.stop()


if __name__ == '__main__':
    player = IntelligentPlayer()
    player.run()
