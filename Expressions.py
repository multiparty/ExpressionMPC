# Base Class.
class Exp(object):
    SUB_CLASSES = []
    OPERANDS_TYPES = []

    # Constructor
    def __init__(self, operands, cmp=None):
        self.operands = [ self.cast(e) for e in operands ]
        if cmp is not none: self.operands.sort(cmp=cmp)
                
    def cast(self, e):
        if isinstance(e, int) or (isinstance(e, float) and e == float('inf')): return AtomicIntExp(e)
        elif isinstance(e, Exp): return e
        else: raise ValueError("Unknown Type: " + str(type(e)))

    def simplify(self, simplifier):
        pass

    # Abstract
    def evaluate(self, evaluator):
        pass

    # Abstract
    def __str__(self):
        pass
    
    # Hash by string
    def __hash__(self):
        return hash(str(self))

    # Overload the + operator.
    def __add__(self, e2):
        return AddExp([self, e2])

    # Overload the + operator.
    def __radd__(self, e2):
        return AddExp([self, e2])
    
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
        
     # Overload the + operator.
    def __add__(self, e2):
        if isinstance(e2, int) or (isinstance(e2, float) and e2 == float('inf')): 
            self.operands[0] = self.operands[0] + e2
            return self
        elif isinstance(e2, AtomicIntExp):
            self.operands[0] = self.operands[0] + e2.operands[0]
            return self
            
        return super(AtomicIntExp, self).__add__(e2)

    # Overload the + operator.
    def __radd__(self, e2):
        if isinstance(e2, int) or (isinstance(e2, float) and e2 == float('inf')): 
            self.operands[0] = self.operands[0] + e2
            return self
        elif isinstance(e2, AtomicIntExp):
            self.operands[0] = self.operands[0] + e2.operands[0]
            return self
            
        return super(AtomicIntExp, self).__radd__(e2)

# Variable (Unknown)
class FreeVarExp(Exp):
    def __init__(self, name):
        self.operands = [str(name)]

    def __str__(self): # Inherited
        return self.operands[0]
        
    def name(self):
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
    # Use to sort operands
    addCompare = None
    
    def __init__(self, operands):                   
        super(AddExp, self).__init__(operands, cmp=AddExp.addCompare)

    def __str__(self): # Inherited
        return "(" + " + ".join([str(o) for o in self.operands]) + ")" # TODO remove space from +

    def evaluate(self, evaluator): # Inherited
        return evaluator.evaluateAddExp(self, [o.evaluate(evaluator) for o in self.operands])

    def simplify(self, simplifier):
        return simplifier.simplifyAddExp(self, [ o.simplify(simplifier) for o in self.operands])

    # Overload the + operator.
    def __add__(self, e2):
        self.simpleAdd(e2)
        return self

    # Overload the + operator.
    def __radd__(self, e2):
        self.simpleAdd(e2)
        return self

    # Add into self keeping operands sorted
    def simpleAdd(self, e2):
        e2 = cast(e2)
        if isinstance(e2, AtomicIntExp): # Add to existing AtomicIntExp argument
            for i in range(len(self.operands)):
                if isinstance(self.operands[i], AtomicIntExp):
                    self.operands[i].operands[0] += e2.operands[0]
                    return
        
        # Insert into position (to keep sorted)
        for i in range(len(self.operands)):
            if AddExp.addCompare(e2, self.operands[i]) > 0:
                self.operands.insert(i, e2)
                return
        self.operands.append(e2)

# Min between n sub expressions.
class MinExp(Exp):
    # Use to sort operands
    minCompare = None
    
    def __init__(self, operands, **kwargs):
        super(MinExp, self).__init__(operands, cmp=MinExp.minCompare)
        self.key = kwargs.get("key", None) # Custom Comparator if needed.

    def __str__(self): # Inherited
        result = "min(" + ",".join( [ str(o) for o in self.operands ] )
        if self.key is not None: result = result + ", key="+str(self.key)
        return result + ")"

    def addToall(self, element):
        return MinExp([o + element for o in self.operands])

    def crossAdd(self, min2):
        return MinExp([ o1 + o2 for o1 in self.operands for o2 in min2.operands])

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
    elif len(args) > 1:
        args = list(args)

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
        return MinExp(args, key=key)

    if key is None:
        return Exp.OLD_MIN(args)
    return Exp.OLD_MIN(args, key=key)
