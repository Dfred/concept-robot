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

""" The control module provides classes for creating behaviours based on a
hierarchical finite state machine.
"""

import math
import logging
import threading

from utils import comm, conf, get_logger

__author__ = "Frédéric Delaunay"
__copyright__ = "Copyright 2011, University of Plymouth, lightHead system"
__credits__ = [""]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__status__ = "Development" # "Production"

LOG = get_logger(__package__)
STARTED, STOPPED = 'STARTED', 'STOPPED'

ANGULAR_SPEED = 20


class FSMRuleError(StandardError):
    pass


class SPFSM(object):
    """Single-Threaded (Sequential) Parallel Finite State Machine(s).

    A state machine sharing states with other state machines. This allows
    running machines with states trigerring/disabling actions in other machines.
    As it's a single-threaded FSM, any blocking function would block all FSMs.
    """


    def __init__(self, name, rules, parent_machine = None):
        """Creates a new behaviour based on given rules.

        SPFSMs can share states if a parent SPFSM instance is given. Order of
        instanciation sets priority for excution.
        name: string identifying this machine.
        rules: iterable of (state or (states,) , function).
        parent_machine: SMFSM instance to run with.
        """
        self._state = None
        self._updates = {}
        self._on_change = None                  # callback for state change
        self.actions = {}                       # { state : (fct,out_state) }
        self.machines = []                      # for parallel machines
        self.name = name
        self.parent = parent_machine
        if self.parent:
            self.parent.machines.append(self)
        self.set_rules(rules)

    def __repr__(self):
        """
        """
        return "<%s %s [%s]>" % (self.__class__.__name__,
                                 self.name, self._state)

    @property
    def state(self):
        """Returns current state."""
        return self._state
    @state.setter
    def state(self, new_state):
        """Also call self.change_state."""
        u = (self.parent or self)._updates
        u[new_state] = u[new_state]+1 if u.has_key(new_state) else 0
        if self._on_change:
            try:
                self._on_change(self.name, self._state, new_state)
            except StandardError,e:
                LOG.error("Bad on_StateChange callback (%s)", e)
                raise
        LOG.debug("%s changed to state: [%s] %s", self, new_state, (
                self.actions.has_key(new_state) and self.actions[new_state][0]
                or '<No Function for state>') )
        self._state = new_state

    def set_rule(self, in_state, action, out_state):
        """Adds a rule in the machine.

        in_state: input state
        action: function, returns True: change to out_state, None: keep state.
        out_state: next state
        """
        if self.actions.has_key(in_state):
            raise FSMRuleError("state '%s' already has %s" % (in_state,
                                             self.actions[in_state][0]))
        self.actions[in_state] = action, out_state

    def set_rules(self, rules_definitions):
        """Adds a set of rules to the machine.

        There is no check of states returned by actions. Although an exception
        will be raised if no action can be taken for a specific state.
        rules_definitions: (trigger state, function, new state)
        """
        assert len(rules_definitions[0]) == 3, "bad rules format"
        for in_states, action, out_state in rules_definitions:
            if hasattr(in_states,'__iter__'):
                for s in in_states:
                    self.set_rule(s, action, out_state)
            else:
                self.set_rule(in_states, action, out_state)

    def set_onStateChange(self, function):
        """Installs a hook on FSM named name called on state transition.

        function: callback with arguments for name, last_state and new_state.
                  Use None to remove the callback.
        """
        self._on_change = function

    def _ready_machines(self):
        """Initializes the machine(s) and returns all valid states.
        """
        self.state = STARTED
        for m in self.machines:
            m.state = STARTED

    def run(self, callback=None):
        """Runs the machine(s) until state STOPPED is reached.

        Allows multiple machines to run (sequentially) at the same step.
        callback: callable called after each step.
        """
        assert self.parent is None, "call this method from the parent FSM"
        self._ready_machines()
        machines = [self]+self.machines
        while self._state != STOPPED:
            waiters = [ m for m in machines if m._step() == False ]
            if len(waiters) == len(machines):
                raise FSMRuleError("no transition possible: %s " % (machines))
            states = sorted(self._updates, key=lambda x: x[1])
            for m in waiters:
                for s in states:
                    if s in m.actions.keys():
                        m.state = s
                        break
            callback and callback()

    def _step(self):
        """Performs one step of the machine.

        Returns True on state change, None if no change, False on unbound state.
        """
        self._updates = {}
        try:
            fct, out_state = self.actions[self._state]
        except KeyError:
            return False
        state = fct() and out_state or self._state
        if state != self._state:
            self.state = state
            return True
        return None

    def abort(self):
        """Aborts the PFSM by setting all to state STOPPED.
        """
        for m in [self]+self.machines:
            m.state = STOPPED


