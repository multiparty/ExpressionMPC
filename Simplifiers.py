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

        return MinExp(*reduce(lambda x,y: x+y, [m.operands for m in allmin], nomin), key=exp.key)

class RemoveNestedAddSimplifier(BaseSimplifier):
    def __init__(self):
        pass

    def simplifyAddExp(self, exp, operands):
        alladd = filter(lambda x: isinstance(x, AddExp), operands)
        noadd = filter(lambda x: not isinstance(x, AddExp), operands)

        for add_exp in alladd:
            noadd = noadd + add_exp.operands

        if len(noadd) == 1:
            return noadd[0]

        allint = filter(lambda x: isinstance(x, AtomicIntExp), noadd)
        noint = filter(lambda x: not isinstance(x, AtomicIntExp), noadd)

        noint.append(AtomicIntExp(sum([e.value() for e in allint])))
        return AddExp(*noint)

    def simplifyMinExp(self, exp, operands):
        return MinExp(*operands, key=exp.key)

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

        return MinExp(*[operands[i] for i in range(len(operands)) if i in uniques], key=exp.key)

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
        # Construct Partial Expression Mapping to Mapping
        mapping = {}
        for o in operands:
            if isinstance(o, AddExp):
                tally_str = ""
                for i in range(len(o.operands)):
                    if i == 0:
                        tally_str = str(o.operands[i])
                    else:
                        tally_str = tally_str + "+" + str(o.operands[i])
                    m = mapping.get(tally_str, None)
                    if m is None:
                        m = []
                        mapping[tally_str] = m

                    m.append((o, o.operands[i+1:]))
            else:
                m = mapping.get(str(o), None)
                if m is None:
                    m = []
                    mapping[str(o)] = m
                m.append((o, []))

        # Attempt to Simplify
        simplified_ops = []
        duplicated_ops = {} # Saves duplicates
        for o in operands:
            ops = o.operands
            visited = { o }
            good = True

            if not isinstance(o, AddExp):
                ops = [ o ]

            ops_str = [ str(op) for op in ops ]
            for l in range(len(ops)):
                i = len(ops) - l
                for other_o, remain_ops in mapping["+".join(ops_str[:i])]:
                    if other_o in visited:
                        continue

                    visited.add(other_o)
                    cmpr = self.ops_leq(remain_ops, ops[i:])
                    if cmpr is None:
                        good = False
                        if duplicated_ops.get(str(o), "") == "-": break
                        duplicated_ops[str(o)] = o
                        break
                    elif cmpr:
                        duplicated_ops[str(o)] = "-"
                        good = False
                        break
            if good:
                simplified_ops.append(o)

        for d in duplicated_ops:
            if duplicated_ops[d] == "-": continue
            simplified_ops.append(duplicated_ops[d])
        return MinExp(*simplified_ops, key=exp.key)

    """
    COMPARE THE OPERANDS ops1 AND ops2
    IF ops1 == ops2 RETURNS None
    IF ops1 < ops2 RETURNS True
    ELSE RETURNS False (ops1 > ops2 OR undetermined)
    """
    def ops_leq(self, ops1, ops2):
        if len(ops1) == 0 and len(ops2) == 0: # Takes care of dups
            return None
        elif len(ops1) == 0: # Takes care of obvious (expression is a proper prefixes)
            return True
        elif len(ops2) == 0:
            return False

        ops1_set = set()
        ops2_set = set()
        ops1_int = 0
        ops2_int = 0

        for o in ops1:
            if isinstance(o, AtomicIntExp): ops1_int += o.value()
            else: ops1_set.add(str(o))
        for o in ops2:
            if isinstance(o, AtomicIntExp): ops2_int += o.value()
            else: ops2_set.add(str(o))

        ops1 = filter(lambda x: not isinstance(x, AtomicIntExp) and not x in ops1_set, ops1)
        ops2 = filter(lambda x: not isinstance(x, AtomicIntExp) and not x in ops1_set, ops2)

        if len(ops1) > 0 and len(ops2) > 0:
            return False

        diff = ops1_int - ops2_int
        if len(ops1) == 0 and len(ops2) == 0 and diff == 0:
            return False

        if len(ops1) == 0 and len(ops2) == 0:
            if diff < 0:
                return True
            else:
                return False

        if len(ops1) == 0 and diff < 0:
            return True
        if len(ops1) == 0 and diff > 0:
            return len(ops2) - diff >= 0

        return False
