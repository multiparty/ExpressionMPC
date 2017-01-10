from Expressions import MinExp

# compare expressions for prettification purposes (lexicographical order)
def pretty_compare(o1, o2):
    o1 = o1.operands
    o2 = o2.operands
    
    for i in range(min(len(o1), len(o2))):
        s1, s2 = str(o1[i]), str(o2[i])
        if s1 < s2:
            return -1
        if s2 < s1:
            return 1
    
    return len(o1) - len(o2)


# Print MIN operator with arguments ordered and on different lines.
def pprint_min(e, indent=0):
    s = ""
    if indent > 0: s = s * indent
    
    print s+"MIN("
    for o in sorted(e.operands, cmp=pretty_compare): print s+"  "+str(o)
    print s+")"
    
# pretty print a map of expressions
def pprint_map(e):
    print "{"
    for k in e:
        print str(k) + " : ",
        
        if isinstance(e[k], MinExp): pprint_min(e[k], indent=2)
        else: print str(e[k])
        
    print "}"

