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

from __future__ import print_function                       # easier with stderr

import threading
import readline
import atexit
import time
import sys
import cmd
import os

# include path of our utils package for next import
sys.path.insert(1,os.path.join(sys.path[0],'..','..'))
from utils import comm, set_logging_default, handle_exception_debug

set_logging_default(verbosity_level=1)
comm.set_debug_logging(False)

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
IDLE        ='idle'

#XXX: With python 2.7, consider using multiprocessing and os.kill(CTRL_C_EVENT)?

class myUI(cmd.Cmd):
  """A readline network client with chocolate.
  Because raw_input is not interruptible, we have to suffer these:
  - messages from the server are displayed in the prompt, but...
  - the prompt is back to its state of generation when Enter key is hit
  """

  def __init__(self, cnx):
    cmd.Cmd.__init__(self)
    self.intro = (("-"*79)+"\nQuit: 'bye', ^C or ^D. Refresh status with "
        "Enter on an empty line.")
    self.prompt = '-initializing-'
    self.messages = []
    self.cnx = cnx
    self.done = False

  def default(self, line):
    """Called when no do_... function is available"""
    if line.upper() in [ 'EOF', 'BYE' ]:
      self.cnx.looping = False
      if self.cnx.status.startswith(CONNECTED):
        print("\n- disconnecting")
        self.cnx.disconnect()
      self.done = True
    elif line.upper().startswith('!RECO OFF'):
        self.cnx.running = False
        print("\n disabled reconnections")
    elif line.upper().startswith('!RECO ON'):
        self.cnx.autoreco = True
        print("\n enabled reconnections")
    elif line.upper().startswith("!PEER"):
        print("\n currently %s" % self.cnx.status)
    elif line.upper().startswith('!PORT'):
        try:
            self.cnx.port = line.split()[1]
        except IndexError:
            print("> PORT VALUE REQUIRED <")
        if self.cnx.status.startswith(CONNECTED):
            self.cnx.disconnect()
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
    msgs = ''.join(self.messages)
    lbl = self.cnx.status
    if self.cnx.status.startswith(CONNECTED):
        lbl = "%s:%s" % self.cnx.addr_port
    elif self.cnx.status.startswith(DISCONNECTED):
        lbl = "disconnected"
    self.prompt = "%s %s> " % (lbl, msgs)
    del self.messages[0:len(self.messages)]

  def redraw_prompt(self):
    line = readline.get_line_buffer()
    self.stdout.write('\r'+' '*( len(self.prompt)+len(line)+1 )+'\r')
    self.preloop()
    print('\r'+self.prompt+line, end='')
    self.stdout.flush()

  def add_message(self, msg):
    self.messages.append(msg)
    self.redraw_prompt()


class commConsClient(comm.ScriptCommandClient):
  """Our connection to a target server
  """

  def __init__(self, name, addr_port, pipe_mode):
    super(commConsClient, self).__init__(addr_port)
    self.ui = None
    self.name = name
    self.status = IDLE
    self.looping = True
    if pipe_mode:
      self.each_loop = self.send_line_from_pipe
      self.read_script()

  def read_script(self):
    script_lines, chars_left = super(self.__class__).__thisclass__.filter_lines(
        sys.stdin.read())
    if chars_left:
        print('Unfinished: %s' % chars_left, file=sys.stderr)
    self.slines_it = iter(script_lines)

  def send_line_from_pipe(self):
    """Writes a line of data in the ."""
    try:
        line = self.slines_it.next()
        print("%s> %s" % (self.name, line[:-1]))                    # remove \n
        self.send_msg(line)
        if self.status.startswith(DISCONNECTED):
          self.running = False
    except StopIteration:
        print('--- done with script ---', file=sys.stderr)
        self.looping = False
        self.disconnect()
    return ''

  def loop_forever(self):
    """Process inputs until self.looping is False or an Exception is received"""
    while self.looping:
      self.status = CONNECTING + " to %s on %s" % self.addr_port
      try:
        if not self.connect_and_run():
          time.sleep(1)
      except KeyboardInterrupt:
        self.looping = False
      except StandardError, e:
        self.looping = False
        if self.ui:
          self.ui.done = True
          self.ui.thread.join()
          self.ui = None
          handle_exception_debug(force_debugger=True)
    if self.ui:
      self.ui.done = True
      print('press Enter key to finish')                # to unblock input read
      self.ui.thread.join()

  def handle_connect(self):
    """Called when the client has just connected successfully"""
    self.status = CONNECTED + " to %s on %s" % self.addr_port
    self.handler_timeout = self.ui and .5 or None
    self.ui and self.ui.redraw_prompt()

  def handle_disconnect(self):
    self.status = DISCONNECTED + " from %s on %s" % self.addr_port
    self.running = False
    if self.ui:
        self.ui.redraw_prompt()
    else:
        print("disconnected", file=sys.stderr)

  def handle_notfound(self, cmd, args):
    """method that handles incoming data (line by line)."""
    msg = '%s: %s %s' % (time.time(),cmd[4:],args)
    if self.ui:
      self.ui.add_message(msg)
    else:
      print(msg,file=sys.stderr)

  def handle_error(self, error):
    """We ignore bad fd in case we're disconnected"""
    if (not self.ui and self.status.startswith(DISCONNECTED) and
        error == errno.EBADF):
        print("using disconnected fd (%s)"%error, file=sys.stderr)
    else:
        super(commConsClient, self).handle_error(error)


if __name__ == "__main__":
    try:
        pipe_mode = sys.argv[1] == '--pipe' and sys.argv.pop(1)
        arg = sys.argv[1]
        addr, port = arg.split(':') if arg.find(':') != -1 else (None,arg)
        addr = addr or 'localhost'
        port = port.isdigit() and int(port) or port
    except:
        print("usage: %s [--pipe] [address:]port" % sys.argv[0],file=sys.stderr)
        exit(-1)
    ADDR_PORT=(addr,port)

    cnx = commConsClient('readline_client', (addr,port), pipe_mode)
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
