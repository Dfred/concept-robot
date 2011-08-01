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
import readline
import logging
import atexit
import time
import sys
import cmd
import os

import comm
comm.set_default_logging(True)

# readline history
try:
    HOME=os.environ["HOME"]
except:
    HOME=''
HISTFILE=os.path.join(HOME, ".readline_client-history")

ADDR_PORT=None
DISCONNECTED='disconnected'
CONNECTING  ='connecting'
CONNECTED   ='connected'

# XXX: With python 2.7, consider using multiprocessing and os.kill(CTRL_C_EVENT)

class myUI(cmd.Cmd):
  """A readline network client with chocolate.
  Because raw_input is not interruptible, we have to suffer these:
  - messages from the server are displayed in the prompt, but...
  - the prompt is back to its state of generation when Enter key is hit
  """

  def __init__(self, cnx):
    cmd.Cmd.__init__(self)
    self.intro = ("-"*79)+"\n enter 'bye' or press ^C or ^D to quit"
    self.prompt = '-initializing-'
    self.messages = []
    self.cnx = cnx
    self.done = False

  def default(self, line):
    """Called when no do_... function is available"""
    if line.upper() in [ 'EOF', 'BYE' ]:
      if self.cnx.status.startswith(CONNECTED):
        print "\n- disconnecting"
        self.cnx.disconnect()
      self.done = True
    elif line.upper() == '!RECO':
      if self.cnx.status.startswith(DISCONNECTED):
        self.cnx.reconnect()
      else:
        print "\n connection already exists (%s)" % self.cnx.status
    elif line and self.cnx.status.startswith(CONNECTED):
      self.cnx.send_msg(line)

  def emptyline(self):
    """forget the command when no command is given"""
    self.messages = []
    self.preloop()

  def precmd(self, line):
    """called just after raw_input"""
    self.messages = []
    return line

  def postcmd(self, stop, line):
    """return True to stop readline thread"""
    return self.done

  def preloop(self):
    self.prompt = "%s %s> " % (self.cnx.status or 'disconnected', self.messages)

  def redraw_prompt(self):
    line = readline.get_line_buffer()
    self.stdout.write('\r'+' '*( len(self.prompt)+len(line)+1 )+'\r')
    self.preloop()
    print '\r'+self.prompt+line,
    self.stdout.flush()

  def add_message(self, msg):
    self.messages.append(msg)
    self.redraw_prompt()


class commConsClient(comm.ASCIICommandClient):
  """Our connection to a target server
  """

  def __init__(self, addr_port, pipe_mode):
    comm.ASCIICommandClient.__init__(self,addr_port)
    self.status = CONNECTING + " to %s on %s" % addr_port
    self.ui = None
    if pipe_mode:
      self.each_loop = self.send_line_from_pipe

  def send_line_from_pipe(self):
    """Writes a line of data in the ."""
    line = sys.stdin.readline()
    if line:
      print sys.argv[0],"sending>", line
      self.send(line)
    if self.status == DISCONNECTED:
      self.running = False
    return line

  def loop_forever(self):
    """Process inputs until disconnection"""
    try:
        self.connect_and_run()
    except KeyboardInterrupt:
      pass
    except Exception, e:
        print "\n"+str(e)
        self.handle_error(e)
    if self.ui:
      self.ui.done = True
      self.ui.thread.join()
    print 'OUT OF LOOP'

  def handle_connect(self):
    """Called when the client has just connected successfully"""
    self.status = CONNECTED
    self.handler_timeout = self.ui and .5 or None
    self.ui and self.ui.redraw_prompt()

  def handle_disconnect(self):
    self.status = DISCONNECTED
    self.running = False
    self.ui and self.ui.redraw_prompt()

  def handle_notfound(self, cmd, args):
    """method that handles incoming data (line by line)."""
    msg = '%s: %s %s' % (time.time(),cmd[4:],args)
    if self.ui:
      self.ui.add_message(msg)
    else:
      print msg


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "usage: %s [--pipe] [address:]port" % sys.argv[0]
        exit(-1)
    pipe_mode = sys.argv[1] == '--pipe' and sys.argv.pop(1)
    arg = sys.argv[1]
    addr, port = arg.split(':') if arg.find(':') != -1 else (None,arg)
    addr = addr or 'localhost'
    port = port.isdigit() and int(port) or port
    ADDR_PORT=(addr,port)

    cnx = commConsClient((addr,port), pipe_mode)
    if not pipe_mode :
        try:
            readline.read_history_file(HISTFILE)
        except IOError:
            pass
        atexit.register(readline.write_history_file, HISTFILE)
        ui = myUI(cnx)
        cnx.ui = ui
        ui.thread = threading.Thread(target=ui.cmdloop, name='UI')
        ui.thread.start()
    cnx.loop_forever()
