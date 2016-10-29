# Impulse Generator experiment

import math
import numpy as np


def Gen(n, startPt = 0.0, stopPt = 0.5):

    start = n * startPt if startPt < 0.5 else 0.0
    stop = n * stopPt if stopPt < 0.5 and stopPt > startPt else n//2 + 1

    ret = np.zeros(n)

    for i in range(int(start),int(stop)):

        delta = 2 * math.pi / ( float(n) / i) if i != 0 else 0.0
        phy = -delta * (n//2)

        for j in range(n):
            ret[j] += math.cos(phy) / n
            phy += delta

        

    return ret

