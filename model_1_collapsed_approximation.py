from __future__ import division

from math import log
from random import random

from utils import log_sum_exp, log_binomial_pdf

import multiprocessing
import numpy as np

def cellular_frequency_sampler(a, d, pi_r, pi_v, mu, max_iters=10000000):
    x = DataPoint(a, d, pi_r, pi_v, mu)
    
    phi = random()
    
    for i in range(max_iters):
        phi = update_phi(x, phi)
        
        if i % 1000 == 0:
            print i, phi, phi * 0.33 * d, phi * 0.66 * d

def update_phi(data_point, old_phi):   
    new_phi = random()
    
    numerator = data_point.compute_log_likelihood(new_phi)
    
    denominator = data_point.compute_log_likelihood(old_phi)
    
    log_ratio = numerator - denominator
    
    u = random()
    
    if log_ratio >= log(u):
        return new_phi
    else:
        return old_phi

class DataPoint(object):
    def __init__(self, a, d, pi_r, pi_v, mu):
        self.a = a
        self.d = d
        
        self._mu_r = []
        self._mu_v = []
        
        self._log_pi_r = []
        self._log_pi_v = []
        
        for g_r, p_r in enumerate(pi_r):
            if p_r == 0:
                continue
            
            self._log_pi_r.append(log(p_r))
            self._mu_r.append(mu[g_r])
        
            print mu[g_r]
            
        for g_v, p_v in enumerate(pi_v):
            if p_v == 0:
                continue
            
            self._log_pi_v.append(log(p_v))
            self._mu_v.append(mu[g_v])
            
            print mu[g_v]
    
        self._init_ll_cache()
        
    def _init_ll_cache(self):
        self._ll_cache = {}
        
        for d_v in range(self.d + 1):
            self._ll_cache[d_v] = self._compute_log_likelihood(d_v)        
    
    def compute_log_likelihood(self, phi):
        temp = []
        
        for d_v in range(self.d + 1):
            ll = self._ll_cache[d_v]
            ll += log_binomial_pdf(d_v, self.d, phi)
            
            temp.append(ll)
            
        return log_sum_exp(temp)
    
    def _compute_log_likelihood(self, d_v):
        print d_v

        d_r = self.d - d_v
        
        temp = []
        
        for mu_r, log_pi_r in zip(self._mu_r, self._log_pi_r):
            for mu_v, log_pi_v in zip(self._mu_v, self._log_pi_v): 
                temp.append(log_pi_r + log_pi_v + self._compute_latent_term(d_r, d_v, mu_r, mu_v))
            
        return log_sum_exp(temp)    
        
    def _compute_latent_term(self, d_r, d_v, mu_r, mu_v, n=1000000):
        if d_r == 0:
            a_r = np.zeros(n)
        else:
            a_r = np.random.binomial(d_r, mu_r, size=n)
        
        if d_v == 0:
            a_v = np.zeros(n)
        else:
            a_v = np.random.binomial(d_v, mu_v, size=n)
        
        a = a_r + a_v
        
        x = np.zeros(n)
        
        x[a == self.a] = 1
        
        e_a = 1 / n * x.sum()
        
        if e_a != 0:
            return log(e_a)
        else:
            return float('-inf')
        
def get_mu():
    eps = 0.001
    
    mu = []
    
    for c in range(1, 7):
        for a in range(0, c + 1):
            m = a / c
            
            if a == 0:
                m = eps
            elif a == c:
                m = 1 - eps
            
            mu.append(m)

    return mu

def get_pi_v():
#    pi_v = []
#    
#    for c in range(1, 7):
#        for a in range(0, c + 1):
#            if 0 < a < c:
#                pi_v.append(1)
#            else:
#                pi_v.append(0)
#            
#    return [x / sum(pi_v) for x in pi_v]

    pi_v = [0.] * 27
    
    pi_v[2] = 0.5
    pi_v[3] = 0.5
    
    return pi_v

def get_pi_r():
    pi_r = [0.] * 27
    
    pi_r[4] = 1.
    
    return pi_r
            

if __name__ == "__main__":
    mu = get_mu()
    pi_r = get_pi_r()
    pi_v = get_pi_v()
    
    a = 0
    d = 1000
    
    cellular_frequency_sampler(a, d, pi_r, pi_v, mu)
    
#    x = DataPoint(a, d, pi_r, pi_v, mu)
#    
#    for i in range(1, d):
#        print x.compute_log_likelihood(1000, i / d)
#    print x.compute_log_likelihood(500, 0.99)