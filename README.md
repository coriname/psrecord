## About

The present repository is a fork of https://github.com/astrofrog/psrecord with minor modifications, especially for the output plot.

``psrecord`` is a small utility that uses the
`psutil <https://github.com/giampaolo/psutil/>`__ library to record the CPU
and memory activity of a process. The package is still under development
and is therefore experimental.

The code is released under a Simplified BSD License, which is given in
the ``LICENSE`` file.

## Installation

Within the institute, this package (and all its dependencies) is available within a virtual python environment.

To activate the environment on the blades do:

::

   source /beegfs/scratch/tnc_scratch/cmelzer/Develop/psrecord_env/bin/activate

If you want to create plots for visualising the process, make sure to login to the blades using:

::

	ssh -XY blade10

#### Requirements

For using this package outside the provided virtual environment, the following packages are required:

-  Python 2.7 or 3.3 and higher
-  `psutil <https://code.google.com/p/psutil/>`__ 1.0 or later
-  `matplotlib <http://www.matplotlib.org>`__ (optional, used for
   plotting)


## Usage

### Basics


To record the CPU and memory activity of an existing process to a file:

::

    psrecord 1330 --log activity.txt
	
So far, only running jobs will be considered for this monitoring. Thus jobs in sleep state will be ignored.

where ``1330`` is an example of a process ID which you can find with
``ps``, ``htop`` or ``top``. You can also use ``psrecord`` to start up a process
by specifying the command in quotes:

::

    psrecord "hyperion model.rtin model.rtout" --log activity.txt

### Plotting

To make a plot of the activity, you need to login to the blade using ``ssh -Y blade10``. Then use

::

    psrecord 1330 --plot plot.png

This will produce a plot such as:

.. image:: https://github.com/astrofrog/psrecord/raw/master/screenshot.png

You can combine these options to write the activity to a file and make a
plot at the same time:

::

    psrecord 1330 --log activity.txt --plot plot.png

To plot from a log file created previously:

::

	psrecord_plot logfile.log
	
A PNG with the same filename base as the logfile will be created.

### Duration and intervals

By default, the monitoring will continue until the process is stopped.
You can also specify a maximum duration in seconds:

::

    psrecord 1330 --log activity.txt --duration 10

Finally, the process is polled as often as possible by default, but it
is possible to set the time between samples in seconds:

::

    psrecord 1330 --log activity.txt --interval 2

### Subprocesses

To include sub-processes in the CPU and memory stats, use:

::

    psrecord 1330 --log activity.txt --include-children

