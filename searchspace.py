
from __future__ import annotations

class dimspec:
    nameinc = 0
    def __init__(self, dimname: str, dimvals: tuple):
        if not dimname:
            dimname = 'd' + str(dimspec.nameinc)
            dimspec.nameinc += 1
        self.dimname = dimname
        self.dimvals = dimvals

    def name(self):
        return self.dimname

    def resolve(self, index):
        return self.dimvals[index]
    
    def len(self):
        return len(self.dimvals)

    def __len__(self):
        return self.len()
    

# dimindices is a list of index vectors
# when used in the dimvals of each dimspec, give the actual search value vector 
class dimset:
    dsnameinc = {}
    def __init__(self, dims: list[dimspec] = [], dimindices: list[tuple] = [], resolve = None, optimizer = None, indinit = None, trig=None, col:dimsetcol = None):

        self.dims = dims
        self.numdim = len(dims)
        self.numindices = len(dimindices)
        self.dimindices = dimindices # not a copy initially
        self.dimnames = list(map(lambda d: d.dimname, self.dims))

        if col:
            self.setcol(col)
        else:
            self.col = None
            self.storedel = None
            self.storesave = None

        self.optimizer = optimizer

        self.optcalled = False

        n = self._name()
        if n in dimset.dsnameinc:
            dimset.dsnameinc[n] += 1
        else:
            dimset.dsnameinc[n] = 1
        
        self.dname = n + '_' + str(dimset.dsnameinc[n])

        self.dimindcpy = []
        
        self.indinit = indinit
        
        self._setindinit()

        if resolve:
            self.resolve = resolve
        else:
            self.resolve = lambda v : v

        self.index = 0

        self.curvcache = None
        self.curunvcache = None
        self.curicache = -1
        self.curunicache = -1

        # function to call after 'next'

        self.trig = trig

        self.acc = [0] # for optional use by callbacks that recieve this object

        if not self.dimindices:
            self.dimindices = self.indinit(self.dims)
            self.numindices = len(self.dimindices)

    @classmethod
    def checkname(cls, dims: list[dimspec]):
        dnames = ''
        for d in dims: dnames += d.dimname        
        return dnames
    
    def __len__(self):
        return self.numindices

    def __iter__(self):
        return self

    def _setindinit(self):
        
        if not self.indinit:
            if self.dimindices:
                self.dimindcpy = self.dimindices.copy() #[ x.copy() for x in self.dimindices] #.deepcopy()
                
                self.indinit = lambda _: self.dimindcpy.copy()
            elif self.numdim == 1:
                    self.indinit = lambda _: [(i,) for i in range(self.dims[0].len())]


    def setdimindices(self, dimi:list[tuple], indinit=None):
        self.dimindices = dimi
        if indinit: self.indinit = indinit

        self._setindinit()

    # parent collection
    def setcol(self, col:dimsetcol):
        self.col = col
        if col.storage:
            self.storesave = col.storage['savedimset'] if 'savedimset' in col.storage else None
            self.storedel = col.storage['deldimset'] if 'deldimset' in col.storage else None

    def _name(self):
        return dimset.checkname(self.dims)

    def name(self):
        return self.dname

    def isend(self):
        return True if self.index >= self.numindices else False
    
    def currentisend(self):
        return True if self.index == self.numindices - 1 else False

    # current always returns a valid set of indices or values
    # if next called on last iteration, returns the last set of indices or values
    def current(self):
        if self.index >= self.numindices or self.index == self.curicache: 
            return self.curvcache
        
        c = self.dimindices[self.index]
        self.curunvcache = tuple([self.dims[i].resolve(c[i]) for i in range(self.numdim)])
        self.curvcache = self.resolve(self.curunvcache)
        self.curicache = self.index
        self.curunicache = self.index
        return self.curvcache

    def current_unres(self):
        if self.index >= self.numindices or self.index == self.curicache: 
            return self.curunvcache
        
        c = self.dimindices[self.index]
    #    print(f"dimindices for {self.dname}: {self.dimindices}, len: {len(self.dimindices)}, i[0]: {self.dimindices[0][0]}")
        self.curunvcache = tuple([self.dims[i].resolve(c[i]) for i in range(self.numdim)])
        self.curunicache = self.index
        return self.curunvcache
    
    def current_dict(self):
        cv = self.current_unres()
        return {self.dims[x].dimname : cv[x] for x in range(self.numdim)}
    
    def current_indices(self):
        if self.index >= self.numindices: # len(self.dimindices):
            return self.dimindices[-1] 
        return self.dimindices[self.index]
    
    def current_dictindices(self):
        ci = self.current_indices()
        return {self.dims[x].dimname : ci[x] for x in range(self.numdim)}

    def optsave(self):
        if not self.optcalled and self.optimizer:
            self.optimizer(self)
            self.optcalled = True
            if len(self.dimindices) != self.numindices: # changes made
                self.numindices = len(self.dimindices)
                self.curicache = -1
                self.curunicache = -1
                if self.storesave:
                    self.storesave(self.dname, self.dimindices)

    def __next__(self):
        if self.index >= self.numindices:
            self.optsave()    
            return None

        r = self.current()

        if self.trig is not None:
            self.trig(self)  # pre index increment

        self.index += 1

        return r
    
    def skip(self):
        if self.index >= self.numindices:
            self.optsave()
            return None

        r = self.current()

        # no trig

        if self.index < self.numindices : self.index += 1

        return r        
    
    # serialize
    #def __str__(self):
    #    ...
    
    # return a val so we can easily combine multiple resets in lambda callbacks, using + operator
    def resetpos(self):
        self.index = 0
        self.optcalled = False
        return 1

    # clear any optimizations
    def resetindices(self, clearstore=True): 
        ret = 0
        if self.indinit is not None:
            self.dimindices = self.indinit(self.dims)
            self.numindices = len(self.dimindices)            
            ret = 1  # full reset was made
        self.index = 0
        self.curicache = -1
        self.curunicache = -1  
        self.optcalled = False

        if self.storedel and clearstore:
            self.storedel(self.dname)

        self.acc = [0]

        return ret

    def append(self, vec:tuple):
        
        assert len(vec) == len(self.dims)
        
        self.dimindices.append(vec)

        self.numindices += 1
    
    def remove(self, index):
        ret = self.dimindices.pop(index)
        self.numindices -= 1
        return ret
    
    def setindex(self, i):
        self.index = i if i > 0 and i < len(self.dimindices) else self.index

    def setindices(self, dsi:list[tuple], indinit = None):
        self.dimindices = dsi
        self.numindices = len(dsi)
        self.index = 0
        self.optcalled = False
        self.curicache = -1
        self.curunicache = -1

        if indinit: self.indinit = indinit

        if not self.indinit:        
            self.dimindcpy = self.dimindices.copy() #.copy()
            self.indinit = lambda _: self.dimindcpy
            


