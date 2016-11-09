import itertools
from functools import partial, wraps
import copy

def end():
    import os
    os.system("kill {}".format(os.popen('ps a | grep al.py').read()))

def all_subsets(ss):
  return itertools.chain(*map(lambda x: map(set, itertools.combinations(ss, x)), range(0, len(ss)+1)))


def p(s):
    """
    >>> p("A")
    frozenset({'A'})
    >>> p("que->rico,io->ce,c->u,ur->ie,i->co,roe->ui") == F({LD("RU","EI"),LD("C","U"),LD("Que", "rico"), LD("IO","CE"), LD("I", "OC"), LD("REO","IU")})
    True
    >>> p("a b, abc") == {frozenset({'A', 'B'}), frozenset({'A', 'B', 'C'})}
    True
    """
    def toset(o):
        return frozenset({A(a) for a in o.replace(" ","")})
    def decompose(al, be):
        return {LD(al,b) for b in be}
    if type(s) is frozenset:
        return s
    if ',' in s:
        they_are_fds = '->' in s # if not they are lists of atts
        dls = F()
        ats = set()
        for e in s.split(','):
            if they_are_fds:
                [al, be] = [toset(e.strip()) for e in  e.split('->')]
                dls.add(LD(al, be))
            else:
                ats.add(toset(e))
        if len(dls) == 1:
            return dls.pop()
        if they_are_fds:
            return dls.composed
        else:
            return ats
    return toset(s)

def parse_params(f):
    """
    Decorator for parsing all arguments of a function
    """
    @wraps(f) #http://stackoverflow.com/questions/22866510/doctest-and-decorators-in-python
    def wrapper(*args, **kwargs):
        args = [p(x) if type(x) == str else x for x in args]
        kwargs = {k: p(v) if type(v) == str else v for k,v in kwargs.items()}
        return f(*args, **kwargs)
    return wrapper

class A(str):
    def __new__(cls, content):
        if len(content) != 1:
            raise Exception("Only one character allowed")
        return str.__new__(cls, content.upper())

