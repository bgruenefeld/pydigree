import random

from pydigree.common import *
from pydigree.simulation import *
from pydigree.simulation.simulation import Simulation, SimulationError
from pydigree import paths
from pydigree import Individual


class ConstrainedMendelianSimulation(Simulation):

    def __init__(self, template=None, replications=1000, only=None):
        Simulation.__init__(self, template=template,
                            replications=replications, only=only)
        for ind in self.template.individuals:
            if ind.is_founder():
                continue
            if not (ind.father.is_founder() or ind.mother.is_founder()):
                raise ValueError("ConstrainedMendelian only available"
                                 "for outbred pedigrees")

    def replicate(self, writeibd=False, verbose=False, linkeq=True, replicatenumber=0):
        self.template.clear_genotypes()
        for ped in self.template:
            for x in ped.founders():
                x.label_genotypes()
            for ind in sorted(self.constraints['ibd'],
                              key=lambda x: x.depth, reverse=True):
                if ind.has_genotypes():
                    # If the individual we're looking at has genotypes
                    # already, we've seen them earlier while getting
                    # genotypes for someone deeper in the pedigree
                    continue
                constraints = self.constraints['ibd'][ind]

                # TODO: Multiple constraints per individual
                # Right now we're only using the first ([0]) constraint
                constraints = [(x[1], (x[0], x[2])) for x in constraints]
                location, allele = constraints[0]
                ancestor = allele[0]
                descent_path = random.choice(paths(ancestor, ind))

                for pathindex, path_member in enumerate(descent_path):
                    if path_member.is_founder():
                        continue
                    fa, mo = path_member.parents()

                    if fa in descent_path:
                        paternal_gamete = fa.constrained_gamete(constraints)
                    else:
                        paternal_gamete = fa.gamete()
                    if mo in descent_path:
                        maternal_gamete = mo.constrained_gamete(constraints)
                    else:
                        maternal_gamete = mo.gamete()

                    genotypes = Individual.fertilize(paternal_gamete,
                                                     maternal_gamete)
                    path_member._set_genotypes(genotypes)
            # Get genotypes for everybody else that we're not constraining.
            for ind in ped:
                ind.get_genotypes()

            if writeibd:
                self._writeibd(replicatenumber)

        # Now replace the label genotypes in founders with real ones.
        self.get_founder_genotypes(linkeq=linkeq)

        # Now replace the label genotypes in the nonfounders with the
        # genotypes of the founders
        if callable(self.only):
            siminds = [x for x in self.template.nonfounders() if self.only(x)]
        else:
            siminds = self.template.nonfounders()

        for nf in siminds:
                nf.delabel_genotypes()
        
        # Predict phenotypes
        if self.trait:
            for ind in siminds:
                ind.phenotypes[trait.name] = trait.predict_phenotype(ind)

        if verbose:
            for ind in siminds:
                print ind, ind.get_genotype(location)