class MPFSM(SPFSM):
    """Multi-Threaded Parallel Finite State Machine(s).

    Each FSM runs in its own thread, allowing them to block/do heavy computation
    without impact on other FSM siblings.
    """

    def __init__(self, name, rules, parent_machine = None):
        """
        """
        super(MPFSM,self).__init__(name, rules, parent_machine)
        self.thread = None
        if not self.parent:
            self.ev = threading.Event()

    @SPFSM.state.setter
    def state(self, new_state):
        """Unblocks all threads waiting for new_state."""
        LOG.debug("%s changed to state: [%s] %s", self, new_state, (
                self.actions.has_key(new_state) and self.actions[new_state][0]
                or '<No Function for state>') )
        for m in [self.parent or self]+(self.parent or self).machines:
            m._updates[new_state] = ( m._updates[new_state]+1 if
                                      m._updates.has_key(new_state) else 0 )
        self._state = new_state
        (self.parent or self).ev.set()

    def _ready_machines(self):
        """
        """
        super(MPFSM, self)._ready_machines()
        for m in self.machines:
            m.thread = threading.Thread(target=m._run_machine,
                                        name='fsm_'+m.name)
            m.thread.start()

    def _run_machine(self):
        """Children run loop.
        """
        machines = [self,self.parent] + [m for m in self.parent.machines if
                                         m != self]
        while self._state != STOPPED:
            s = self._step()
            if s == False:
                self.state = self._wait_active_states(machines) or STOPPED
            if s == None:
                st = [ s for s in sorted(self._updates, key=lambda x: x[1])
                       if s in self.actions.keys() and s is not self._state ]
                if st:
                    self.state = st[0]
        LOG.debug("%s terminating", self.name)

    def _wait_active_states(self, machines):
        """Waits for any state in its own rules. See also MPFSM.state.setter...
        """
        p = self.parent or self
        my_states = self.actions.keys()                 #XXX: considered const
        while self._state != STOPPED:
            p.ev.wait()
            states = sorted(self._updates, key=lambda x: x[1])
            new_states = [ s for s in states if s in my_states ]
            p.ev.clear()
            if new_states:
                return new_states[0]

    def run(self, callback=None):
        """Runs the machine(s) until state STOPPED is reached.

        Allows multiple machines to run at the same time: no blocking between 
        machines.
        callback: callable called after each step.
        """
        self._ready_machines()
        machines = [self]+self.machines
        while self._state != STOPPED:
            if self._step() == False:
                self.state = self._wait_active_states(machines)
            callback and callback()
        self.abort()

    def abort(self):
        assert self.parent is None, "abort parent FSM only"
        if self.state != STOPPED:
            self.state = STOPPED
        while any( m.thread.isAlive() for m in self.machines ):
            for m in self.machines:
                m.state = STOPPED
                self.ev.set()
                LOG.debug("joining %s", m.name)
                m.thread.join(.2)



if __name__ == "__main__":
    import time, sys
    if len(sys.argv) > 1 and sys.argv[1] == '-d':
        from utils import LOGFORMATINFO
        LOGFORMATINFO['format'] = '[%(threadName)s] '+LOGFORMATINFO['format']
        logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)
    else:
        print "use -d for debug"

    TMP = None
    # fct1 immediately shifts to next state
    def fct1(): print '@1 '; return True
    # fct2 blocks 2 times for .5s and shifts to next state
    def fct2(): print '@2 '; TMP[0] += 1; time.sleep(.05); return TMP[0] == 2
    # fct3 blocks 2 times for .1s and shifts to next state
    def fct3(): print '@3 '; TMP[1] += 1; time.sleep(.01); return TMP[1] == 2
    # fct4 is not blocking and runs as fast as possible keeping state
    def fct4(): TMP[2] += 1; return False
    # fct5 immediately shifts to next state
    def fct5(): print '@5 '; return True    

    parent_rules = (( STARTED ,fct1,'STATE_1'), ('STATE_1',fct2, STOPPED))
    # in single-threaded FSM, STATE_2 is never reached because fct2 blocks
    # in multi-threaded FSM,  STATE_2 is reached because fct3 is not blocked
    child1_rules = (('STATE_1',fct3,'STATE_2'), ('STATE_2',fct5, STOPPED))
    # with SPFSM, fct4 can only run in synch with fct2 (2 times)
    # with MPFSM, fct4 runs unbounded to fct2
    child2_rules = (('STATE_1',fct4, STOPPED ),)

    for cls, msg in ((SPFSM,'Sequential'), (MPFSM,'Multi-Threaded')):
        try:
            print '--- testing simple %s FSM ---' % msg
            m_p = cls('SM_parent', parent_rules)
            TMP = [0,0,0]
            m_p.run()
            print 'done'
            print 'TMP counts: %s / should be [2,0,0]' % (TMP)

            print '--- testing parallel %s FSM ---' % msg
            m_p = cls('SM_parent', parent_rules)
            cls('SM_child1', child1_rules, m_p)
            cls('SM_child2', child2_rules, m_p)
            TMP = [0,0,0]
            m_p.run()
            print 'done'
            print 'TMP counts: %s / should be [2,2,2%s]' % (TMP, msg[0]=='M' and
                                                            ' or more' or '')
        except StandardError, e:
            print '===== Exception: %s =====' % e
            import pdb; pdb.post_mortem()

    #TODO: mixing SPFSM and MPFSM ?
    #TODO: why MPFSM looping on the same state? (conditions to be clarified)