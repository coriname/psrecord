# Copyright (c) 2013, Thomas P. Robitaille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import (unicode_literals, division, print_function,
                        absolute_import)

import time
import argparse


def get_percent(process):
    try:
        # first call returns 0
        return process.cpu_percent(interval=0.01)
    except AttributeError:
        return process.get_cpu_percent()


def get_memory(process):
    try:
        return process.memory_info()
    except AttributeError:
        return process.get_memory_info()


def all_children(pr):        
    processes = []
    children = []
    try:
        children = pr.children(recursive=True)
    except AttributeError:
        children = pr.get_children()
    except Exception:  # pragma: no cover
        pass

    for child in children:
        try: 
            stat = child.status()
        except:
            continue
        if stat == 'running':
            processes.append(child)
            processes += all_children(child)
    return processes


def get_children_names(process):
    try:
        return process.name()
    except AttributeError:
        return process.get_name()
        

def get_process_group(log):
    prev = ''
    group={}
    cnt = -1
    for idx, elem in enumerate(log['name']):
        single_name = elem[-1]
        if elem!=prev:
            cnt += 1
            group[(cnt, single_name)] = []
        group[(cnt, single_name)].append(idx)
        prev = elem
    return group

def get_groupmempeak(group, log, count=10):
    import numpy as np
    peak_info_tmp = []
    for k,v in group.items():
        mem_group = [log['mem_real'][i] for i in v]
        max_idx = np.argmax(mem_group)
        max_mem_group = mem_group[max_idx]
        max_idx_group = v[max_idx]
        peak_info_tmp.append((k[1], max_idx_group, max_mem_group))
    peak_info_sorted = sorted(peak_info_tmp, key=lambda x: x[2], reverse=True)
    if count:
        peak_info = peak_info_sorted[0:count]
    return peak_info



def main():

    parser = argparse.ArgumentParser(
        description='Record CPU and memory usage for a process')

    parser.add_argument('process_id_or_command', type=str,
                        help='the process id or command')

    parser.add_argument('--log', type=str,
                        help='output the statistics to a file')

    parser.add_argument('--plot', type=str,
                        help='output the statistics to a plot')

    parser.add_argument('--duration', type=float,
                        help='how long to record for (in seconds). If not '
                             'specified, the recording is continuous until '
                             'the job exits.')

    parser.add_argument('--interval', type=float,
                        help='how long to wait between each sample (in '
                             'seconds). By default the process is sampled '
                             'as often as possible.')

    parser.add_argument('--include-children',
                        help='include sub-processes in statistics (results '
                             'in a slower maximum sampling rate).',
                        action='store_true')

    args = parser.parse_args()

    # Attach to process
    try:
        pid = int(args.process_id_or_command)
        print("Attaching to process {0}".format(pid))
        sprocess = None
    except Exception:
        import subprocess
        command = args.process_id_or_command
        print("Starting up command '{0}' and attaching to process"
              .format(command))
        sprocess = subprocess.Popen(command, shell=True)
        pid = sprocess.pid

    monitor(pid, logfile=args.log, plot=args.plot, duration=args.duration,
            interval=args.interval, include_children=args.include_children)

    if sprocess is not None:
        sprocess.kill()


