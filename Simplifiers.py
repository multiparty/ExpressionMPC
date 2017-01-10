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

class AgressiveRedundantMinSimplifier(BaseSimplifier):
    def __init__(self):
        pass

    def simplifyMinExp(self, exp, operands):
        operands_set = set() # Useful to remove duplicates
        prefix_map = dict()
        
        for op in operands:
            if isinstance(op, AtomicIntExp) or isinstance(op, FreeVarExp): operands_set.add(AddExp([op]))
            else: 
                addFlag = True # Remove arguments with ``loops'' (i.e. the same weight used multiple times).
                tmp_set = set()
                for o in op.operands:
                    if str(o) in tmp_set:
                        addFlag = False
                        break
                    tmp_set.add(str(o))
                        
                if addFlag: operands_set.add(op)
        
        for op in operands_set: # Construct prefix map
            str_op = ""
            l = prefix_map.get(str_op, [])
            l.append(op)
            prefix_map[str_op] = l

            for i in range(len(op.operands)):
                if isinstance(op.operands[i], AtomicIntExp): continue
                
                if len(str_op) > 0: str_op = str_op + "+"
                str_op = str_op + str(op.operands[i])
                
                l = prefix_map.get(str_op, [])
                l.append(op)
                prefix_map[str_op] = l
        
        output = set(operands_set)
        for op in operands_set: # Remove Impossible arguments
            str_op = self.getStrReprWithoutInt(op)
            candidates = prefix_map.get(str_op, [])
            for candidate in candidates:
                if candidate is op: continue
                var_diff = len(candidate.operands) - len(op.operands)
                int_diff = self.getIntPart(op) - self.getIntPart(candidate)
                if var_diff >= int_diff: # can remove
                    if candidate in output: output.remove(candidate)
                    
        operands = []
        for op in output:
            if len(op.operands) == 1: operands.append(op.operands[0])
            else: operands.append(op)
                
        return MinExp(operands, key=exp.key) 
                    
                
    def getIntPart(self, addExp):
        candidate = addExp.operands[-1]
        if isinstance(candidate, AtomicIntExp): return candidate.value()
        return 0
        
    def getAllNotInt(self, addExp):
        candidate = addExp.operands[-1]
        if isinstance(candidate, AtomicIntExp): return addExp.operands[:-1]
        return addExp.operands
        
    def getStrReprWithoutInt(self, addExp):
        return "+".join( [ str(o) for o in self.getAllNotInt(addExp) ] )
                
        
        
        
        
        
        
                    
