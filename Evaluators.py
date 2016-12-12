from Expressions import *

class BaseEvaluator(object):
    def __init__(self, assignments):
        self.assignments = assignments

    def evaluateAtomicIntExp(self, exp, value):
        return value

    def evaluateFreeVarExp(self, exp, name):
        return self.assignments[name]

    def evaluateAddExp(self, exp, evaluated_operands):
        return sum(evaluated_operands)

    def evaluateMinExp(self, exp, evaluated_operands):
        if exp.key is None:
            return Exp.OLD_MIN(evaluated_operands)

        return Exp.OLD_MIN(evaluated_operands, key=exp.key)
