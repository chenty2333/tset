import math
import unittest
from analyze import wilson

class IntervalTest(unittest.TestCase):
    def test_boundary_counts(self):
        self.assertEqual(wilson(0,0),[None,None])
        lo,hi=wilson(0,300)
        self.assertAlmostEqual(lo,0)
        self.assertAlmostEqual(hi,3.841458820694124/(300+3.841458820694124))
        lo1,hi1=wilson(300,300)
        self.assertAlmostEqual(lo1,1-hi);self.assertAlmostEqual(hi1,1)
        self.assertAlmostEqual(1-math.pow(.05,1/300),.0099360819444577)
    def test_symmetry(self):
        for n in (1,5,300):
            for k in range(n+1):
                a,b=wilson(k,n);c,d=wilson(n-k,n)
                self.assertAlmostEqual(a,1-d);self.assertAlmostEqual(b,1-c)
                self.assertLessEqual(a,k/n);self.assertGreaterEqual(b,k/n)

if __name__=='__main__':unittest.main()
