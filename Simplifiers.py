from Expressions import *
from collections import Counter

class BaseSimplifier(object):
    def __init__(self):
        pass

    def simplifyAtomicIntExp(self, exp, operands):
        return exp

    def simplifyFreeVarExp(self, exp, operands):
        return exp

    def simplifyAddExp(self, exp, operands):
        return exp

    def simplifyMinExp(self, exp, operands):
        return exp


class MinToTopSimplifier(BaseSimplifier):
    def __init__(self):
        pass

    def simplifyAddExp(self, exp, operands):
        allmin = filter(lambda x: isinstance(x, MinExp), operands)
        nomin = filter(lambda x: not isinstance(x, MinExp), operands)
        if len(nomin) == 0:
            return reduce(lambda x,y: x.crossAdd(y), allmin)

        nomin = reduce(lambda x, y: x + y, nomin)
        if len(allmin) == 0:
            return nomin

        allmin[0] = allmin[0].addToall(nomin)
        return reduce(lambda x,y: x.crossAdd(y), allmin)

    def simplifyMinExp(self, exp, operands):
        allmin = filter(lambda x: isinstance(x, MinExp), operands)
        nomin = filter(lambda x: not isinstance(x, MinExp), operands)

        return MinExp(reduce(lambda x,y: x+y, [m.operands for m in allmin], nomin), key=exp.key)

class AgressiveRedundantMinSimplifier(BaseSimplifier):
    def __init__(self):
        pass

    def simplifyMinExp(self, exp, operands):
        return MinExp(set(operands))
