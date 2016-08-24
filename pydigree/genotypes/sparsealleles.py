from collections import Sequence

import numpy as np

from pydigree.cydigree.datastructures import SparseArray
from pydigree.exceptions import NotMeaningfulError
from pydigree.genotypes import AlleleContainer, Alleles
from pydigree.exceptions import NotMeaningfulError
from pydigree.common import mode

class SparseAlleles(AlleleContainer):

    '''
    An object representing a set of haploid genotypes efficiently by 
    storing allele differences from a reference. Useful for manipulating
    genotypes from sequence data (e.g. VCF files)
    '''

    def __init__(self, data=None, refcode=None, missingcode='.', size=None, template=None, dtype=None):
        self.template = template

        if refcode is None:
            if data is None:
                raise IndexError('No refcode or dense data')
            else:
                refcode = mode(data)

        self.refcode = refcode

        if dtype is not None:
            self.dtype = dtype
        elif isinstance(refcode, str):
            self.dtype = np.dtype("S")
        elif isinstance(refcode, np.int):
            self.dtype = np.int
        else:
            raise IndexError('No dtype for container')

        if data is None:
            if template is None and size is None:
                raise ValueError('No template or size')
            elif template is not None and size is None:
                size = self.template.nmark()
            self.container = SparseArray(size, refcode) 
            self.missingindices = set()
            return 

        if type(data) is SparseArray:
            raise NotImplementedError
        
        else:    
            if not isinstance(data, np.ndarray):
                data = np.array(data)
            
            missingidx = np.where(data == missingcode)[0]
            
            # assert 0
            data[missingidx] = refcode
            self.container = SparseArray.from_dense(data, refcode)
            self.missingindices = set(missingidx)

        self.size = len(self.container)

    def __getitem__(self, key):
        return self.container[key]

    def __setitem__(self, key, value):
        self.container[key] = value

    @property
    def missingcode(self):
        return 0 if np.issubdtype(self.dtype, np.integer) else ''

    @property
    def missing(self):
        " Returns a numpy array indicating which markers have missing data "
        base = np.zeros(self.size, dtype=np.bool_)
        base[list(self.missingindices)] = 1
        return base

    def __eq__(self, other):
        if type(other) is SparseAlleles:
            return self.container == other.container
        else:
            return self.container == other

    def __ne__(self, other):
        if type(other) is SparseAlleles:
            return self.container != other.container
        else:
            return self.container != other

    def nmark(self):
        '''
        Return the number of markers (both reference and non-reference)
        represented by the SparseAlleles object
        '''
        return self.container.size

    def todense(self):
        dense = Alleles(self.container.tolist(), template=self.template)
        dense[list(self.missingindices)] = dense.missingcode
        return dense

    def empty_like(self):
        output = SparseAlleles(template=self.template,
                               missingcode=self.missingcode,
                               refcode=self.refcode, size=self.nmark())
        return output

    def copy_span(self, template, copy_start, copy_stop):
        if isinstance(template, SparseAlleles):
            self.container[copy_start:copy_stop] = template.container[copy_start:copy_stop]
            self.missingindices = {x for x in self.missingindices if not (copy_start <= x < copy_stop)}
            self.missingindices |= {x for x in other.missingindices if copy_start <= x < copy_stop}
        else:
            self.container = template[copy_start:copy_stop]

    @staticmethod
    def empty(reference=None, template=None, missingcode=''):
        out = SparseArray(size, template=template, missingcode=missingcode)
        out.missingindices = set()

        return out 