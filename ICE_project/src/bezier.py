
import numpy 
from scipy.special import binom 
           
def bernstein(n, k):
    """Bernstein polynomial.
    """
    coeff = binom(n, k)
    def _bpoly(x):
        return coeff * x ** k * (1 - x) ** (n - k)
 
    return _bpoly    
     
def bezier(xList, yList, num=200):
    """Build Bézier curve from points.
    """
    points = (list(zip(xList, yList)))
    N = len(points)
    t = numpy.linspace(0, 1, num=num)
    curve = numpy.zeros((num, 2))
    for ii in range(N):
        curve += numpy.outer(bernstein(N - 1, ii)(t), points[ii])
    return curve
     
     

     