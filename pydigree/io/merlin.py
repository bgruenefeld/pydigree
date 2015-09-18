from itertools import izip

import numpy as np

from pydigree.io import smartopen
from pydigree.genotypes import ChromosomeTemplate
from pydigree.exceptions import FileFormatError


def phenotype_indices(types):
    indices = []
    for property_type in types:
        if property_type in {'S2', 'M'}:
            # Genotypes (M) or skipped genotypes (S2) take up two columns
            indices.extend([False, False])
        elif property_type == 'S':
            indices.append(False)
        elif property_type in {'A', 'T', 'C'}:
            indices.append(True)
        else:
            raise FileFormatError(
                'Unknown MERLIN field type: {}'.format(property_type))
    return np.array(indices, dtype=np.bool)


def genotype_indices(types):
    indices = []
    for property_type in types:
        if property_type == 'M':
            # Genotypes (M) take up two columns
            indices.extend([True, True])
        elif property_type == 'S2':
            # Skipped genotypes take up two columns
            indices.extend([False, False])
        elif property_type in {'A', 'S', 'T', 'C'}:
            indices.append(False)
        else:
            raise FileFormatError(
                'Unknown MERLIN field type: {}'.format(property_type))
    return np.array(indices, dtype=np.bool)


def read_map(filename):
    with open(filename) as f:
        line = f.readline()
        header = line.strip().split()
        sex_specific_map = len(header) == 5
        
        lastchrom = None
        chromosomes = []
        for markernum, line in enumerate(f):
            l = line.strip().split()

            if sex_specific_map:
                chrom, marker, pos, male_pos, female_pos = l
                pos = float(pos)
                male_pos, female_pos = float(male_pos), float(female_pos)
            else:
                chrom, marker, pos = l
                pos = float(pos)
                male_pos, female_pos = None, None

            if chrom != lastchrom:
                c = ChromosomeTemplate(label=chrom)
                chromosomes.append(c)
                lastchrom = chrom

            c.add_genotype(map_position=pos, label=marker)

        return chromosomes 

def write_phenotypes(pedigrees, prefix, phenotypes=None,
                     phenotype_types=None, predicate=None, 
                     skip_all_missing=True, missing_code='X', trait=None):
    output_inds = pedigrees.individuals
    if callable(predicate):
        output_inds = [x for x in output_inds if predicate(x)]

    if phenotypes is None:
        available_phenotypes = reduce(set.union,
                                      [set(x.phenotypes.keys())
                                       for x in pedigrees.individuals])
        available_phenotypes = sorted(available_phenotypes)
    else: 
        available_phenotypes = phenotypes

    if not phenotype_types:
        # Default to covariate
        phenotype_types = [('T' if ph == trait else 'C')
                           for ph in available_phenotypes]
    
    if len(phenotype_types) != len(available_phenotypes):
        raise ValueError('Not enough types for specified phenotypes')
    
    def get_ph(ind, phen):
        if phen not in ind.phenotypes:
            return str(missing_code)

        p = ind.phenotypes[phen]

        if p is None:
            return str(missing_code)
        
        return str(ind.phenotypes[phen])

    with open(prefix + '.phenotypes.dat', 'w') as datf:
        for ptype, phen in izip(phenotype_types, available_phenotypes):
            datf.write('{0} {1}\n'.format(ptype, phen))

    with open(prefix + '.phenotypes.ped', 'w') as phenf:
        for ind in pedigrees.individuals:
            pedinfo = [str(x) for x in (ind.population.label,
                                        ind.label,
                                        ind.father.label if ind.father is not None else '0',
                                        ind.mother.label if ind.mother is not None else '0',
                                        1 if ind.sex == 0 else 2)]
            phenotypes = [get_ph(ind, ph) for ph in available_phenotypes]
            
            if all(ph == missing_code for ph in phenotypes):
                continue

            oline = ' '.join(str(x) for x in pedinfo + phenotypes)
            phenf.write(oline + '\n')
