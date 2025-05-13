# searchspace
A convenience package for searching and reducing mutli-dimensional spaces

The motivation for this package was to ease the process of searching through permutations of values from multiple sets, where:
* There is a non-negligible cost to evaluating each combination/and or the total space size is large
  * So optimizations on dimensions/sets may want to be done, mid space traversal.
* There are enough dimensions involved for manually coded nested loops to become enwieldy
  * Especially where the order of dimensions and any optimization steps are likely to change
*  The cost of individual combination evaluation is large enough to allow for more abstracted/higher overhead iteration and the convenience/manageability that brings

## Applications

* cybersec tools for password (system) testing
* optimization where there are large numbers of variables, with a high test cost.
* ... let me know! 

## Usage

### Overview

There are 3 classes that work together: dimspec, dimset, dimsetcol.

#### dimspec: 
used to encapulate a 'dimension' in a search space.

#### dimset: 
groups sets (1+) of dimspecs, takes list (or list-like obj) of all searchable vectors for the set of dimspecs.
supports optimization and value change callbacks
useful for combining dimensions that will be optimized as a set.
is iterable


#### dimsetcol:
collects a group of dimsets for form the whole space to be searched.
supports save and resume state storage backend, including optimized dimset value indices.
provided a 'process' function to traverse the whole space, but is also iterable


### Examples
ds1 = dimspec('d1', list(range(-10,10)))
ds2 = dimspec('d12', list(range(-20,0)))
ds3 = dimspec('d12', [chr(x) for x in range(0,256)])

dst1 = dimset([d1]) # defaults to generating indices for all possible values
dst2 = dimset([ds2,ds3], [(x,y) for x in range(len(ds2)) for y in range(len(ds3)]

def proc(c:dimsetcol):
 ...
 # the vector evaluation/cost/processing function

dsc = dimsetcol([dst1,dst2], procs=proc)





