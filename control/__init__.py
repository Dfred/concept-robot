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

import comm, conf

__author__ = "Frédéric Delaunay"
__copyright__ = "Copyright 2011, University of Plymouth, lightHead system"
__credits__ = [""]
__license__ = "GPL"
__version__ = "0.0.1"
__maintainer__ = "Frédéric Delaunay"
__email__ = "frederic.delaunay@plymouth.ac.uk"
__status__ = "Prototype" # , "Development" or "Production"

conf.load()

class BehaviourRuleError(Exception):
    pass

class IO(object):
    """Input and Output abstracting feature access (in terms of Feature Pool).
    Connection method can be using the comm module or simply import (process).
    """

    def __init__(self, numpy_array, inp_or_out):
        """
        inp_or_out: True: input, False: output
        """
        self.npArray = numpy_array
        self.io = inp_or_out


class Behaviour(object):
    """
    """

    def __init__(self, rules, parent_machine = None):
        """
        Creates a new behaviour based on given rules.
        Behaviours can share states if a parent Behaviour instance is given.
         Order of instanciation sets priority for excution and IO.
        parent_machine: Behaviour instance to run with.
        """
        self.actions = {}       # state : [(fct,in,out),] # ordered by priority
        self.machines = []      # for parallel machines
        self.reset()
        if parent_machine:
            parent_machine.machines.append(self)
        self.set_rules(rules)

    def reset(self):
        """
        """
        self.previous_state = self.current_state = 'STARTED'

    def set_rule(self, in_state, action):
        """Add a rule in the machine.
        in_state: input state
        action: function returning a new state (or None for no state change)
        inp/out: 
        """
        if not self.actions.has_key(in_state):
                self.actions[in_state] = action
        elif self.actions[in_state]:
            raise BehaviourRuleError("Overwritting state: %s has action %s" %
                                     (in_state, self.actions[in_state][0]) )

    def set_rules(self, rules_definitions):
        """
        There is no check of states returned by actions. Although an exception
         will be raised if no action can be taken for a specific state.
        rules_definitions:
        """
        for in_states, action, in rules_definitions:
            if hasattr(in_states,'__iter__'):
                for s in in_states:
                    self.set_rule(s, action)
            else:
                self.set_rule(in_states, action)
        # no integrity check

    # def run(self):
    #     """
    #     """
    #     if self.machines:
    #         self.run_machines()
    #     else:
    #         while self.current_state is not None:
    #             self.current_state = machine.step()

    def run(self, callback=None):
        """Run machine(s) until one reaches state 'STOPPED'.
        Allows multiple Behaviours to run at the same time.
        callback: callable called after each step.
        """
        machines = [self]+self.machines
        machines_states = ['STARTED',]*len(machines)
        while machines_states[0] is not None:
            errors = []
            for i, machine in enumerate(machines):
                try:
                    machines_states[i] = machine.step(machines_states)
                except BehaviourRuleError, e:
                    errors.append(e)
            if len(errors) == len(machines_states):
                raise BehaviourRuleError(errors)
            if callback:
                callback(machines)
                machines_states = [ m.current_state for m in machines ]

    def step(self, machines_states = None):
        """
        """
        try:
            fct = self.actions[self.current_state]
        except KeyError:
            if not machines_states:
                raise BehaviourRuleError("unknown state %s" %self.current_state)
            # else:
            states = [ s for s in machines_states if self.actions.has_key(s)]
            if not states:
                raise BehaviourRuleError("no action for any state in %s" %
                                         machines_states)
            fct = self.actions[states[0]]
        self.current_state = fct() or self.previous_state
        if self.current_state != self.previous_state:
            print 'state change to', self.current_state
        self.previous_state = self.current_state
        return self.current_state

    def stop(self):
        """
        """
        machines = [self]+self.machines
        for m in machines:
            if m.actions.has_key('STOPPED'):
                m.actions['STOPPED']()
            m.current_state = None
