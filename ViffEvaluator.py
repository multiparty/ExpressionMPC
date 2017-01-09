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


def smin(x, y):
    #m = (x <= y)*x + (y <= x)*y
    m = y + (x <= y)*(x-y)
    return m

class ViffEvaluator(BaseEvaluator):
    @classmethod
    def evaluate(clazz, input_map, expressions, config_file=None, options=None):
        if config_file is None and options is None:
            parser = OptionParser()
            parser.set_defaults(modulus=2**65)

            Runtime.add_options(parser)
            options, args = parser.parse_args()
            config_file = args[0]

        evaluator = ViffEvaluator(input_map, config_file, options=options)
        if isinstance(expressions, dict): # If expressions is a dict, return results as dict.
            keys, exps = [], []
            for key in expressions:
                keys.append(key)
                exps.append(expressions[key])

            exps = evaluator.evaluate_all(exps)
            return {keys[i]: exps[i] for i in range(len(exps))}

        return evaluator.evaluate_all(expressions)

    def __init__(self, input_map, config_file, options=None):
        self.config_file = config_file
        self.options = options

        self.id, self.parties = load_config(self.config_file)
        self.parties_list = [p for p in self.parties]

        self.input_map = input_map
        self.map_inputs_to_parties()

        runtime_class = make_runtime_class(mixins=[ComparisonToft07Mixin])
        self.pre_runtime = create_runtime(self.id, self.parties, 1, self.options, runtime_class)

    def evaluate_all(self, expressions):
        self.expressions = expressions
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
        self.runtime = runtime
        self.share() # Share inputs

        # Evaluate
        evaluated = []
        for key, exp in self.expressions:
            evaluated.append((key, exp.evaluate(self)))

        # Open
        gathered = []
        self.results = []
        for key, ev in evaluated:
            share = self.runtime.open(ev, receivers=[key])
            if share is not None:
                gathered.append(share)
                self.results.append("?")
            else:
                self.results.append("X")

        gathered = gather_shares(gathered)
        gathered.addCallback(self.results_ready)

        # Shutdown
        self.runtime.schedule_callback(gathered, lambda _: self.runtime.shutdown())

    def results_ready(self, results):
        i = 0
        for j in range(len(results)):
            while self.results[i] != "?":
                i = i + 1
            self.results[i] = int(results[j])

    """
    VIFF RELATED FUNCTIONS
    """

    # PARTY ID MAPPED TO INPUT NAMES
    def map_inputs_to_parties(self):
        # Map node names by party id
        self.party_inputs = {p: [] for p in self.parties}
        for node_name in self.input_map:
            party = int(node_name[1:node_name.index("_")])
            self.party_inputs.get(party+1).append(node_name)

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
