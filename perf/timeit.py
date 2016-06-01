from __future__ import absolute_import
import subprocess
import sys
import timeit

import perf

# FIXME: simplify this code
_FORMAT_DELTA = (
    # sec
    (100.0,    1, "%.0f sec", "%.0f sec +- %.0f sec"),
    (10.0,     1, "%.1f sec", "%.1f sec +- %.1f sec"),
    (1.0,      1, "%.2f sec", "%.2f sec +- %.2f sec"),
    # ms
    (100e-3, 1e3, "%.0f ms", "%.0f ms +- %.0f ms"),
    (10e-3,  1e3, "%.1f ms", "%.1f ms +- %.1f ms"),
    (1e-3,   1e3, "%.2f ms", "%.2f ms +- %.2f ms"),
    # us
    (100e-6, 1e6, "%.0f us", "%.0f us +- %.0f us"),
    (10e-6,  1e6, "%.1f us", "%.1f us +- %.1f us"),
    (1e-6,   1e6, "%.2f us", "%.2f us +- %.2f us"),
    # ns
    (100e-9, 1e9, "%.0f ns", "%.0f ns +- %.0f ns"),
    (10e-9,  1e9, "%.1f ns", "%.1f ns +- %.1f ns"),
    (1e-9,   1e9, "%.2f ns", "%.2f ns +- %.2f ns"),
)

def _format_delta(dt, stdev=None):
    for min_dt, factor, fmt, fmt_stdev in _FORMAT_DELTA:
        if dt >= min_dt:
            break

    if stdev is not None:
        return fmt_stdev % (dt * factor, stdev * factor)
    else:
        return fmt % (dt * factor,)


class Result(perf.Result):
    def _format(self):
        if len(self.values) >= 2:
            stdev = self.stdev()
        else:
            stdev = None
        return _format_delta(self.mean(), stdev)


_MIN_TIME = 0.2


def _calibrate_timer(timer):
    # determine number so that _MIN_TIME <= total time
    for i in range(1, 10):
        number = 10**i
        dt = timer.timeit(number)
        if dt >= _MIN_TIME:
            break
    return number


def _main_common(args=None):
    # FIXME: use top level imports?
    # FIXME: get ride of getopt! use python 3 timeit main()
    import getopt
    if args is None:
        args = sys.argv[1:]

    try:
        opts, args = getopt.getopt(args, "n:s:r:h",
                                   ["number=", "setup=", "repeat=", "help"])
    except getopt.error as err:
        print(err)
        print("use -h/--help for command line help")
        return 2

    stmt = "\n".join(args) or "pass"
    number = 0   # auto-determine
    setup = []
    repeat = timeit.default_repeat
    for o, a in opts:
        if o in ("-n", "--number"):
            number = int(a)
        if o in ("-s", "--setup"):
            setup.append(a)
        if o in ("-r", "--repeat"):
            repeat = int(a)
            if repeat <= 0:
                repeat = 1
        if o in ("-h", "--help"):
            # FIXME: it's not the right CLI, --verbose doesn't exist
            print(timeit.__doc__)
            return 0
    setup = "\n".join(setup) or "pass"

    # Include the current directory, so that local imports work (sys.path
    # contains the directory of this script, rather than the current
    # directory)
    import os
    sys.path.insert(0, os.curdir)

    timer = timeit.Timer(stmt, setup, perf.perf_counter)
    if number == 0:
        try:
            number = _calibrate_timer(timer)
        except:
            timer.print_exc()
            return 1

    return (timer, repeat, number)


def _main_raw(args=None):
    timer, repeat, number = _main_common()

    result = Result()
    result.metadata['loops'] = str(number)
    try:
        r = []
        for i in range(repeat):
            dt = timer.timeit(number) / number
            result.values.append(dt)
            print(dt)
    except:
        timer.print_exc()
        return 1

    # FIXME: verbose mode
    #print(result.metadata)
    #print(result)
    return None


def _run_subprocess(number):
    args = [sys.executable,
            '-m', 'perf.timeit',
            '--raw',
            "-n", str(number)]
    # FIXME: don't pass duplicate -n
    args.extend(sys.argv[1:])

    proc = subprocess.Popen(args,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            universal_newlines=True)
    # FIXME: use context manager on Python 3
    stdout, stderr = proc.communicate()
    values = []
    # FIXME: pass also metadata like loops
    for line in stdout.splitlines():
        # FIXME: nice error message on parsing error
        value = float(line)
        values.append(value)
    return Result(values)


def _main():
    if '--raw' in sys.argv:
        sys.argv.remove('--raw')
        _main_raw()
    else:
        # FIXME: add command line option
        verbose = False
        # FIXME: don't hardcode the number of runs!
        processes = 3

        timer, repeat, number = _main_common()
        metadata = {
            'processes': processes,
            'runs': repeat,
            'loops': number,
        }
        result = Result(metadata=metadata)
        for process in range(processes):
            run = _run_subprocess(number)
            if verbose:
                print("[%s/%s] %s" % (1 + process, processes, run))
            result.merge_result(run)
        print("Average on %s process x %s runs (%s loops): %s"
              % (metadata['processes'], metadata['runs'], metadata['loops'],
                 result))


if __name__ == "__main__":
    _main()
