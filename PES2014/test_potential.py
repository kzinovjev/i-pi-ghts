#!/usr/bin/env python
# encoding: utf-8

from PES import get_potential, initialize_potential
import numpy as np

q = np.array([
    [[-4.62878267,    1.25606861,    0.95459788],
     [-4.85261637,    2.15380812,    0.37457524],
     [-4.27740626,    2.99438311,    0.76831501],
     [-4.53003946,    1.95346377,   -0.88649386],
     [-5.91912714,    2.37708958,    0.44643735],
     [-4.21407574,    1.75722671,   -2.12170961],
     [-3.93964920,    2.62885961,   -2.44704966]],
    [[-4.62878267,    1.25606861,    0.95459788],
     [-4.85261637,    2.15380812,    0.37457524],
     [-4.27740626,    2.99438311,    0.76831501],
     [-4.53003946,    1.95346377,   -0.88649386],
     [-5.91912714,    2.37708958,    0.44643735],
     [-4.21407574,    1.75722671,   -2.12170961],
     [-3.93964920,    2.62885961,   -2.44704966]]
]).T

initialize_potential()
V, dVdq, info = get_potential(q)
print(V, dVdq.T, info)



