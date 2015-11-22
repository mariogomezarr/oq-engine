#  -*- coding: utf-8 -*-
#  vim: tabstop=4 shiftwidth=4 softtabstop=4

#  Copyright (c) 2015, GEM Foundation

#  OpenQuake is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  OpenQuake is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU Affero General Public License
#  along with OpenQuake.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
from datetime import datetime

import numpy
import h5py

from openquake.baselib.general import humansize
from openquake.baselib.hdf5 import Hdf5Dataset


import psutil
if psutil.__version__ > '2.0.0':  # Ubuntu 14.10
    def virtual_memory():
        return psutil.virtual_memory()

    def memory_info(proc):
        return proc.memory_info()

elif psutil.__version__ >= '1.2.1':  # Ubuntu 14.04
    def virtual_memory():
        return psutil.virtual_memory()

    def memory_info(proc):
        return proc.get_memory_info()

else:  # Ubuntu 12.04
    def virtual_memory():
        return psutil.phymem_usage()

    def memory_info(proc):
        return proc.get_memory_info()

perf_dt = numpy.dtype([('operation', (bytes, 50)), ('time_sec', float),
                       ('memory_mb', float), ('counts', int)])


# this is not thread-safe
class PerformanceMonitor(object):
    """
    Measure the resident memory occupied by a list of processes during
    the execution of a block of code. Should be used as a context manager,
    as follows::

     with PerformanceMonitor('do_something') as mon:
         do_something()
     print mon.mem

    At the end of the block the PerformanceMonitor object will have the
    following 5 public attributes:

    .start_time: when the monitor started (a datetime object)
    .duration: time elapsed between start and stop (in seconds)
    .exc: usually None; otherwise the exception happened in the `with` block
    .mem: the memory delta in bytes

    The behaviour of the PerformanceMonitor can be customized by subclassing it
    and by overriding the method on_exit(), called at end and used to display
    or store the results of the analysis.
    """
    def __init__(self, operation, hdf5path=None, pid=None,
                 autoflush=False, measuremem=False):
        self.operation = operation
        self.hdf5path = hdf5path
        self.pid = pid
        self.autoflush = autoflush
        self.measuremem = measuremem
        self.mem = 0
        self.duration = 0
        self._start_time = time.time()
        self.children = []

    def measure_mem(self):
        """A memory measurement (in bytes)"""
        try:
            if self.pid:
                proc = psutil.Process(self.pid)
                return memory_info(proc).rss
        except psutil.AccessDenied:
            # no access to information about this process
            # don't not try to check it anymore
            self.pid = 0

    @property
    def start_time(self):
        """
        Datetime instance recording when the monitoring started
        """
        return datetime.fromtimestamp(self._start_time)

    def get_data(self):
        """
        :returns:
            an array of dtype perf_dt, with the information of the monitor
            and its children (operation, time_sec, memory_mb, counts)

        .. note::

            at the moment only the direct children are retrieved, i.e.
            get_data is not recursive.
        """
        data = []
        monitors = [self] + self.children  # only direct children
        for mon in monitors:
            if mon.duration:
                time_sec = mon.duration
                memory_mb = mon.mem / 1024. / 1024. if mon.measuremem else 0
                data.append((mon.operation, time_sec, memory_mb, 1))
        return numpy.array(data, perf_dt)

    def __enter__(self):
        if self.pid is None:
            self.pid = os.getpid()
        self.exc = None  # exception
        self._start_time = time.time()
        if self.measuremem:
            self.start_mem = self.measure_mem()
        return self

    def __exit__(self, etype, exc, tb):
        self.exc = exc
        if self.measuremem:
            self.stop_mem = self.measure_mem()
            self.mem += self.stop_mem - self.start_mem
        self.duration += time.time() - self._start_time
        self.on_exit()

    def on_exit(self):
        "To be overridden in subclasses"
        if self.autoflush:
            self.flush()

    def flush(self):
        """
        Save the measurements on the performance file (or on stdout)
        """
        data = self.get_data()
        # reset monitors
        for mon in ([self] + self.children):
            mon.duration = 0
            mon.mem = 0

        if len(data) == 0:  # no information
            return
        if self.hdf5path:
            h5 = h5py.File(self.hdf5path)
            try:
                pdata = Hdf5Dataset(h5['performance_data'])
            except KeyError:
                pdata = Hdf5Dataset.create(h5, 'performance_data', perf_dt)
            pdata.extend(data)
            h5.close()
        else:  # print on stddout
            for rec in data:
                print(rec)

    def __call__(self, operation, **kw):
        """
        Return a child of the monitor usable for a different operation.
        """
        self_vars = vars(self).copy()
        del self_vars['operation']
        del self_vars['children']
        del self_vars['pid']
        new = self.__class__(operation)
        vars(new).update(self_vars)
        vars(new).update(kw)
        self.children.append(new)
        return new

    def __repr__(self):
        if self.measuremem:
            return '<%s %s, duration=%ss, memory=%s>' % (
                self.__class__.__name__, self.operation, self.duration,
                humansize(self.mem))
        return '<%s %s, duration=%ss>' % (self.__class__.__name__,
                                          self.operation, self.duration)


class DummyMonitor(PerformanceMonitor):
    """
    This class makes it easy to disable the monitoring in client code.
    Disabling the monitor can improve the performance.
    """
    def __init__(self, operation='dummy', *args, **kw):
        self.operation = operation
        self.hdf5path = None
        self.pid = None

    def __call__(self, operation, **kw):
        return self.__class__(operation)

    def __enter__(self):
        return self

    def __exit__(self, etype, exc, tb):
        pass

    def flush(self):
        pass

    def __repr__(self):
        return '<%s>' % self.__class__.__name__
