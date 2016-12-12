# Base Class.
class Exp(object):
    SUB_CLASSES = []
    OPERANDS_TYPES = []

    # Constructor
    def __init__(self, *operands):
        self.operands = []
        for o in operands:
            if isinstance(o, int) or (isinstance(o, float) and o == float('inf')):
                self.operands.append(AtomicIntExp(o))
            elif isinstance(o, Exp):
                self.operands.append(o)
            else:
                raise ValueError("Unknown Type: " + str(type(o)))

    def simplify(self, simplifier):
        pass

    # Abstract
    def evaluate(self, evaluator):
        pass

    # Abstract
    def __str__(self):
        pass

    # Overload the + operator.
    def __add__(self, e2):
        return AddExp(self, e2)

    # Overload the + operator.
    def __radd__(self, e2):
        return AddExp(self, e2)

# Constant Integer
class AtomicIntExp(Exp):
    def __init__(self, value):
        self.operands = [value]

    def __str__(self): # Inherited
        return str(self.operands[0])

    def value(self):
        return self.operands[0]

    def evaluate(self, evaluator): # Inherited
        return evaluator.evaluateAtomicIntExp(self, self.operands[0])

    def simplify(self, simplifier):
        return simplifier.simplifyAtomicIntExp(self, self.operands)

# Variable (Unknown)
class FreeVarExp(Exp):
    def __init__(self, name):
        self.operands = [str(name)]

    def __str__(self): # Inherited
        return self.operands[0]

    def evaluate(self, evaluator): # Inherited
        return evaluator.evaluateFreeVarExp(self, self.operands[0])

    def simplify(self, simplifier):
        return simplifier.simplifyFreeVarExp(self, self.operands)

# Alias for FreeVarExp constructor
def V(name):
    return FreeVarExp(name)

# Addition between n sub expressions.
class AddExp(Exp):
    simpleAddLam = (lambda x, ops: AddExp(*ops))
    def __init__(self, *operands):
        super(AddExp, self).__init__(*operands)

    def __str__(self): # Inherited
        return "(" + "+".join([str(o) for o in self.operands]) + ")"

    def evaluate(self, evaluator): # Inherited
        return evaluator.evaluateAddExp(self, [o.evaluate(evaluator) for o in self.operands])

    def simplify(self, simplifier):
        return simplifier.simplifyAddExp(self, [ o.simplify(simplifier) for o in self.operands])

    # Overload the + operator.
    def __add__(self, e2):
        return self.simpleAdd(e2)

    # Overload the + operator.
    def __radd__(self, e2):
        return self.simpleAdd(e2)

    def simpleAdd(self, e2):
        if isinstance(e2, int) or isinstance(e2, float):
            e2 = AtomicIntExp(e2)

        if isinstance(e2, AddExp):
            return AddExp.simpleAddLam(self, self.operands + e2.operands)
        else:
            return AddExp.simpleAddLam(self, self.operands + [e2])

# Min between n sub expressions.
class MinExp(Exp):
    def __init__(self, *operands, **kwargs):
        super(MinExp, self).__init__(*operands)
        self.key = kwargs.get("key", None) # Custom Comparator if needed.

    def __str__(self): # Inherited
        str_ops = []
        for o in self.operands:
            str_o = str(o)
            if not str_o.startswith("("):
                str_o = "("+str_o+")"
            str_ops.append(str_o)
        str_ops.sort()

        result = "min(" + ",".join(str_ops)
        if self.key is not None:
            result = ", key="+str(self.key)

        return result + ")"

    def addToall(self, element):
        return MinExp(*[o + element for o in self.operands])

    def crossAdd(self, min2):
        return MinExp(*[ o1 + o2 for o1 in self.operands for o2 in min2.operands])

    def evaluate(self, evaluator):
        return evaluator.evaluateMinExp(self, [o.evaluate(evaluator) for o in self.operands])

    def simplify(self, simplifier):
        return simplifier.simplifyMinExp(self, [ o.simplify(simplifier) for o in self.operands ])

# Enumerate all types.
Exp.SUB_CLASSES = [ AtomicIntExp, FreeVarExp, AddExp, MinExp ]
Exp.OPERANDS_TYPES = [ int, float ] + Exp.SUB_CLASSES
Exp.OLD_MIN = min # save min before overloading

# Override the min function
def min(*args, **kwargs):
    # Check count of parameters
    if len(args) == 0:
        Exp.OLD_MIN() # Replicate error

    if len(args) == 1:
        args = list(args[0]) # Copy Iteratable.

    # Check if this min call is part of our expressions or not
    has_exp = len(filter(lambda a: isinstance(a, Exp),  args)) > 0

    # Ensure key word arguments contain nothing or only key.
    key = kwargs.get("key", None)
    if "key" in kwargs:
        del kwargs["key"]

    if len(kwargs) > 0: # return the same error as the actual min.
        Exp.OLD_MIN(*args, **kwargs)

    # Either call the python min, or construct MinExp
    if has_exp:
        return MinExp(*args, key=key)

    if key is None:
        return Exp.OLD_MIN(args)
    return Exp.OLD_MIN(args, key=key)
