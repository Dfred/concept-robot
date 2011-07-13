#!/usr/bin/python
# -*- coding: utf-8 -*-

# LightHead programm is a HRI PhD project at the University of Plymouth,
#  a Robotic Animation System including face, eyes, head and other
#  supporting algorithms for vision and basic emotions.
# Copyright (C) 2010 Frederic Delaunay, frederic.delaunay@plymouth.ac.uk

#  This program is free software: you can redistribute it and/or
#   modify it under the terms of the GNU General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   General Public License for more details.

#  You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.


#
# Windows users: you need pyreadline from PyPI (http://pypi.python.org/pypi).
# even better, from ipython: https://launchpad.net/pyreadline/+download

import threading
import platform
import readline
import logging
import atexit
import sys
import cmd
import os

import comm
comm.set_default_logging(False)#True)

# readline history
try:
    HOME=os.environ["HOME"]
except:
    HOME=''
HISTFILE=os.path.join(HOME, ".readline_client-history")

ADDR_PORT=None

class myUI(cmd.Cmd):
  def __init__(self):
    self.use_rawinput = platform.system() != 'Windows'
    cmd.Cmd.__init__(self)
    self.intro = "- enter 'bye' or press ^C or ^D to quit"
    self.cnx = None
    self.done = False

  def default(self, line):
    global ADDR_PORT

    if line.upper() in [ 'EOF', 'BYE' ]:
      if self.cnx:
        print "\n- disconnecting"
        self.cnx.disconnect()
        self.cnx = None
      self.done = True
    elif line.upper() == '!RECO':
      if not self.cnx:
        self.cnx = commConsClient(ADDR_PORT)
        self.cnx.ui = self
        threading.Thread(target=self.cnx.loop_forever, name='cnx').start()
      else:
        print "\n connection already exists and runs!", self.cnx.status
    elif line and self.cnx and self.cnx.status == "connected":
      self.cnx.send_msg(line)

  def emptyline(self):
    """forget the command when no command is given"""
    pass

  def postcmd(self, stop, line):
    """return True to stop readline thread"""
    return self.done

  def preloop(self):
    self.prompt = "%s> " % (self.cnx and self.cnx.status or 'disconnected')

  def redraw_prompt(self, message=''):
    line = readline.get_line_buffer()   # doesn't return any character..?
    self.preloop()
    #readline.redisplay()        # unfortunately we don't have this on windows..
    print "\r"+message+"\n"+self.prompt,"%s"%line,
    self.stdout.flush()


class commConsClient(comm.BaseClient):
  """Our connection to a target server"""

  def __init__(self, addr_port):
    self.addr_port = addr_port
    self.status = "connecting to %s on %s" % addr_port
    self.ui = None

  def loop_forever(self):
    """Process inputs until disconnection"""
    try:
        comm.BaseClient.__init__(self, self.addr_port)
        self.connect_and_run()
    except KeyboardInterrupt:
      pass
    except Exception, e:
        print "\n"+str(e)
        self.handle_error(e)
    finally:
        if self.ui:
            self.ui.cnx = None

  def handle_connect(self):
    """Called when the client has just connected successfully"""
    self.status = "connected"
    self.handler_timeout = self.ui and .5 or None
    if self.ui:
        self.ui.redraw_prompt()

  def handle_disconnect(self):
    self.status = "disconnected"
    self.running = False
    if self.ui:
        self.ui.redraw_prompt()

  def handle_error(self, e):
    if self.ui:
        self.ui.done = True
    comm.BaseClient.handle_error(self,e)

  def handle_timeout(self):
    """Called when timeout waiting for data has expired."""
    if pipe_mode:
        line = sys.stdin.readline()
        while line:
            print sys.argv[0],"sending>", line
            self.send(line)
            line = sys.stdin.readline()
            if self.status == "disconnected":
                self.running = False
                return

  def handle_notfound(self, cmd, args):
    """method that handles incoming data (line by line)."""
    msg = 'from server: %s %s' % (cmd[4:],args)
    if self.ui:
        self.ui.redraw_prompt(msg)
    else:
      print msg


if __name__ == "__main__":
    def usage():
        print "usage: %s [--pipe] [address:]port"
        exit(-1)
    pipe_mode =  sys.argv[1] == '--pipe' and sys.argv.pop(1)
    try:
      addr, port = sys.argv[1].split(':')
      port = int(port)
    except Exception:
      if sys.argv[1].isdigit():
        addr,port = 'localhost', int(sys.argv[1])
      else:
        usage()
    ADDR_PORT=(addr,port)

    cnx = commConsClient((addr,port))
    if not pipe_mode :
        try:
            readline.read_history_file(HISTFILE)
        except IOError:
            pass
        atexit.register(readline.write_history_file, HISTFILE)
        ui = myUI()
        ui.cnx = cnx
        cnx.ui = ui
        threading.Thread(target=ui.cmdloop, name='UI').start()
    cnx.loop_forever()
