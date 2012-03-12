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
__status__ = "Prototype" # , "Development" or "Production"

LOG = get_logger(__package__)
STARTED, STOPPED = 'STARTED', 'STOPPED'


#
#TODO: Use a event-based approach - currently we're badly wasting CPU... :(
#


class FSMRuleError(StandardError):
    pass


class SPFSM(object):
    """Single-Threaded (Sequential) Parallel Finite State Machine(s).

    A state machine sharing states with other state machines. This allows
    running machines with states trigerring/disabling actions in other machines.
    """


    def __init__(self, name, rules, parent_machine = None):
        """Creates a new behaviour based on given rules.

        SMFSMs can share states if a parent SMFSM instance is given. Order of
        instanciation sets priority for excution.
        name: string identifying this machine.
        rules: iterable of (state or (states,) , function).
        parent_machine: SMFSM instance to run with.
        """
        self.name = name
        self.current_state = None
        self.actions = {}       # { state : (fct,out_state) }
        self.machines = []      # for parallel machines
        self.parent = parent_machine
        if self.parent:
            self.parent.machines.append(self)
        self.set_rules(rules)

    def __repr__(self):
        """
        """
        return "<%s %s [%s]>" % (self.__class__.__name__,
                                 self.name, self.current_state)

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

    def run(self, callback=None):
        """Runs the machine(s) until state STOPPED is reached.

        Allows multiple machines to run (sequentially) at the same step.
        callback: callable called after each step.
        """
        assert self.parent is None, "call this method from the parent FSM"
        self._ready_machines()
        machines = [self]+self.machines
        while self.current_state != STOPPED:
            m_states = [ m.current_state for m in machines ]    # keep sequence
            if all([not m._step(m_states) for m in machines]):  # same here
                raise FSMRuleError("[%s] no action for any state in %s" % (
                                     m.name, m_states))
            callback and callback()

    def abort(self):
        """
        """
        for m in [self]+self.machines:
            m.current_state = STOPPED

    def _ready_machines(self):
        """Initializes the machine(s) and returns all valid states.
        """
        self.current_state = STARTED
        for m in self.machines:
            m.current_state = STARTED

    def _step(self, machines_states):
        """Performs one step of the machine.

        machines_states: [ this machine state, other machines states ]
        Return: False if no action could be triggered.
        """
        states = [ s for s in machines_states if self.actions.has_key(s) ]
        if not states:
            return False
        fct, out_state = self.actions[states[0]]
        state = fct() and out_state or states[0]
        if state != self.current_state:
            LOG.debug("[%s] changed to state: %s %s", self.name, state,
                      self.actions.has_key(state) and self.actions[state][0] or
                      '<keep>')
            self.current_state = state
#            if state == STOPPED:
#                if self.actions.has_key(STOPPED):
#                    self.actions[state][0](self.name)
        return True


class MPFSM(SPFSM):
    """Multi-Threaded Parallel Finite State Machine(s).
    """

    def __init__(self, name, rules, parent_machine = None):
        """
        """
        super(MPFSM,self).__init__(name, rules, parent_machine)
        self.thread = None

    def _ready_machines(self):
        """
        """
        super(MPFSM, self)._ready_machines()
        for m in self.machines:
            m.thread = threading.Thread(target=m._run_machine,name=m.name)
            m.thread.start()

    def _run_machine(self):
        """
        """
        machines = [self,self.parent] + [m for m in self.parent.machines if
                                         m != self]
        while self.current_state != STOPPED:
            if not self._step( [m.current_state for m in machines] ):
                self._wait_active_states()
            else:
                self._wake_state_waiters()
        self.parent.machines.remove(self)       # much easier than synching...
#        self.actions.has_key(STOPPED) and self.actions[STOPPED][0](self.name)
        LOG.debug("%s terminating", self.name)

    def _wait_active_states(self):
        """Thread waits for any state in its own rules.
        """
        pass

    def _wake_state_waiters(self):
        """Unblocks all threads waiting for this thread's state.
        """
        pass

    def run(self, callback=None):
        """Runs the machine(s) until state STOPPED is reached.

        Allows multiple machines to run at the same time: no blocking between 
        machines.
        callback: callable called after each step.
        """
        self._ready_machines()
        machines = [self]+self.machines
        while ( self.current_state != STOPPED and
                self._step([m.current_state for m in machines]) ):     #order
            callback and callback()
        while any( m.thread.isAlive() for m in self.machines ):
            for m in self.machines:
                m.current_state = STOPPED
                if m.thread.isAlive():
                    LOG.debug("joining %s", m.name)
                    m.thread.join(.1)
#        self.actions.has_key(STOPPED) and self.actions[STOPPED][0](self.name)


if __name__ == "__main__":
    import time
#    from utils import LOGFORMATINFO
#    logging.basicConfig(level=logging.DEBUG, **LOGFORMATINFO)

    TMP = None
    # fct1 immediately shifts to next state
    def fct1(): print '@A@'; return True
    # fct2 blocks 2 times for .5s and shifts to next state
    def fct2(): print '@B@'; TMP[0] += 1; time.sleep(.05); return TMP[0] == 2
    # fct3 blocks 2 times for .1s and shifts to next state
    def fct3(): print '@C@'; TMP[1] += 1; time.sleep(.01); return TMP[1] == 2
    # fct4 is not blocking and runs as fast as possible keeping state
    def fct4(): TMP[2] += 1; return False
    # fct5 immediately shifts to next state
    def fct5(): print '@D@'; return True    

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
            print 'TMP counts: %s' % (TMP)

            print '--- testing parallel %s FSM ---' % msg
            m_p = cls('SM_parent', parent_rules)
            cls('SM_child1', child1_rules, m_p)
            cls('SM_child2', child2_rules, m_p)
            TMP = [0,0,0]
            m_p.run()
            print 'done'
            print 'TMP counts: %s' % (TMP)
        except StandardError, e:
            print '===== Exception: %s =====' % e
            import pdb; pdb.post_mortem()
