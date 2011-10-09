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


class FSMRuleError(StandardError):
    pass


class SMFSM(object):
    """ Sequential Multiple Finite State Machines.
    A state machine which shares states with other state machines. This allows
    running machines with states trigerring/disabling actions in other machines.
    """

    STARTED, STOPPED = 'STARTED', 'STOPPED'

    def __init__(self, name, rules, parent_machine = None):
        """ Creates a new behaviour based on given rules.
        SMFSMs can share states if a parent SMFSM instance is given.
        Order of instanciation sets priority for excution.
        name: string identifying this machine.
        rules: iterable of (state or (states,) , function).
        parent_machine: SMFSM instance to run with.
        """
        self.name = name
        self.actions = {}       # { state : fct }
        self.machines = []      # for parallel machines
        if parent_machine:
            parent_machine.machines.append(self)
        self.set_rules(rules)

    def set_rule(self, in_state, action):
        """ Add a rule in the machine.
        in_state: input state
        action: function returning a new state (or None for no state change)
        """
        if not self.actions.has_key(in_state):
                self.actions[in_state] = action
        elif self.actions[in_state]:
            raise FSMRuleError("Overwritting state: %s has action %s" % (
                                 in_state, self.actions[in_state][0]))

    def set_rules(self, rules_definitions):
        """ Add a set of rules to the machine.
        There is no check of states returned by actions. Although an exception
        will be raised if no action can be taken for a specific state.
        rules_definitions: (state, function)
        """
        for in_states, action, in rules_definitions:
            if hasattr(in_states,'__iter__'):
                for s in in_states:
                    self.set_rule(s, action)
            else:
                self.set_rule(in_states, action)

    # def run(self):
    #     """
    #     """
    #     if self.machines:
    #         self.run_machines()
    #     else:
    #         while self.current_state is not None:
    #             self.current_state = machine.step()

    def run(self, callback=None):
        """ Run the machine(s) until one reaches state STOPPED.
        Allows multiple machines to run (sequentially) at the same step.
        callback: callable called after each step.
        """
        all_states, machines = [], [self]+self.machines
        for m in machines:
            m.current_state = self.STARTED
            all_states.extend(m.actions.keys())
        all_states = set(all_states)
        while self.current_state is not self.STOPPED:
            m_states = [ m.current_state for m in machines ]  # get child states
            errors = [ not m._step(m_states) for m in machines ]
            if all(errors):
                raise FSMRuleError("[%s] no action for any state in %s" % (
                                     m.name, m_states))
            for m in machines:                         # XXX: assertion needed ?
                assert m.current_state in all_states, '[%s] unknown state %s' %(
                    self.name, self.current_state)
            if callback:
                callback(machines)

    def _step(self, machines_states = ()):
        """ Perform one step of the machine.
        machines_states: all machines states.
        Return: False if no action could be triggered.
        """
        if self.actions.has_key(self.current_state):
            fct = self.actions[self.current_state]
        else:
            states = [ s for s in machines_states if self.actions.has_key(s)]
            if not states:
                return False
            fct = self.actions[states[0]]
        state = fct()
        if state is not None:
            LOG.debug("[%s] changing to state: %s", self.name, state)
            self.current_state = state
            if state == self.STOPPED and self.actions.has_key(self.STOPPED):
                self.actions[state](self.name)
        return True

    def abort(self):
        """
        """
        for m in [self]+self.machines:
            m.current_state = None

class FSM(SMFSM):
    """ A simple FSM.
    """

    def __init__(self, name, rules):
        """ Create a FSM from the given rules.
        name: string identifying this machine.
        rules: iterable of (state or (states,) , function).
        """
        SMFSM.__init__(self, name, rules)
