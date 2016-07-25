#!/usr/bin/env python3

import pydigree
import sys
import time
import itertools
import argparse

import numpy as np

from pydigree.ibs import ibs

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', required=True,
                    help='Pedigree file for simulations')
parser.add_argument('-n', '--niter', type=lambda x: int(float(x)), default=10000,
                    help='Number of simulations per pedigree')
parser.add_argument('--only', metavar='PED',
                    help='Only simulate specified pedigrees',
                    nargs='*', dest='onlypeds')
parser.add_argument('--writedist', 
                    help='Write null distribution to file')
parser.add_argument('--include-marryins', dest='remove_mif', action='store_false',
                    help='Include affected marry-in founders in IBD sharing scores')
parser.add_argument('--scorefunction', '-s', dest='scorefunc', default='sbool')
parser.add_argument('--seed', type=int, help='Random seed', default=None)
args = parser.parse_args()


if args.seed is not None:
    pydigree.set_seed(args.seed)


def spairs(ped, inds, loc):
    r = [ibs(j.get_genotype(loc, checkhasgeno=False),
             k.get_genotype(loc, checkhasgeno=False)) 
         for j, k in itertools.combinations(inds, 2)]
    return sum(r)

def sbool(ped, inds, loc):
    npairs = float(len(inds) * (len(inds) - 1) / 2)
    r = [ibs(j.get_genotype(loc, checkhasgeno=False),
             k.get_genotype(loc, checkhasgeno=False)) > 0
         for j, k in itertools.combinations(inds, 2)]
    return sum(r) / npairs


def genedrop(ped, affs, scorer, iteration):
    if iteration % (args.niter / 10) == 0:
        print('Simulation %s' % x)
    ped.simulate_ibd_states(inds=affs)
    s = scorer(ped, affs, (0, 0))
    return s

try:
    scorefunction = {'sbool': sbool, 'spairs': spairs}[args.scorefunc]
except KeyError:
    print("Invalid score function {}".format(args.scorefunc))

pop = pydigree.Population(5000)


peds = pydigree.io.read_ped(args.file, pop)
c = pydigree.ChromosomeTemplate()
c.add_genotype(0.5, 0)
peds.add_chromosome(c)


nulldist = {}

naff = sum(1 for ind in peds.individuals if ind.phenotypes['affected'])
print('{} affecteds'.format(naff))

if args.remove_mif:
    for ind in peds.individuals:
        if ind.is_marryin_founder(): 
            ind.phenotypes['affected'] = False
    naff = sum(1 for ind in peds.individuals if ind.phenotypes['affected'])
    print('{} affecteds after removing marry-in founders'.format(naff))

for i, ped in enumerate(sorted(peds, key=lambda q: q.label)):
    if args.onlypeds and ped.label not in args.onlypeds:
        continue


    # Clear the genotypes, if present
    ped.clear_genotypes()

    affs = {x for x in ped if x.phenotypes['affected']}

    if len(affs) < 2:
        print('Error in pedigree {}: less than two affected individuals. Skipping.'.format(ped.label))
        continue

    print("Pedigree %s (%s/%s), %s affecteds, %s bits, %s simulations" % (ped.label, i+1, len(peds), len(affs), ped.bit_size(),  args.niter))

    sim_share = np.array([genedrop(ped, affs, scorefunction, x)
                             for x in range(args.niter)])
    nulldist[ped.label] = sim_share

    print() 


def stringify(n):
    if type(n) is str:
        return n
    else:
        return "{:.1e}".format(n)

print('\t'.join(['Pedigree','Min','Mean','SD','Max']))
for ped, dist in nulldist.items():
    print('\t'.join(stringify(q) for q in [ped, dist.min(), dist.mean(), dist.std(), dist.max()]))

if args.writedist:
    with open(args.writedist, 'w') as of:
        print("Outputting distribution to %s" % args.writedist)
        for ped in sorted(peds, key=lambda q: q.label):
            try:
                of.write('{} {}\n'.format(ped.label, ' '.join(str(x) for x in nulldist[ped.label])))
            except KeyError:
                pass
