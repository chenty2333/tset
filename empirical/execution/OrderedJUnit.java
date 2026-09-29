import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.lang.reflect.Modifier;
import java.util.*;
import org.junit.runner.*;
import org.junit.runner.notification.*;

/** Runs whole JUnit classes with the project's runner/fixtures, never one Request per method.
 * CLI: discover CLASSES OUTPUT, or run ORDER OUTPUT. All paths are explicit.
 */
public final class OrderedJUnit {
    static String id(Description d) {
        return d.getMethodName() == null ? d.getDisplayName()
            : d.getClassName() + "." + d.getMethodName();
    }
    static String clean(String s) {
        return s == null ? "" : s.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ');
    }
    static void leaves(Description d, PrintWriter out) {
        if (d.isTest()) out.println("TEST\t" + id(d));
        else for (Description c : d.getChildren()) leaves(c, out);
    }
    static int rank(Description d, Map<String,Integer> ranks) {
        Integer r = ranks.get(id(d));
        if (r != null) return r;
        int result = Integer.MAX_VALUE;
        for (Description c : d.getChildren()) result = Math.min(result, rank(c, ranks));
        return result;
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("discover|run INPUT OUTPUT");
        final boolean discover = args[0].equals("discover");
        List<String> lines = Files.readAllLines(Paths.get(args[1]), StandardCharsets.UTF_8);
        LinkedHashSet<String> names = new LinkedHashSet<String>();
        final Map<String,Integer> ranks = new HashMap<String,Integer>();
        for (String line : lines) {
            if (line.trim().isEmpty()) continue;
            if (discover) names.add(line);
            else {
                names.add(line.substring(0, line.lastIndexOf('.')));
                if (ranks.put(line, ranks.size()) != null) throw new IllegalArgumentException("duplicate test");
            }
        }
        List<Class<?>> classes = new ArrayList<Class<?>>();
        for (String name : names) {
            Class<?> cls = Class.forName(name, false, OrderedJUnit.class.getClassLoader());
            if (!Modifier.isAbstract(cls.getModifiers())) classes.add(cls);
        }
        Request request = Request.classes(classes.toArray(new Class<?>[classes.size()]));
        if (!discover) request = request.sortWith(new Comparator<Description>() {
            public int compare(Description a, Description b) {
                return Integer.compare(rank(a, ranks), rank(b, ranks));
            }
        });
        Runner runner = request.getRunner();
        final PrintWriter out = new PrintWriter(new OutputStreamWriter(
            new FileOutputStream(args[2]), StandardCharsets.UTF_8), true);
        if (discover) { leaves(runner.getDescription(), out); out.close(); return; }
        JUnitCore core = new JUnitCore();
        core.addListener(new RunListener() {
            public void testStarted(Description d) { out.println("START\t" + id(d)); }
            public void testFinished(Description d) { out.println("END\t" + id(d)); }
            public void testIgnored(Description d) { out.println("SKIP\t" + id(d)); }
            public void testAssumptionFailure(Failure f) { out.println("ASSUME\t" + id(f.getDescription()) + "\t" + clean(f.getMessage())); }
            public void testFailure(Failure f) {
                Throwable ex = f.getException();
                out.println("FAIL\t" + id(f.getDescription()) + "\t" + ex.getClass().getName()
                    + "\t" + clean(f.getMessage()));
                for (StackTraceElement frame : ex.getStackTrace()) {
                    if (!frame.getClassName().startsWith("org.junit.") && !frame.getClassName().startsWith("java.")) {
                        out.println("FRAME\t" + id(f.getDescription()) + "\t" + clean(frame.toString())); break;
                    }
                }
            }
        });
        Result result = core.run(runner);
        out.println("DONE\t" + result.getRunCount() + "\t" + result.getFailureCount()
            + "\t" + result.getIgnoreCount() + "\t" + result.getRunTime());
        out.close();
        // Tests can leave application threads alive; all JUnit teardown has finished.
        System.exit(0);
    }
}
