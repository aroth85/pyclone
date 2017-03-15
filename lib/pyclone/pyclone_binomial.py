'''
Created on 2013-04-28

@author: Andrew Roth
'''
from __future__ import division

from collections import OrderedDict
from pydp.base_measures import BetaBaseMeasure
from pydp.densities import log_binomial_pdf, Density
from pydp.samplers.atom import BaseMeasureAtomSampler
from pydp.samplers.dp import DirichletProcessSampler
from pydp.samplers.partition import AuxillaryParameterPartitionSampler
from pydp.utils import log_sum_exp

from pyclone.multi_sample import MultiSampleBaseMeasure, MultiSampleDensity, MultiSampleAtomSampler
from pyclone.trace import DiskTrace

import pyclone.config as config

def run_pyclone_binomial_analysis(config_file, num_iters, alpha, alpha_priors):
    data, sample_ids = config.load_data(config_file)
    
    sample_atom_samplers = OrderedDict()
    
    sample_base_measures = OrderedDict()
    
    sample_cluster_densities = OrderedDict()
    
    base_measure_params = config.load_base_measure_params(config_file)
    
    init_method = config.load_init_method(config_file)
        
    for sample_id in sample_ids:
        sample_base_measures[sample_id] = BetaBaseMeasure(base_measure_params['alpha'], base_measure_params['beta'])
        
        sample_cluster_densities[sample_id] = PyCloneBinomialDensity()
        
        sample_atom_samplers[sample_id] = BaseMeasureAtomSampler(sample_base_measures[sample_id], 
                                                                 sample_cluster_densities[sample_id])  
    
    base_measure = MultiSampleBaseMeasure(sample_base_measures)
    
    cluster_density = MultiSampleDensity(sample_cluster_densities)
    
    atom_sampler = MultiSampleAtomSampler(base_measure, cluster_density, sample_atom_samplers)
    
    partition_sampler = AuxillaryParameterPartitionSampler(base_measure, cluster_density)
    
    sampler = DirichletProcessSampler(atom_sampler, partition_sampler, alpha, alpha_priors)
    
    trace = DiskTrace(config_file, data.keys(), {'cellular_frequencies' : 'x'})
    
    trace.open()
    
    sampler.sample(data.values(), trace, num_iters, init_method=init_method)
    
    trace.close()

class PyCloneBinomialDensity(Density):
    def _log_p(self, data, params):
        ll = []
        
        for cn_n, cn_r, cn_v, mu_n, mu_r, mu_v, log_pi  in zip(data.cn_n, data.cn_r, data.cn_v, data.mu_n, data.mu_r, data.mu_v, data.log_pi):
            temp = log_pi + self._log_binomial_likelihood(data.b,
                                                          data.d,
                                                          cn_n,
                                                          cn_r,
                                                          cn_v,
                                                          mu_n,
                                                          mu_r,
                                                          mu_v,
                                                          params.x,
                                                          data.tumour_content)
            
            ll.append(temp)
        
        return log_sum_exp(ll)
    
    def _log_binomial_likelihood(self, b, d, cn_n, cn_r, cn_v, mu_n, mu_r, mu_v, cellular_frequency, tumour_content):  
        f = cellular_frequency
        t = tumour_content
        
        p_n = (1 - t) * cn_n
        p_r = t * (1 - f) * cn_r
        p_v = t * f * cn_v
        
        norm_const = p_n + p_r + p_v
        
        p_n = p_n / norm_const
        p_r = p_r / norm_const
        p_v = p_v / norm_const
        
        mu = p_n * mu_n + p_r * mu_r + p_v * mu_v
        
        return log_binomial_pdf(b, d, mu)