class F(set):
    """
    be carefull with cached values! => frozenset ??
    """
    def __init__(self, *args):
        set.__init__(self, *args)

    def __rshift__(self, other):
        def ldimplied(ld):
            return ld.be.issubset(self.cierre(ld.al, R=self.R))
        if type(other) is LD:
            return ldimplied(other)
        if type(other) == type(self):
            return all(map(ldimplied, other))

    @parse_params
    def esquema_en_fnbc(self, r, R=None):
        """
        >>> p("a->b,b->c").esquema_en_fnbc("abc", R="abcd")
        False
        >>> p("a->b,b->c").esquema_en_fnbc("ab", R="abcd")
        True
        """
        assert R != None
        if not r.issubset(R):
            raise Exception("r not subset of R")
        if self.R.issubset(r):
            filtered = filter(lambda df: df.al.issubset(r) and df.be.issubset(r), self)
            return all(map(lambda df: df.istrivial or self.issuperkey(df.al, R=r), filtered))
        else:
            def condition(a):
                c = self.cierre(a, R=R)
                return c.intersection(r - a) == set() or r.issubset(c)
            return all(map(condition, all_subsets(r)))

    def get_esquema_a_normalizar(self, descomp, R=None):
        assert R != None
        for sch in descomp:
            if not self.esquema_en_fnbc(sch, R=R):
                return sch
        return False

    @parse_params
    def descomp_en_fnbc(self, descomp, R=None):
        """
        >>> p("a->b,b->c").descomp_en_fnbc("ab, abc", R="abcd")
        False
        """
        assert R != None
        return self.get_esquema_a_normalizar(descomp, R=R) == False

    def descomp_sin_perdida(self, s1, s2, R=None):
        if not (s1.issubset(R) and s2.issubset(R)):
            raise Exception("s1 or s2 not subset of F.R")
        ss = s1.intersection(s2)
        if ss == set():
            return False
        return self >> LD(ss, s1) or self >> LD(ss, s2)

    def descomp_preserva_dependencias(self, descomposition):
        def df_is_preserved(df):
            result = set(df.al)
            while True:
                x = result.copy()
                for r in descomposition:
                    t = self.cierre(result.intersection(r), R=self.R).intersection(r)
                    result.update(t)
                if x == result:
                    return df.be.issubset(result)
        return all(map(df_is_preserved, self))

    @property
    def composed(self):
        g = F()
        alfas = set()
        for df in self:
            alfas.add(df.al)
        for a in alfas:
            betas = set()
            for dff in self:
                if dff.al == a:
                    betas = betas.union(dff.be)
            g.add(LD(a, betas))
        return g

    #def fnbc(r, R):
    #    result = {r}
    #    done = False
    #    while not done:
    #        sch = get_esquema_a_normalizar(result, R=R)
    #        if sch:



    @property
    def cubrimiento(self):
        """
        >>> f = p("que->rico,io->ce,c->u,ur->ie,i->co,roe->ui")
        >>> f.cubrimiento # doctest:+ELLIPSIS
        F({...})
        """
        def step(f):
            have_removed = False
            f = f.composed
            t = F()
            for ld in f:
                al = set(ld.al)
                be = set(ld.be)
                for a in ld.al:
                    if not have_removed and f.esraroA(a, ld):
                        al.remove(a)
                        have_removed = True
                for a in ld.be:
                    if not have_removed and f.esraroB(a, ld):
                        be.remove(a)
                        have_removed = True
                if len(al) > 0 and len(be) > 0:
                    t.add(LD(al, be))
            return t.composed, have_removed
        rst = self
        while True:
            rst, have_removed = step(rst)
            if not have_removed:
                assert self >> rst
                assert rst >> self
                return rst

    #@functools.lru_cache(maxsize=None)
    @property
    def R(self):
        #import time
        #time.sleep(2)
        R = set()
        for ld in self:
            for a in ld.al.union(ld.be):
                R.add(a)
        return frozenset(R)

    def issuperkey(self, k, R=None):
        assert R != None
        return self.cierre(k, R=self.R) == R

    # def iscandidatekey(self, k):
    #     def trytoremove(k, e):
    #         n = k.copy().remove(e)
    #         if self.issuperkey(n):
    #             return True
    #         return False
    #     def shrink(k):
    #         shrinked = False
    #         for e in k:
    #             if trytoremove(k, e):
    #                 shrinked = True
    #         return shrinked
    #     return shrink(k)

    @property
    def candidatekeys(self, R=None):
        assert R != None
        cks = set()
        def getcomb(n):
            return map(frozenset, itertools.combinations(R, n))
        def some_el_is_subset(cks, c):
            for e in cks:
                if e.issubset(c):
                    return True
            return False
        for n in range(1, len(R)):
            cs = getcomb(n)
            for c in cs:
                if cks != set() and some_el_is_subset(cks, c):
                    continue
                if self.issuperkey(c):
                    cks.add(c)
        return frozenset(cks)

    #@functools.lru_cache(maxsize=None)
    #@property
    #def superkeys(self):
    #    result = {frozenset(F.R)}
    #    for comb in map(frozenset, itertools.combinations(F.R, len(F.R) - 1)):
    #        if self.issuperkey(comb):
    #            result.add(comb)
    #    return result
    

    @parse_params
    def cierre(self, ats, R=None):
        """
        :type ats:set
        """
        assert R != None
        if not ats.issubset(R):
            raise Exception("not subset of R")
        result = set(ats)
        while True:
            t = result.copy()
            for ld in self:
                if ld.al.issubset(result):
                    result.update(ld.be)
            if t == result:
                return result

    def esraroA(self, a, df):
        if not a in df.al:
            raise Exception("A is not subset of df.al")
        if df not in self:
            raise Exception("df not in self")
        if frozenset(a) == df.al:
            return False
        t = set(df.al)
        t.remove(a)
        return df.be.issubset(self.cierre(t, R=self.R))

    def esraroB(self, a, df):
        if not a in df.be:
            raise Exception("A is not subset of df.be")
        if df not in self:
            raise Exception("df not in self")
        if set(a) == df.be:
            return False
        G = F(self)
        G.remove(df)
        bep = set(df.be)
        bep.remove(a)
        if len(bep) < 1 or len(df.al) < 1:
            return False
        G.add(LD(df.al, bep))
        return a in G.cierre(df.al, R=G.R)

class LD(object):
    @parse_params
    def __init__(self, al, be):
        self.al = frozenset(al)
        self.be = frozenset(be) # attributo simple
        if len(al) < 1 or len(be) < 1:
            raise Exception("wrong attrs")
    def __key(self):
        return (self.al, self.be)
    def __eq__(x, y):
        return x.__key() == y.__key()
    def __hash__(self):
        return hash(self.__key())
    def __eq__(self, other):
        return (self.al, self.be) == (other.al, other.be)
    def __repr__(self):
        return "{} -> {}".format(''.join(map(str, self.al)), ''.join(map(str, self.be)))
    @property 
    def istrivial(self):
        return self.be.issubset(self.al)
    __str__ = __repr__


import doctest
doctest.testmod(verbose=False)
#F = LD.decompose("AR","BCDE").union(LD.decompose("O","ER")).union(LD.decompose("E","A"))
#print(f.descomp_preserva_dependencias({p("AB"),p("BC")}))
#print(f.esraroB("D", p("A->DC")))
#print(f.R)
#print(f.cierre(p('A')))
#print(f.candidatekeys)
#print(f.cubrimiento)
#print(f.composed)
#print(f.esquema_en_fnbc(p("AB")))
#import IPython ; IPython.embed()