# processing collections of dimsets
class dimsetcol:
    def __init__(self, col:list[dimset] = None, storage:dict = None, procs = None, mode='v'):
        self.col = col
        self.storage = storage

        self.mode = mode
        #self.dir = 0
        #self.stacki = 0
        self.procs = procs # optional step processing function, executed for each call to next(self)

        self.curit = self.col[-1] if self.col else None
        self.stackl = len(self.col) if self.col else 0
    #    self.cachediff = None
    #    self.cachedc = 0 # count for next
        self.upcur = True # flag for updating current value on next call to current
        self.curr = {}
        self.curri = {}

        self.end = False

        self.names = []

        if storage:
            self.setstorage(storage)    

        if self.col:
            for ds in self.col:
                ds.setcol(self)            
            self.getnames()
            self.curri, self.curr = self.resolve('dict', 'b')


    def setcol(self, col:list[dimset]):
        self.col = col

        for ds in self.col:
            ds.setcol(self)
        
        self.stackl = len(self.col)
        
        self.curit = self.col[-1]

        self.getnames()

        self.curri, self.curr = self.resolve('dict', 'b')

        
    def setstorage(self, storage:dict):
        self.storage = storage
        self.savestate = self.storage['savestate'] if 'savestate' in self.storage else None
        self.loadstate = self.storage['loadstate'] if 'loadstate' in self.storage else None

        self.savedimsetstore = self.storage['savedimset'] if 'savedimset' in self.storage else None
        self.deldimsetstore = self.storage['deldimset'] if 'deldimset' in self.storage else None
        self.loaddimsetstore = self.storage['loaddimset'] if 'loaddimset' in self.storage else None

        if self.col:
            for ds in self.col:
                ds.setcol(self)  # to update storage callbacks

    # resolve current values of all dimensions into a tuple, list or dictionary

    def resolve(self, type='tuple', mode=None):
        
        if not mode: mode = self.mode

        if mode == 'b':
            return ( self.resolve(type, 'i'), self.resolve(type, 'v') )

        match type:
            case 'tuple' | 'list':            
                cvr = []
                for ds in self.col:
                    dsv = ds.current_unres() if mode == 'v' else ds.current_indices()
                    for dv in dsv:
                        cvr.append(dv)

                if type == 'tuple':
                    cvr = tuple(cvr)
                
            case 'dict' | 'dictionary':
                cv = [ds.current_dict() if mode == 'v' else ds.current_dictindices() for ds in self.col]
                cvr = {}
                for d in cv: cvr |= d
            case _:
                cvr = []
                
        return cvr
        
    # for usage where storage is provided
    def restore(self, skipistate=False, skipfstate=True):
        # load any optimized dimset indices
        if self.col:
            if self.loaddimsetstore:
                for ds in self.col:
                    dsi = self.loaddimsetstore(ds.name())
                    if dsi:
                        ds.dimindices = dsi
                        ds.numindices = len(dsi)
                        # debug
                        print(f"restoring dimset indices for {ds.name()}, numindices: {ds.numindices}, indices:", dsi)
                    
            # lastly
            if self.loadstate and not skipistate:
                state = self.loadstate() # dictionary
                # apply state
                if state and self.col and len(self.col) > 0:

                    s = True
                    for ds in self.col:
                        iv = []
                        for d in ds.dims:
                            if d.dimname in state:
                                iv.append(state[d.dimname])
                            else:
                                break # can't match this dimset from state
                        iv = tuple(iv)
                        if len(iv) == len(ds.dims):
                            try:
                                i = ds.dimindices.index(iv)
                                ds.setindex(i)
                            except ValueError as ve:
                                print(f'Could not find indices {iv} in dimindices, unable to restore position for dimset: ', ds.name())
                        else:
                            s = False
                            print(f"Could not find dimensions of dimset {ds.name()} in restore state")
                else:
                    s = False
                    print("Unable to restore state, no state saved")

                if s: 
                    print(f"Successfully restored state: {state}")

                if skipfstate:
                    if self.currentisend():
                        self.end = True
                        print("Restored state already at end of collection.")
                        for ds in self.col:
                            ds.skip()
                        return
                    self.skip()

            

    # reset all optimizations in all dimsets of the col
    def reset(self, clearstore=True):
        for ds in self.col:
            ds.resetindices(clearstore) # also takes care of deleting stored dimsets, if storage defined for this dimsetcol

        self.end = False

    def isend(self):  # true if at the end set of dim values, or past it.
        end = True
        for ds in self.col:
            if not ds.isend():
                end = False
                break
        self.end = end
        return end
    
    def currentisend(self):
        end = True
        for ds in self.col:
            if not ds.currentisend():
                end = False
                break
        return end        

    # returns the whole collection of dims, except for ds
    def diff(self, ds:dimset, mode=None):
        curr = self.resolve(type='dict', mode=mode)
        return {k : v for k, v in curr.items() if k not in ds.dimnames}

    
    # process all values of a collection of dimsets
    # use a stack structure to process the search space
    # handles state restoration, resuming, 
    def process(self, procs=None, ctrl=None, stacki=-1):

        stackl = len(self.col)

        if not procs and self.procs:
            procs = self.procs

        def proc_cb():
            if self.savestate:
                self.curri = self.resolve('dict', 'i')
                procs(self)
                while next(self.col[-1]): 
                    procs(self)
                    #store the indices of the dimension values before indices were advanced by next()
                    self.savestate(self.curri)  # function takes dimset indexes and adds whatever other data is to be associated with it, when saving this vector.

                    self.curri |= self.col[-1].current_dictindices() # resolve('dict', 'i') # resolves the next set of indices 
                    procs(self)
                
            else:
                procs(self)
                while next(self.col[-1]): 
                    procs(self)             
            
        def proc_trig():
            if self.savestate:
                self.curri = self.resolve('dict', 'i')  
            #    print(":: proc_trig current indices: ", self.curri)              
                while next(self.col[-1]):
                # rely on next() trig callback in the end dimset for processing
                    self.savestate(self.curri) 
                    
                    self.curri |= self.col[-1].current_dictindices() #self.resolve('dict', 'i')
                    
            else:
                while next(self.col[-1]): ...
                # rely on next() trig callback in the end dimset for processing                

        if procs:
            proc = proc_cb  # (additional) process function provided for each step
        else:
            proc = proc_trig # rely on the dimset trig functions to do the processing of each step


        if stacki == -1:
            stacki = stackl - 2 

        while not self.end:
       
            self.col[-1].resetpos()
            proc()
            #    stacki -= 1
            if stacki > 0:
                next(self.col[stacki])
            else:
                break # no outer loops

            if self.col[stacki].isend():

                stackj = stacki - 1
                while stackj >= 0 and self.col[stackj].currentisend():
                    next(self.col[stackj]) # trigger any optimize callbacks
                    stackj -= 1
                    
                if stackj < 0:
                    self.end = True
                    break

                while stacki > stackj:
                    self.col[stacki].resetpos() # only want to reset any dimset pos if not at the final col end
                    stacki -= 1
                # also at the end of the dimset at this position, so keep moving up the stack
                next(self.col[stacki])
                stacki = stackl - 2

        return True     


    def _next_outer(self):
        stacki = self.stackl - 2
    
        if stacki < 0:
            return False 
    
        # increment the dimset at this stack position, then head back down.
        if self.col[stacki].currentisend():

            stackj = stacki - 1
            while stackj >= 0 and self.col[stackj].currentisend():
                next(self.col[stacki])  # trigger any optimize callbacks
                stackj -= 1
                
            if stackj < 0:
                self.end = True
                return False

            while stacki > stackj:
                self.col[stacki].resetpos() # only want to reset any dimset pos if not at the final col end
                stacki -= 1
            # also at the end of the dimset at this position, so keep moving up the stack
            next(self.col[stacki])

        else:
            next(self.col[stacki])
        

        return not self.end
    
    # returns list of all names of all dims in all dimsets, in order of dimset list
    def getnames(self):
        n = []
        for ds in self.col:
            for dim in ds.dims:
                n.append(dim.dimname)
        self.names = n
        return n
    
    def name(self):
        return ''.join(self.names)

    def current_i(self):
        self.curri |= self.col[-1].current_dictindices()
        return self.curri
     
    def current_v(self):
        self.curr |= self.col[-1].current_dict()
        return self.curr
     
    def current_b(self):
        self.curri |= self.col[-1].current_dictindices()
        self.curr |= self.col[-1].current_dict()
        return self.curri, self.curr
     

    

    def current(self, mode=None):

        mode = self.mode if not mode else mode
        match mode:
            case 'i':
                return self.current_i()
            case 'b':
                return self.current_b()
            case _:
                return self.current_v()


    # careful not to update dimset indices outside of iterator usage, when using this..
    def __iter__(self):
        
        return self
    
    def __next__(self):
        if self.end: return None
        if self.mode == 'i':
            ci = self.current()
        else:
            ci, cv = self.current('b') 

        next(self.curit) # important to call this and then 'isend' so that dimset optimize callbacks are called

        if self.procs:
            self.procs(self)  # if using dim indices/values, will need to to use self.curr and self.curri for the ci, cv values

        if self.curit.isend(): # end of the last dimset. the now current 
            next(self.curit) # trigger any optimization callbacks
            if not self._next_outer(): # advance the 'outer loop' dimset(s) as needed 
                self.end = True  

                return None
            else:
                self.curit = self.col[-1] # in case size of collection changed after optimization
                self.curit.resetpos() # other dimsets can change this method if needed, for alternative reset behaviour
                if self.mode == 'i':
                    self.curri = self.resolve('dict', self.mode)
                else:
                    self.curri, self.curr = self.resolve('dict', 'b')

        if self.savestate:
            self.savestate(ci)
                
        return ci if self.mode == 'i' else cv
    
    def __len__(self):
        l = 1
        for ds in self.col:
            l *= len(ds)
        return l

    def skip(self, restoring=False):
        if self.end: return None

        def advance_outer():
            if not self._next_outer(): # advance the 'outer loop' dimset(s) as needed 
                self.end = True  
                return None
            else:
                self.curit = self.col[-1]
                self.curit.resetpos() # other dimsets can change this method if needed, for alternative reset behaviour
          

        if self.curit.currentisend():
            self.curit.skip()
            advance_outer()
            if self.mode == 'i':
                self.curri = self.resolve('dict', self.mode)
            else:
                self.curri, self.curr = self.resolve('dict', 'b')          
        elif self.curit.isend():
            advance_outer()
            if self.mode == 'i':
                self.curri = self.resolve('dict', self.mode)
            else:
                self.curri, self.curr = self.resolve('dict', 'b')          
            self.curit.skip()
        else:
            self.curit.skip()

        self.upcur = True
