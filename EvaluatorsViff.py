from Expressions import Exp
from Evaluators import BaseEvaluator

from threading import Lock
from optparse import OptionParser

import viff.reactor
viff.reactor.install()
from twisted.internet import reactor
from viff.config import load_config

from viff.field import GF
from viff.util import find_prime
from viff.comparison import *
from viff.runtime import Runtime, create_runtime, gather_shares, make_runtime_class

import time
import os
import sys

INFINITY=100000

def smin(x, y):
    #m = (x <= y)*x + (y <= x)*y
    m = y + (x <= y)*(x-y)
    return m

class ViffEvaluator(BaseEvaluator):
    @classmethod
    def evaluate(clazz, input_map, expressions, weight_expressions, config_file=None, options=None):
        if config_file is None and options is None:
            parser = OptionParser()
            parser.set_defaults(modulus=2**65)

            Runtime.add_options(parser)
            options, args = parser.parse_args()
            config_file = args[0]

        evaluator = ViffEvaluator(input_map, config_file, options=options)
        return evaluator.evaluate_all(expressions, weight_expressions)

    def __init__(self, input_map, config_file, options=None):
        self.config_file = config_file
        self.options = options

        self.id, self.parties = load_config(self.config_file)
        self.parties_list = [p for p in self.parties]

        self.input_map = input_map
        self.map_inputs_to_parties()

        runtime_class = make_runtime_class(mixins=[ComparisonToft07Mixin])
        self.pre_runtime = create_runtime(self.id, self.parties, 1, self.options, runtime_class)

    def evaluate_all(self, expressions, weight_expressions):
        self.expressions = expressions
        self.weight_expressions = weight_expressions
        self.pre_runtime.addCallback(self.begin_MPC)

        # Start the Twisted event loop.
        reactor.run()
        return self.results

    """
    EVALUATING FUNCTIONS
    """

    def evaluateAtomicIntExp(self, exp, value):
        return value

    def evaluateFreeVarExp(self, exp, name):
        return self.shares[name]

    def evaluateAddExp(self, exp, evaluated_operands):
        return sum(evaluated_operands)

    def evaluateMinExp(self, exp, evaluated_operands):
        #return evaluated_operands[0] # FIX MIN IN VIFF...
        return reduce(smin, evaluated_operands)

    """
    CALLBACKS
    """

    def begin_MPC(self, runtime):
        try:
            self.runtime = runtime
            self.share() # Share inputs

            # Evaluate
            for i in range(len(self.parties_list) - 2):
                print "COMB"
                tmp = {}
                i = 0
                for key in self.expressions:
                    print "exp " + str(i)
                    i = i + 1
                    party, exp = self.expressions[key]
                    tmp[key] = exp.evaluate(self)
                self.shares.update(tmp)
                
                tmp = {}
                i = 0
                for key in self.weight_expressions:
                    print "w" + str(i)
                    i = i + 1
                    exp = self.weight_expressions[key]
                    tmp[key] = exp.evaluate(self)
                self.shares.update(tmp)
            
            evaluated = {}
            for key in self.expressions:
                print "."
                party, exp = self.expressions[key]
                evaluated[key] = (party, exp.evaluate(self))

            # Open
            gathered = []
            self.results = []
            self.keys = []
            for key in evaluated:
                self.keys.append(key)
                
                party, ev = evaluated[key]
                share = self.runtime.open(ev, receivers=[party])
                if share is not None:
                    gathered.append(share)

            gathered = gather_shares(gathered)
            gathered.addCallback(self.results_ready)

            # Shutdown
            self.runtime.schedule_callback(gathered, lambda _: self.runtime.shutdown())
        except:
            import traceback
            traceback.print_exc()

    def results_ready(self, results):
        try:
            self.results = {}
            for i in range(len(results)):
                self.results[self.keys[i]] = results[i]
             
            reveal = set()
            for key in self.expressions:
                party, _ = self.expressions[key]
                if party == self.id:
                    reveal.add(key)
                
            self.results = { k: self.results[k] for k in reveal }
            for k in self.results:
                val = self.results[k]
                if val >= INFINITY: self.results[k] = float("inf")
        except:
            import traceback
            traceback.print_exc()

        
    """
    VIFF RELATED FUNCTIONS
    """

    # PARTY ID MAPPED TO INPUT NAMES
    def map_inputs_to_parties(self):
        # Map node names by party id
        self.party_inputs = {p: [] for p in self.parties}
        for node_name in self.input_map:
            party = int(node_name[1:node_name.index("_")])
            self.party_inputs.get(party).append(node_name)

        # Sort the node names consistently in each party
        self.share_rounds = 0
        for party in self.party_inputs:
            self.party_inputs[party].sort()
            current_length = len(self.party_inputs[party])
            if self.share_rounds < current_length:
                self.share_rounds = current_length

    # SHARE INPUTS IN ROUNDS
    def share(self):
        self.shares = {}

        l = self.runtime.options.bit_length
        k = self.runtime.options.security_parameter
        Zp = GF(find_prime(2**65, blum=True))

        this_party_input = self.party_inputs[self.id]

        # Share in rounds
        for i in range(self.share_rounds):
            value_to_share = 0
            if i < len(this_party_input):
                value_to_share = self.input_map[this_party_input[i]]

            round_shares = self.runtime.shamir_share(self.parties_list, Zp, value_to_share)
            for index in range(len(round_shares)):
                party = self.parties_list[index]
                party_inputs = self.party_inputs[party]
                if i < len(party_inputs):
                    self.shares[party_inputs[i]] = round_shares[index]