def monitor(pid, logfile=None, plot=None, duration=None, interval=None,
            include_children=False):

    # We import psutil here so that the module can be imported even if psutil
    # is not present (for example if accessing the version)
    import psutil

    pr = psutil.Process(pid)

    # Record start time
    start_time = time.time()

    if logfile:
        f = open(logfile, 'w')
        f.write("# {0:12s} {1:12s} {2:12s} {3:12s} {4:255s}\n".format(
            'Elapsed time'.center(12),
            'CPU (%)'.center(12),
            'Real (MB)'.center(12),
            'Virtual (MB)'.center(12),
            'Process names'.center(20))
        )

    log = {}
    log['times'] = []
    log['cpu'] = []
    log['mem_real'] = []
    log['mem_virtual'] = []
    log['name'] = []

    try:

        # Start main event loop
        while True:

            # Find current time
            current_time = time.time()

            try:
                pr_status = pr.status()
            except TypeError:  # psutil < 2.0
                pr_status = pr.status
            except psutil.NoSuchProcess:  # pragma: no cover
                break

            # Check if process status indicates we should exit
            if pr_status in [psutil.STATUS_ZOMBIE, psutil.STATUS_DEAD]:
                print("Process finished ({0:.2f} seconds)"
                      .format(current_time - start_time))
                break

            # Check if we have reached the maximum time
            if duration is not None and current_time - start_time > duration:
                break

            # Get current CPU and memory
            current_name = []
            try:
                current_cpu = get_percent(pr)
                current_mem = get_memory(pr)
                current_name.append(pr.name())
            except Exception:
                break
            current_mem_real = current_mem.rss / 1024. ** 2
            current_mem_virtual = current_mem.vms / 1024. ** 2

            # Get information for children
            if include_children:
                for child in all_children(pr):
                    try:
                        current_cpu += get_percent(child)
                        current_mem = get_memory(child)
                        current_name.append(get_children_names(child))
                    except Exception:
                        continue
                    current_mem_real += current_mem.rss / 1024. ** 2
                    current_mem_virtual += current_mem.vms / 1024. ** 2

            if logfile:
                f.write("{0:12.3f} {1:12.3f} {2:12.3f} {3:12.3f} {4:255s}\n".format(
                    current_time - start_time,
                    current_cpu,
                    current_mem_real,
                    current_mem_virtual,
                    ','.join(current_name)))
                f.flush()

            if interval is not None:
                time.sleep(interval)

            # If plotting, record the values
            if plot:
                log['times'].append(current_time - start_time)
                log['cpu'].append(current_cpu)
                log['mem_real'].append(current_mem_real)
                log['mem_virtual'].append(current_mem_virtual)
                log['name'].append(current_name)

    except KeyboardInterrupt:  # pragma: no cover
        pass

    if logfile:
        f.close()

    if plot:
        process_group = get_process_group(log)
        mempeak_info = get_groupmempeak(process_group, log, count=10)

        # Use non-interactive backend, to enable operation on headless machines
        import matplotlib.pyplot as plt
        import matplotlib.gridspec as gridspec
        with plt.rc_context({'backend': 'Agg'}):

            fig = plt.figure(figsize=(10,6), dpi=150, facecolor='w')
            gs = gridspec.GridSpec(1,2, width_ratios=[4,1])
            ax = plt.subplot(gs[0])

            ax.plot(log['times'], log['cpu'], '-', lw=1, color='r')
            ax.set_ylabel('CPU (%)', color='r')
            ax.set_xlabel('time (s)')
            ax.set_ylim(0., max(log['cpu']) * 1.2)

            ax2 = ax.twinx()
            ax2.plot(log['times'], log['mem_real'], '-', lw=1, color='b')
            ax2.set_ylim(0., max(log['mem_real']) * 1.2)
            ax2.set_ylabel('Real Memory (MB)', color='b')
            
            ax.grid()
            
            ax_text = plt.subplot(gs[1])
            ax_text.text(0.1, 1, 'Top List - Memory Consumption:', {'ha': 'left', 'va': 'bottom'}, fontsize=8, transform=ax_text.transAxes)
            ax_text.set_axis_off()
            ax_text.yaxis.set_visible(False)
            ax_text.xaxis.set_visible(False)
            text_init = (0.15, 0.95)
            cnt = 0
            for elem in mempeak_info:
                cnt -= 0.03
                mem_str = "{:.2f}".format(elem[2])
                ax_text.text(text_init[0], text_init[1]+cnt, elem[0]+' - '+mem_str+'MB', {'ha': 'left', 'va': 'bottom'}, fontsize=8, transform=ax_text.transAxes)

            fig.savefig(plot)
