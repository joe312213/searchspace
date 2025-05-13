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

 
