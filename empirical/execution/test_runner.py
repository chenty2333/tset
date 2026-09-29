"""Small real-JUnit regression: order control must preserve class/method fixtures."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from run import parse_events

WORK = Path(os.environ.get('EXEC_WORK', '/tmp/execution'))
JDK = Path(os.environ.get('EXEC_JDK', str(WORK/'deps/jdk8u504-b01')))
SOURCE = r'''
import org.junit.*;
public class LifecycleFixture {
  public static class A {
    static int before, after, perTest, ended;
    @BeforeClass public static void beforeClass() { Assert.assertEquals(0,before++); }
    @AfterClass public static void afterClass() { Assert.assertEquals(3,ended); Assert.assertEquals(0,after++); }
    @Before public void setup() { Assert.assertEquals(1,before); perTest++; }
    @After public void teardown() { ended++; }
    @Test public void alpha() { Assert.assertTrue(perTest>0); }
    @Test(expected=IllegalArgumentException.class) public void beta() { throw new IllegalArgumentException("expected"); }
    @Test public void fails() { Assert.fail("intentional"); }
  }
  public static class B {
    static int count;
    @BeforeClass public static void beforeClass() { Assert.assertEquals(0,count++); }
    @AfterClass public static void afterClass() { Assert.assertEquals(1,count); }
    @Test public void gamma() { Assert.assertEquals(1,count); }
  }
  public static class Bad {
    @BeforeClass public static void fails() { throw new IllegalStateException("initialization"); }
    @Test public void neverRuns() {}
  }
}
'''

class RunnerTest(unittest.TestCase):
    def test_whole_class_lifecycle_and_actual_order(self):
        deps=(WORK/'http-request.classpath').read_text().strip()
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); (td/'LifecycleFixture.java').write_text(SOURCE)
            subprocess.run([str(JDK/'bin/javac'),'-cp',deps,'-d',str(td),str(td/'LifecycleFixture.java')],check=True)
            cp=os.pathsep.join([str(WORK/'runner'),str(td),deps])
            forward=['LifecycleFixture$A.alpha','LifecycleFixture$A.beta','LifecycleFixture$A.fails','LifecycleFixture$B.gamma']
            for order in (forward,list(reversed(forward)),forward):
                (td/'order').write_text('\n'.join(order)+'\n')
                subprocess.run([str(JDK/'bin/java'),'-ea','-cp',cp,'OrderedJUnit','run',str(td/'order'),str(td/'events')],check=True)
                r=parse_events(td/'events')
                self.assertEqual(r['started'],order); self.assertEqual(r['ended'],order)
                self.assertEqual(set(r['failures']),{'LifecycleFixture$A.fails'})
                self.assertEqual(r['junit_result'][:3],[4,1,0])
            (td/'order').write_text('LifecycleFixture$Bad.neverRuns\n')
            subprocess.run([str(JDK/'bin/java'),'-cp',cp,'OrderedJUnit','run',str(td/'order'),str(td/'events')],check=True)
            r=parse_events(td/'events')
            self.assertEqual(r['started'],[])
            self.assertEqual(set(r['failures']),{'LifecycleFixture$Bad'})

if __name__=='__main__': unittest.main()
