from __future__ import division

from pydigree.simulation.architecture import Architecture
from pydigree.simulation.simulation import Simulation, SimulationError


class NaiveGeneDroppingSimulation(Simulation):
    def __init__(self, template=None, replications=1000):
        Simulation.__init__(self, template, replications)
        self.genedrop_attempts = 1000

    def replicate(self, writeibd=False, verbose=None, replicatenumber=0):

        for ind in self.template.individuals:
            ind.clear_genotypes()

        for ped in self.template:

            for attempt in xrange(self.genedrop_attempts):
                
                for ind in ped:
                    ind.clear_genotypes()

                # Step 1: Segregate labeled markers so we can know the IBD states
                for founder in ped.founders():
                    founder.label_genotypes()
                for nf in ped.nonfounders():
                    nf.get_genotypes()
                if writeibd:
                    self._writeibd(replicatenumber)
                # Step 2: Fill in genotypes 
                for founder in ped.founders():
                    founder.clear_genotypes()
                    if founder in self.constraints['genotype']:
                        founder.get_constrained_genotypes(
                            self.constraints['genotype'][founder],
                            linkeq=True)
                    else:
                        founder.get_genotypes()

                for nf in ped.nonfounders():
                    nf.delabel_genotypes()


                if self.trait:
                    accuracy = self.predicted_trait_accuracy(ped)
                    if accuracy < self.accuracy_threshold:
                        continue
                if verbose:
                    print 'Success (%s%%) after %s attempts' % (accuracy * 100,
                                                                attempt)
                break
            else:
                raise SimulationError('Ran out of gene dropping attempts!')
