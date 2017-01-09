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

class RemoveNestedAddSimplifier(BaseSimplifier):
    def __init__(self):
        pass

    def simplifyAddExp(self, exp, operands):
        for i in range(len(operands)):
            if isinstance(operands[i], int):
                operands[i] = AtomicIntExp(operands[i])
                
        alladd = filter(lambda x: isinstance(x, AddExp), operands)
        noadd = filter(lambda x: not isinstance(x, AddExp), operands)

        for add_exp in alladd:
            noadd = noadd + add_exp.operands

        if len(noadd) == 1:
            return noadd[0]

        allint = filter(lambda x: isinstance(x, AtomicIntExp), noadd)
        noint = filter(lambda x: not isinstance(x, AtomicIntExp), noadd)

        if len(allint) > 0:
            noint.append(AtomicIntExp(sum([e.value() for e in allint])))
            
        return AddExp(noint)

    def simplifyMinExp(self, exp, operands):
        return MinExp(operands, key=exp.key)

# This will only work desirably on expressions simplified
# By both MinToTopSimplifier and RemoveNestedAddSimplifier (in order).
class RemoveRedundantMinSimplifier(BaseSimplifier):
    def __init__(self):
        pass

    def simplifyMinExp(self, exp, operands):
        uniques = { i for i in range(len(operands)) }
        for i in range(len(operands)):
            for j in range(len(operands)):
                if i < j and self.eq(operands[i], operands[j]) and j in uniques:
                    uniques.remove(j)
                elif i != j and self.lt(operands[i], operands[j]) and j in uniques:
                    uniques.remove(j)

        return MinExp([operands[i] for i in range(len(operands)) if i in uniques], key=exp.key)

    def eq(self, o1, o2):
        if not isinstance(o1, Exp) or not isinstance(o2, Exp):
            return NotImplemented

        if isinstance(o1, AtomicIntExp) and isinstance(o2, AtomicIntExp):
            return o1.operands[0] == o2.opernads[0]

        if isinstance(o1, FreeVarExp) and isinstance(o2, FreeVarExp):
            return o1.operands[0] == o2.opernads[0]

        if isinstance(o1, AddExp) and isinstance(o2, AddExp):
            return sorted(map(str, o1.operands)) == sorted(map(str, o2.operands))

        if isinstance(o1, AddExp) or isinstance(o2, AddExp):
            add = o1 if isinstance(o1, AddExp) else o2
            oth = o2 if isinstance(o1, AddExp) else o1

            if isinstance(oth, FreeVarExp):
                varExps = map(str, filter(lambda x: isinstance(x, FreeVarExp), add.operands))
                intExps = map(lambda x: x.operands[0], filter(lambda x: isinstance(x, AtomicIntExp), add.operands))

                return len(varExps) + len(intExps) == len(add.operands) and \
                        len(varExps) == 1 and varExps[0] == oth.operands[0] and \
                        sum(intExps) == 0

            if isinstance(oth, AtomicIntExp):
                intExps = map(lambda x: x.operands[0], filter(lambda x: isinstance(x, AtomicIntExp), add.operands))
                return oth.operands[0] == sum(intExps) and len(intExps) == len(add.operands)

        return False

    def lt(self, o1, o2):
        if not isinstance(o1, Exp) or not isinstance(o2, Exp):
            return NotImplemented

        if isinstance(o1, AtomicIntExp) and isinstance(o2, AtomicIntExp):
            return o1.operands[0] < o2.opernads[0]

        if isinstance(o1, FreeVarExp) and isinstance(o2, FreeVarExp):
            return False

        if isinstance(o1, AddExp) and isinstance(o2, AddExp):
            varExps1 = map(str, filter(lambda x: isinstance(x, FreeVarExp), o1.operands))
            intExps1 = map(lambda x: x.operands[0], filter(lambda x: isinstance(x, AtomicIntExp), o1.operands))
            varExps2 = map(str, filter(lambda x: isinstance(x, FreeVarExp), o2.operands))
            intExps2 = map(lambda x: x.operands[0], filter(lambda x: isinstance(x, AtomicIntExp), o2.operands))

            if len(varExps1) + len(intExps1) != len(o1.operands):
                return False
            if len(varExps2) + len(intExps2) != len(o2.operands):
                return False

            if not Counter(varExps1) == Counter(varExps2):
                return False

            return sum(intExps1) < sum(intExps2)

        if isinstance(o2, AddExp):
            if isinstance(o1, FreeVarExp):
                varExps = map(str, filter(lambda x: isinstance(x, FreeVarExp), o2.operands))
                intExps = map(lambda x: x.operands[0], filter(lambda x: isinstance(x, AtomicIntExp), o2.operands))

                return str(o1.operands[0]) in map(str, varExps) and sum(intExps) > 0

            if isinstance(o1, AtomicIntExp):
                intExps = map(lambda x: x.operands[0], filter(lambda x: isinstance(x, AtomicIntExp), o2.operands))
                return o1.opernads[0] < sum(intExps)

        return False

class AgressiveRedundantMinSimplifier(BaseSimplifier):
    def __init__(self):
        pass

    def simplifyMinExp(self, exp, operands):
        return MinExp(set(operands))
