#!/usr/bin/env python

import argparse

import pydigree
from pydigree.io import read_ped, read_gs_chromosome_template
from pydigree.simulation import ConstrainedMendelianSimulation
from pydigree.simulation import NaiveGeneDroppingSimulation
from pydigree.simulation import Architecture

parser = argparse.ArgumentParser()
parser.add_argument('--template', dest='template', metavar='template_pedigrees',
                    required=True, help='PLINK/LINKAGE/MERLIN format pedigree file')
parser.add_argument('--chromosomes', dest='chromosomes',nargs='+', 
                    help='genomeSIMLA format chromosome templates')
parser.add_argument('--method',  required=True, help='Simulation method',
                    choices=('constrained','genedrop'))
parser.add_argument('--replications', type=int, metavar='nrep',  
                    default=1000, help='Number of replicates')
parser.add_argument('--constraintfile', metavar='file',  help='Constriant file')
parser.add_argument('--effectfile', dest='effectfile',
                    help='File containing marker effects for trait simulation')
parser.add_argument('--effect', nargs=5, action='append', dest='effects')
parser.add_argument('--liability-threshold', type=float, dest='lthresh')
parser.add_argument('--freq', dest='freqs', nargs=3, action='append')
parser.add_argument('--prefix', type=str, help='prefix for output file',
                    default='simulation')
args = parser.parse_args()

# Read the pedigrees
template = read_ped(args.template)

# Read the chromosomes
if not args.chromosomes:
    print 'No chromosomes specified!'
    exit()
for cfile in args.chromosomes:
    c = read_gs_chromosome_template(cfile)
    template.add_chromosome(c)
for freq in args.freqs:
    chr, idx, maf = freq
    maf = float(maf)
    chr, idx = int(chr), int(idx)
    template.chromosomes()[chr].frequencies[idx] = maf
    
# Simulation method
if args.method.lower() == 'constrained':
    sim = ConstrainedMendelianSimulation(template, replications=args.replications)
elif args.method.lower() == 'genedrop':
    sim = NaiveGeneDroppingSimulation(template, replications=args.replications)

# Read effects file
if args.effectfile:
    trait = Architecture.from_file(args.effectsfile)
    trait.name = 'affected'
else:
    trait = Architecture('affected','dichotomous')

# More effects. Specified effects override file effects.
for effect in args.effects:
    chr, pos, p, q, e = effect
    locus = int(chr), int(pos)
    p, q = int(p), int(q)
    e = float(e)
    eff = {(p,q): e}
    trait.add_effect(locus, eff)
if args.lthresh:
    trait.set_liability_threshold(args.lthresh)

sim.set_trait(trait)

if args.constraintfile:
    sim.read_constraints(args.constraintfile)

sim.prefix = args.prefix

sim.run(verbose=True)