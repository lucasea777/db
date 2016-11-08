# echo '3ra,1wa,2rb,2ra,3wa,2wa,1rb' | python3 ~/Desktop/vs.py
from itertools import permutations
import fileinput, re

def info(instructions):
    state_written_by = {} # {'a': 1, 'b': 0}
    last_write = None # transaction
    reads = set() # {('a', 1, 2)} # var, where, value written by
    for transaction, r_w, var in instructions:
        if r_w == 'w':
            state_written_by[var] = last_write = transaction
        elif r_w == 'r':
            if var not in state_written_by:
                written_by = None
            else:
                written_by = state_written_by[var]
            reads.add((var, transaction, written_by))
        else:
            print('wtf')
    return (reads, last_write)

def plan(instructions, numbers):
    rst = []
    for n in numbers:
        rst.extend(list(filter(lambda x: x[0] == n, instructions)))
    return rst

def check_all_plans(insts):
    """
    >>> ej5 = [(2,'r','a'), \
               (3,'w','a'), \
               (1,'r','b'), \
               (1,'r','a'), \
               (2,'w','a'), \
               (1,'w','a'), \
               (3,'r','b')]
    >>> asw = set(check_all_plans(ej5))
    >>> rst = {((3, 2, 1), False), ((1, 2, 3), False), ((3, 1, 2), False), ((2, 1, 3), False), ((2, 3, 1), True), ((1, 3, 2), False)}
    >>> assert asw == rst
    """
    for per in permutations({x[0] for x in insts}):
        yield (per, info(insts) == info(plan(insts, per)))

def show_check(instrs):
    for per, is_view_ser in check_all_plans(instrs):
        print("{} -> {}".format(per, is_view_ser))

def parse(s):
    try:
        return [re.search('(\d*)([w|r])(\w+)', ins).groups() for ins in s.split(',')]
    except:
        raise Exception("Parse Error")

from doctest import testmod
testmod()
#from IPython import embed; embed()
def main():
    input_data = fileinput.input().readline().replace('\n', '')
    show_check(parse(input_data))
main()
#show_check(ej5)