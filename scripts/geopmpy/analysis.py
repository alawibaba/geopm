#  Copyright (c) 2015, 2016, 2017, 2018, Intel Corporation
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#      * Redistributions of source code must retain the above copyright
#        notice, this list of conditions and the following disclaimer.
#
#      * Redistributions in binary form must reproduce the above copyright
#        notice, this list of conditions and the following disclaimer in
#        the documentation and/or other materials provided with the
#        distribution.
#
#      * Neither the name of Intel Corporation nor the names of its
#        contributors may be used to endorse or promote products derived
#        from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY LOG OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
GEOPM Analysis - Used to run applications and analyze results for specific GEOPM use cases.
"""

import argparse
import sys
import os
import glob
from collections import defaultdict
import socket
import json
import math
import numpy
import pandas
import subprocess

import geopmpy.io
import geopmpy.launcher
import geopmpy.plotter
from geopmpy import __version__


def all_region_data_pretty(combined_df):
    rs = 'All region data:\n'
    for region, df in combined_df.groupby('region'):
        df = df.sort_index(ascending=False)
        rs += '-' * 120 + '\n'
        rs += 'Region : {}\n'.format(region)
        rs += '{}\n'.format(df)
    rs += '-' * 120 + '\n'
    return rs


class LaunchConfig(object):
    def __init__(self, num_rank, num_node, app_argv,
                 geopm_ctl='process', do_geopm_barrier=False):
        self.num_rank = num_rank
        self.num_node = num_node
        self.app_argv = app_argv
        self.geopm_ctl = geopm_ctl
        self.do_geopm_barrier = do_geopm_barrier


class Analysis(object):
    """
    Base class for different types of analysis that use the data from geopm
    reports and/or logs. Implementations should define how to launch experiments,
    parse and process the output, and process text summaries or graphical plots.
    """

    @staticmethod
    def add_options(parser, enforce_required):
        """
        Set up options supported by the analysis type.
        """
        raise NotImplementedError('Analysis base class does not implement the app_options() method')

    @staticmethod
    def help_text():
        """
        Return the set of options supported by the analysis type.
        """
        raise NotImplementedError('Analysis base class does not implement the help_text() method')

    def __init__(self, profile_prefix, output_dir, verbose, iterations):
        self._name = profile_prefix
        self._output_dir = output_dir
        self._verbose = verbose
        self._iterations = iterations
        self._report_paths = []
        self._trace_paths = []
        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)

    def launch(self):
        """
        Run experiment and set data paths corresponding to output.
        """
        raise NotImplementedError('Analysis base class does not implement the launch() method')

    def find_files(self, search_pattern='*report'):
        """
        Uses the output dir and any custom naming convention to load the report and trace data
        produced by launch.
        """
        report_glob = self._name + search_pattern
        self.set_data_paths(report_glob)

    def set_data_paths(self, report_paths, trace_paths=None):
        """
        Set directory paths for report and trace files to be used in the analysis.
        """
        if not self._report_paths and not self._trace_paths:
            self._report_paths = report_paths
            self._trace_paths = trace_paths
        else:
            self._report_paths.extend(report_paths)
            if trace_paths is not None:
                self._trace_paths.extend(trace_paths)

    def parse(self):
        """
        Load any necessary data from the application result files into memory for analysis.
        """
        output = geopmpy.io.AppOutput(self._report_paths, None, dir_name=self._output_dir, verbose=True)
        return output.get_report_df()

    def plot_process(self, parse_output):
        """
        Process the parsed data into a form to be used for plotting (e.g. pandas dataframe).
        """
        raise NotImplementedError('Analysis base class does not implement the plot_process() method')

    def summary_process(self, parse_output):
        """
        Process the parsed data into a form to be used for the text summary.
        """
        raise NotImplementedError('Analysis base class does not implement the summary_process() method')

    def summary(self, process_output):
        """
        Print a text summary of the results.
        """
        raise NotImplementedError('Analysis base class does not implement the summary() method')

    def plot(self, process_output):
        """
        Generate graphical plots of the results.
        """
        raise NotImplementedError('Analysis base class does not implement the plot() method')


class PowerSweepAnalysis(Analysis):
    """
    Runs the application under a range of socket power limits.  Used
    by other analysis types to run either the PowerGovernorAgent or
    the PowerBalancerAgent.
    """

    @staticmethod
    def add_options(parser, enforce_required):
        """
        Set up options supported by the analysis type.
        """
        req_default = {'default': None}
        if enforce_required:
            req_default = {'required': True}
        parser.add_argument('--min-power', dest='min_power',
                            type=int, **req_default)
        parser.add_argument('--max-power', dest='max_power',
                            type=int, **req_default)
        parser.add_argument('--step-power', dest='step_power',
                            type=int, default=10)
        parser.add_argument('--agent-type', dest='agent_type',
                            type=str, required=False)

    @staticmethod
    def sys_power_avail():
        # TODO: this would be nicer with PlatformIO python API
        proc = subprocess.Popen(['geopmread', 'POWER_PACKAGE_MIN', 'package', '0'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        min_power = int(proc.stdout.readline().strip())
        proc = subprocess.Popen(['geopmread', 'POWER_PACKAGE_TDP', 'package', '0'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        tdp_power = int(proc.stdout.readline().strip())
        proc = subprocess.Popen(['geopmread', 'POWER_PACKAGE_MAX', 'package', '0'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        max_power = int(proc.stdout.readline().strip())

        return min_power, tdp_power, max_power

    # TODO : have this return left and right columns to be formatted by caller
    @staticmethod
    def help_text():
        return """  Power sweep analysis: {}
  Options for PowerSweepAnalysis:

  --min-power           Minimum power limit to use for sweep. Default uses system minimum.
  --max-power           Maximum power limit to use for sweep. Default uses system maximum.
  --step-power          Step size of power limits used in sweep.  Default is 10W.
  --agent-type          Specify which agent to use.  Default is power_governor.
""".format(PowerSweepAnalysis.__doc__)

    def __init__(self, profile_prefix, output_dir, verbose, iterations,
                 min_power, max_power, step_power, agent_type='power_governor'):
        super(PowerSweepAnalysis, self).__init__(profile_prefix, output_dir, verbose, iterations)
        self._min_power = min_power
        self._max_power = max_power
        self._step_power = step_power
        self._agent_type = agent_type

    def try_launch(self, profile_name, tag, iteration, agent_conf, config):
        # tag is used to differentiate output files for governor and balancer.  profile name will be the same.
        report_path = os.path.join(self._output_dir, profile_name + '_{}_{}.report'.format(tag, iteration))
        trace_path = os.path.join(self._output_dir, profile_name + '_{}_{}.trace'.format(tag, iteration))
        self._report_paths.append(report_path)
        self._trace_paths.append(trace_path+'*')

        if config.app_argv and not os.path.exists(report_path):
            argv = ['dummy', '--geopm-ctl', config.geopm_ctl,
                             '--geopm-agent', agent_conf.get_agent(),
                             '--geopm-policy', agent_conf.get_path(),
                             '--geopm-report', report_path,
                             '--geopm-trace', trace_path,
                             '--geopm-profile', profile_name]
            if config.do_geopm_barrier:
                argv.append('--geopm-barrier')
            argv.append('--')
            argv.extend(config.app_argv)
            launcher = geopmpy.launcher.factory(argv, config.num_rank, config.num_node)
            launcher.run()
        elif os.path.exists(report_path):
            sys.stderr.write('<geopmpy>: Warning: output file "{}" exists, skipping run.\n'.format(report_path))
        else:
            raise RuntimeError('<geopmpy>: output file "{}" does not exist, but no application was specified.\n'.format(report_path))

    def launch(self, config):
        sys_min, sys_tdp, sys_max = PowerSweepAnalysis.sys_power_avail()
        if self._min_power is None or self._min_power < sys_min:
            # system minimum is actually too low; use 50% of TDP or min rounded up to nearest step, whichever is larger
            self._min_power = max(int(0.5 * sys_tdp), sys_min)
            self._min_power = int(self._step_power * math.ceil(float(self._min_power)/self._step_power))
            sys.stderr.write("<geopmpy>: Warning: Invalid or unspecified min_power; using default minimum: {}.\n".format(self._min_power))
        if self._max_power is None or self._max_power > sys_max:
            self._max_power = sys_tdp
            sys.stderr.write("<geopmpy>: Warning: Invalid or unspecified max_power; using system TDP: {}.\n".format(self._max_power))

        power_caps = range(self._min_power, self._max_power+1, self._step_power)
        for power_cap in power_caps:
            # governor runs
            options = {'agent': self._agent_type,
                       'power_budget': power_cap},
            agent_conf = geopmpy.io.AgentConf(self._name + '_agent.config', options)
            agent_conf.write()

            for iteration in range(self._iterations):
                profile_name = self._name + '_' + str(power_cap)
                self.try_launch(profile_name, self._agent_type, iteration, agent_conf, config)

    @staticmethod
    def extract_index_from_profile(df):
        # Pull the power budget out of the profile name ('name' index field)
        profile_name_map = {}
        names_list = df.index.get_level_values('name').unique().tolist()
        for name in names_list:
            # The profile name is currently set to: ${NAME}_${POWER_BUDGET}
            profile_name_map.update({name: int(name.split('_')[-1])})
        df = df.rename(profile_name_map)
        return df

    def summary_process(self, parse_output):
        df = PowerSweepAnalysis.extract_index_from_profile(parse_output)
        idx = pandas.IndexSlice
        # profile name has been changed to power cap
        df = df.loc[idx[:, self._min_power:self._max_power, :, :, :,
                        self._agent_type, :, :, 'epoch'], ]
        summary = pandas.DataFrame()
        for col in ['count', 'runtime', 'mpi_runtime', 'energy_pkg', 'energy_dram', 'frequency']:
            summary[col] = df[col].groupby(level='name').mean()
        summary.index.rename('power cap', inplace=True)
        return summary

    def summary(self, process_output):
        rs = 'Summary for {} with {} agent\n'.format(self._name, self._agent_type)
        rs += process_output.to_string()
        sys.stdout.write(rs + '\n')

    def plot_process(self, parse_output):
        sys.stdout.write("<geopmpy>: Warning: No plot implemented for this analysis type.\n")

    def plot(self, process_output):
        pass


class BalancerAnalysis(Analysis):
    """
    Runs the application under a given range of power caps using both the governor
    and the balancer.  Compares the performance of the two agents at each power cap.
    """

    @staticmethod
    def add_options(parser, enforce_required):
        """
        Set up options supported by the analysis type.
        """
        PowerSweepAnalysis.add_options(parser, enforce_required)
        parser.add_argument('--metric', default='runtime')
        parser.add_argument('--normalize', action='store_true', default=False)
        parser.add_argument('--speedup', action='store_true', default=False)

    # TODO : have this return left and right columns to be formatted by caller
    @staticmethod
    def help_text():
        return """  Balancer analysis: {}
  Options for BalancerAnalysis:

  --metric              Metric to use for comparison (runtime, power, or energy).
  --normalize           Whether to normalize results to governor at highest power budget.
  --speedup             Plot the inverse of the target data to show speedup as a positive change.

{}""".format(BalancerAnalysis.__doc__, PowerSweepAnalysis.help_text())

    def __init__(self, profile_prefix, output_dir, verbose, iterations,
                 min_power, max_power, step_power, metric, normalize, speedup):
        super(BalancerAnalysis, self).__init__(profile_prefix, output_dir, verbose, iterations)
        self._governor_power_sweep = PowerSweepAnalysis(profile_prefix, output_dir, verbose, iterations,
                                                        min_power, max_power, step_power, 'power_governor')
        self._balancer_power_sweep = PowerSweepAnalysis(profile_prefix, output_dir, verbose, iterations,
                                                        min_power, max_power, step_power, 'power_balancer')
        self._metric = metric
        if self._metric == 'energy':
            self._metric = 'energy_pkg'
        self._normalize = normalize
        self._speedup = speedup

        self._min_power = min_power
        self._max_power = max_power

    # todo: why does each analysis need to define this?
    # a: in case of special naming convention like freq sweep
    def find_files(self, search_pattern='*report'):
        report_glob = os.path.join(self._output_dir, self._name + search_pattern)
        # todo: fix search pattern parameter
        trace_glob = os.path.join(self._output_dir, self._name + '*trace*')
        self.set_data_paths(glob.glob(report_glob), glob.glob(trace_glob))

    def launch(self, config):
        self._governor_power_sweep.launch(config)
        self._balancer_power_sweep.launch(config)

    def summary_process(self, parse_output):
        report_df = PowerSweepAnalysis.extract_index_from_profile(parse_output)
        report_df['power'] = report_df['energy_pkg'] / report_df['runtime']
        report_df.reset_index(['power_budget', 'tree_decider', 'leaf_decider'], drop=True, inplace=True)
        report_df.index = report_df.index.set_names('power_budget', level='name')

        # Data reduction - mean (if running more than 1 iteration, noop otherwise)
        mean_report_df = report_df.groupby(['power_budget', 'agent', 'node_name', 'region']).mean()
        mean_report_df = mean_report_df[['frequency', 'power', 'runtime', 'mpi_runtime', 'energy_pkg', 'count']]

        summary_df = mean_report_df.groupby(['power_budget', 'agent', 'region']).mean() # node_name not in group

        return report_df, mean_report_df, summary_df

    def summary(self, process_output):
        report_df, mean_report_df, summary_df = process_output
        idx = pandas.IndexSlice
        pandas.set_option('display.max_rows', None)

        if self._verbose:
            sys.stdout.write('Writing {}... '.format(os.path.join(self._output_dir, 'balancer.log')))
            sys.stdout.flush()
        with open(os.path.join(self._output_dir, 'balancer.log'), 'w') as out_file:
            """
            Writes epoch statistics for the Governor vs. Balancer comparisons.
            Results are aggregated so that all iterations and all nodes are averaged together.
            """
            epoch_report = summary_df.loc[idx[:, :, 'epoch'], ]
            out_file.write('=' * 80 + '\n')
            out_file.write('Governor stats :\n{}\n\n{}\nBalancer stats:\n{}\n\n'.format(
                           epoch_report.loc[idx[:, 'power_governor', :], ],
                           '-' * 80,
                           epoch_report.loc[idx[:, 'power_balancer', :], ]))
            out_file.write('=' * 80 + '\n\n')

            # Calculate percentage improvements
            a = epoch_report.loc[idx[:, 'power_governor', :], ['runtime', 'energy_pkg']].reset_index(level='agent', drop=True)
            b = epoch_report.loc[idx[:, 'power_balancer', :], ['runtime', 'energy_pkg']].reset_index(level='agent', drop=True)
            improvement = (a - b) / a # Result * 100 is percentage

            out_file.write('Balancer vs. Governor Improvement:\n\n{}\n\n'.format(improvement))
        if self._verbose:
            sys.stdout.write('Done.\n')
            sys.stdout.flush()

        if self._verbose:
            sys.stdout.write('Writing {}... '.format(os.path.join(self._output_dir, 'per_node.log')))
            sys.stdout.flush()
        with open(os.path.join(self._output_dir, 'per_node.log'), 'w') as out_file:
            """
            Writes the per_budget/per-region/all-nodes means to the log file.
            Writes the per-budget/per-node/per-region means to the log file.
            """
            out_file.write('All node Summary :\n{}\n\n'.format(summary_df))
            out_file.write('-' * 80 + '\n\n')
            out_file.write('Per-node / per-region stats :\n{}\n\n'.format(mean_report_df))
            out_file.write('=' * 80 + '\n\n')
        if self._verbose:
            sys.stdout.write('Done.\n')
            sys.stdout.flush()

        if self._verbose:
            sys.stdout.write('Writing {}... '.format(os.path.join(self._output_dir, 'per_region.log')))
            sys.stdout.flush()
        with open(os.path.join(self._output_dir, 'per_region.log'), 'w') as out_file:
            """
            Writes the per-budget/per-agent/per-region detailed stats to the log file.
                This includes mean, std, min, max, and the standard quartiles.
            """
            for (power_budget, region, agent), df in report_df.groupby(['power_budget', 'region', 'agent']):
                out_file.write('=' * 80 + '\n\n')
                out_file.write('{} W : Agent = {} : Region = {}\n'.format(power_budget, agent, region))
                out_file.write('{}\n\n'.format(df.describe()))
        if self._verbose:
            sys.stdout.write('Done.\n')
            sys.stdout.flush()

    def plot_process(self, parse_output):
        report_df = PowerSweepAnalysis.extract_index_from_profile(parse_output)
        idx = pandas.IndexSlice
        df = pandas.DataFrame()

        reference = 'static_policy'
        target = 'power_balancing'
        reference = 'power_governor'
        target = 'power_balancer'
        # TODO: have a separate power analysis?
        if self._metric == 'power':
            rge = report_df.loc[idx[:, self._min_power:self._max_power, :, :, :, reference, :, :, 'epoch'], 'energy_pkg']
            rgr = report_df.loc[idx[:, self._min_power:self._max_power, :, :, :, reference, :, :, 'epoch'], 'runtime']
            reference_g = (rge / rgr).groupby(level='name')
        else:
            reference_g = report_df.loc[idx[:, self._min_power:self._max_power, :, :, :, reference, :, :, 'epoch'],
                                        self._metric].groupby(level='name')

        df['reference_mean'] = reference_g.mean()
        df['reference_max'] = reference_g.max()
        df['reference_min'] = reference_g.min()
        if self._metric == 'power':
            tge = report_df.loc[idx[:, self._min_power:self._max_power, :, :, :, target, :, :, 'epoch'], 'energy_pkg']
            tgr = report_df.loc[idx[:, self._min_power:self._max_power, :, :, :, target, :, :, 'epoch'], 'runtime']
            target_g = (tge / tgr).groupby(level='name')
        else:
            target_g = report_df.loc[idx[:, self._min_power:self._max_power, :, :, :, target, :, :, 'epoch'],
                                     self._metric].groupby(level='name')

        df['target_mean'] = target_g.mean()
        df['target_max'] = target_g.max()
        df['target_min'] = target_g.min()

        if self._normalize and not self._speedup:  # Normalize the data against the rightmost reference bar
            df /= df['reference_mean'].iloc[-1]

        if self._speedup:  # Plot the inverse of the target data to show speedup as a positive change
            df = df.div(df['reference_mean'], axis='rows')
            df['target_mean'] = 1 / df['target_mean']
            df['target_max'] = 1 / df['target_max']
            df['target_min'] = 1 / df['target_min']

        # Convert the maxes and mins to be deltas from the mean; required for the errorbar API
        df['reference_max_delta'] = df['reference_max'] - df['reference_mean']
        df['reference_min_delta'] = df['reference_mean'] - df['reference_min']
        df['target_max_delta'] = df['target_max'] - df['target_mean']
        df['target_min_delta'] = df['target_mean'] - df['target_min']

        return df

    def plot(self, process_output):
        config = geopmpy.plotter.ReportConfig(output_dir=os.path.join(self._output_dir, 'figures'))
        config.output_types = ['png']
        config.verbose = True
        config.datatype = self._metric
        config.speedup = self._speedup
        config.normalize = self._normalize
        config.profile_name = self._name
        config.tgt_plugin = 'power_balancer'
        config.ref_plugin = 'power_governor'
        geopmpy.plotter.generate_bar_plot_comparison(process_output, config)


class NodeEfficiencyAnalysis(Analysis):
    """
    Generates a histogram per power cap of the frequency achieved in the epoch
    across nodes.
    """

    @staticmethod
    def add_options(parser, enforce_required):
        """
        Set up options supported by the analysis type.
        """
        PowerSweepAnalysis.add_options(parser, enforce_required)
        req_default = {'default': None}
        if enforce_required:
            req_default = {'required': True}
        parser.add_argument('--min-freq', dest='min_freq',
                            type=float, default=0.5e9)
        parser.add_argument('--max-freq', dest='max_freq',
                            type=float, default=3.0e9)
        parser.add_argument('--step-freq', dest='step_freq',
                            type=float, default=0.1e9)
        parser.add_argument('--sticker-freq', dest='sticker_freq',
                            type=float, **req_default)
        parser.add_argument('--nodelist',
                            type=str, default=None)

    # TODO : have this return left and right columns to be formatted by caller
    @staticmethod
    def help_text():
        return """  Node efficiency analysis: {}
  Options for NodeEfficiencyAnalysis:
  --min-freq            Minimum frequency to display for plotting.  Default is 0.5 GHz.
  --max-freq            Maximum frequency to display for plotting.  Default is 3.0 GHz.
  --step-freq           Size of frequency bins to use for plotting.  Default is 100 MHz.
  --sticker-freq        Sticker frequency of the system where data was collected.
                        If not provided, the current system sticker frequency will be used.
  --nodelist            Range of nodes separated by '-' to use for analysis. This option
                        is not used for launch and should contain a range of nodes
                        for which previously collected data is available.
{}""".format(NodeEfficiencyAnalysis.__doc__, PowerSweepAnalysis.help_text())

    # TODO: use configured agent type
    def __init__(self, profile_prefix, output_dir, verbose, iterations,
                 min_power, max_power, step_power,
                 min_freq, max_freq, step_freq, sticker_freq, nodelist):
        super(NodeEfficiencyAnalysis, self).__init__(profile_prefix, output_dir, verbose, iterations)
        self._governor_power_sweep = PowerSweepAnalysis(profile_prefix, output_dir, verbose, iterations,
                                                        min_power=min_power, max_power=max_power,
                                                        step_power=step_power, agent_type='power_governor')
        self._balancer_power_sweep = PowerSweepAnalysis(profile_prefix, output_dir, verbose, iterations,
                                                        min_power=min_power, max_power=max_power,
                                                        step_power=step_power, agent_type='power_balancer')

        self._min_freq = min_freq
        self._max_freq = max_freq
        self._step_freq = step_freq
        if not sticker_freq:
            sticker_freq = NodeEfficiencyAnalysis._find_sticker_freq()
        self._sticker_freq = sticker_freq
        self._min_power = min_power
        self._max_power = max_power
        self._step_power = step_power
        if nodelist:
            begin, end = tuple(nodelist.split('-'))
            self._nodelist = (begin, end)
        else:
            self._nodelist = None

    def launch(self, config):
        self._governor_power_sweep.launch(config)
        self._balancer_power_sweep.launch(config)

    def summary_process(self, parse_output):
        report_df = parse_output
        profiles = [int(pc.split('_')[-1]) for pc in report_df.index.get_level_values('name')]
        if not self._min_power:
            self._min_power = min(profiles)
        if not self._max_power:
            self._max_power = max(profiles)

        self._power_caps = range(self._min_power, self._max_power+1, self._step_power)
        gov_freq_data = {}
        bal_freq_data = {}

        begin_node = min(report_df.index.get_level_values('node_name'))
        end_node = max(report_df.index.get_level_values('node_name'))
        if self._nodelist:
            begin_node, end_node = self._nodelist
        for target_power in self._power_caps:
            profile = self._name + "_" + str(target_power)
            region_of_interest = 'epoch'
            # version name power_budget tree_decider leaf_decider agent node_name iteration region
            gov_freq_data[target_power] = report_df.loc[pandas.IndexSlice[:, profile, :, :, :, "power_governor", begin_node:end_node, :, region_of_interest], ]\
                                                   .groupby('node_name').mean()['frequency'].sort_values()
            bal_freq_data[target_power] = report_df.loc[pandas.IndexSlice[:, profile, :, :, :, "power_balancer", begin_node:end_node, :, region_of_interest], ]\
                                                   .groupby('node_name').mean()['frequency'].sort_values()
            # convert percent to GHz frequency based on sticker
            gov_freq_data[target_power] *= 0.01 * self._sticker_freq / 1e9
            bal_freq_data[target_power] *= 0.01 * self._sticker_freq / 1e9
            gov_freq_data[target_power] = pandas.DataFrame(gov_freq_data[target_power])
            bal_freq_data[target_power] = pandas.DataFrame(bal_freq_data[target_power])

        return gov_freq_data, bal_freq_data

    def summary(self, process_output):
        gov_freq_data, bal_freq_data = process_output
        for target_power in self._power_caps:
            gov_data = gov_freq_data[target_power].to_string()
            bal_data = bal_freq_data[target_power].to_string()
            #sys.stdout.write('Achieved frequencies at {}W with PowerGovernorAgent:\n'.format(target_power))
            #sys.stdout.write(gov_data + '\n')
            #sys.stdout.write('Achieved frequencies at {}W with PowerBalancerAgent:\n'.format(target_power))
            #sys.stdout.write(bal_data + '\n')
            # TODO: this is here to be consumed by another script that characterizes subsets of nodes.
            # range of nodes could also be an input option
            with open(os.path.join(self._output_dir, "gov_freq_{}.data".format(target_power)), "w") as outfile:
                outfile.write(gov_data)
            with open(os.path.join(self._output_dir, "bal_freq_{}.data".format(target_power)), "w") as outfile:
                outfile.write(bal_data)
        sys.stdout.write('Achieved frequencies summary written to {}/*.data.\n'.format(self._output_dir))

    def plot_process(self, parse_output):
        return self.summary_process(parse_output)

    def plot(self, process_output):
        all_gov_data, all_bal_data = process_output

        config = geopmpy.plotter.ReportConfig(output_dir=os.path.join(self._output_dir, 'figures'))
        config.output_types = ['png']
        config.verbose = True
        config.min_drop = self._min_freq / 1e9
        config.max_drop = (self._max_freq - self._step_freq) / 1e9
        bin_size = self._step_freq / 1e9

        for target_power in self._power_caps:
            gov_data = all_gov_data[target_power]
            bal_data = all_bal_data[target_power]
            #profile = self._name + "_" + str(target_power)

            config.profile_name = self._name + "@" + str(target_power) + "W Governor"
            geopmpy.plotter.generate_histogram(gov_data, config, 'frequency',
                                               bin_size, 3)
            config.profile_name = self._name + "@" + str(target_power) + "W Balancer"
            geopmpy.plotter.generate_histogram(bal_data, config, 'frequency',
                                               bin_size, 3)

    @staticmethod
    def _find_sticker_freq():
        # TODO: this would be nicer with PlatformIO python API
        proc = subprocess.Popen(['geopmread', 'CPUINFO::FREQ_STICKER', 'board', '0'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        res = proc.wait()
        if res != 0:
            cont = True
            err = ""
            while cont:
                line = proc.stderr.readline()
                if line:
                    err += line
                else:
                    cont = False
            raise RuntimeError("Unable to determine sticker_freq: " + err)
        return float(proc.stdout.readline().strip())


class NodePowerAnalysis(Analysis):
    """
    Generates a histogram of the achieved package power across nodes when the
    application is run without a power cap.
    """

    @staticmethod
    def add_options(parser, enforce_required):
        """
        Set up options supported by the analysis type.
        """
        # TODO: these have the same name as PowerSweepAnalysis, but different purpose.
        parser.add_argument('--min-power', dest='min_power',
                            type=int, default=120)
        parser.add_argument('--max-power', dest='max_power',
                            type=int, default=200)
        parser.add_argument('--step-power', dest='step_power',
                            type=int, default=10)

    # TODO : have this return left and right columns to be formatted by caller
    @staticmethod
    def help_text():
        return """  Node power analysis: {}
  Options for NodePowerAnalysis:
  --min-power           Minimum power to display for plotting.  Default is 120W.
  --max-power           Maximum power to display for plotting.  Default is 200W.
  --step-power          Size of power bins to use for plotting.  Default is 10W.
""".format(NodePowerAnalysis.__doc__)

    def __init__(self, profile_prefix, output_dir, verbose, iterations, min_power, max_power, step_power):
        super(NodePowerAnalysis, self).__init__(profile_prefix, output_dir, verbose, iterations)

        # min and max are only used for plot xaxis, not for launch
        self._min_power = min_power
        self._max_power = max_power
        self._step_power = step_power
        self._profile_name = self._name + '_' + str(self._max_power)  # '_nocap'  # TODO

    def launch(self, config):
        options = {'agent': 'monitor'}
        agent_conf = geopmpy.io.AgentConf(self._name + '_agent.config', options)
        agent_conf.write()

        for iteration in range(self._iterations):
            report_path = os.path.join(self._output_dir, self._profile_name + '_{}.report'.format(iteration))
            trace_path = os.path.join(self._output_dir, self._profile_name + '_{}.trace'.format(iteration))
            self._report_paths.append(report_path)
            self._trace_paths.append(trace_path+'*')

            if config.app_argv and not os.path.exists(report_path):
                argv = ['dummy', '--geopm-ctl', config.geopm_ctl,
                                 '--geopm-agent', agent_conf.get_agent(),
                                 '--geopm-policy', agent_conf.get_path(),
                                 '--geopm-report', report_path,
                                 '--geopm-trace', trace_path,
                                 '--geopm-profile', profile_name]
                if config.do_geopm_barrier:
                    argv.append('--geopm-barrier')
                argv.append('--')
                argv.extend(config.app_argv)
                launcher = geopmpy.launcher.factory(argv, config.num_rank, config.num_node)
                launcher.run()
            elif os.path.exists(report_path):
                sys.stderr.write('<geopmpy>: Warning: output file "{}" exists, skipping run.\n'.format(report_path))
            else:
                raise RuntimeError('<geopmpy>: output file "{}" does not exist, but no application was specified.\n'.format(report_path))

    def summary_process(self, parse_output):
        sys.stdout.write("<geopmpy>: Warning: No summary implemented for this analysis type.\n")

    def summary(self, process_output):
        pass

    def plot_process(self, parse_output):
        report_df = parse_output

        profile = self._profile_name

        region_of_interest = 'epoch'
        energy_data = report_df.loc[pandas.IndexSlice[:, profile, :, :, :, :, :, :, region_of_interest], ].groupby('node_name').mean()['energy_pkg'].sort_values()
        runtime_data = report_df.loc[pandas.IndexSlice[:, profile, :, :, :, :, :, :, region_of_interest], ].groupby('node_name').mean()['runtime'].sort_values()
        power_data = energy_data / runtime_data
        power_data = power_data.sort_values()
        power_data = pandas.DataFrame(power_data, columns=['power'])
        return power_data

    # Note: there is also a generate_power_plot method in plotter.
    def plot(self, process_output):
        config = geopmpy.plotter.ReportConfig(output_dir=os.path.join(self._output_dir, 'figures'))
        config.output_types = ['png']
        config.verbose = True
        config.profile_name = self._name
        config.min_drop = self._min_power
        config.max_drop = self._max_power - self._step_power

        bin_size = self._step_power

        geopmpy.plotter.generate_histogram(process_output, config, 'power',
                                           bin_size, 0)


class FreqSweepAnalysis(Analysis):
    """
    Runs the application at each available frequency. Compared to the baseline
    frequency, finds the lowest frequency for each region at which the performance
    will not be degraded by more than a given margin.
    """
    step_freq = 100e6
    # TODO: if doing skip launch, this should discover freq range from reports

    @staticmethod
    def add_options(parser, enforce_required):
        """
        Set up options supported by the analysis type.
        """
        req_default = {'default': None}
        if enforce_required:
            req_default = {'required': True}
        parser.add_argument('--min-freq', dest='min_freq',
                            type=float, **req_default)
        parser.add_argument('--max-freq', dest='max_freq',
                            type=float, **req_default)
        parser.add_argument('--enable-turbo', dest='enable_turbo',
                            action='store_true', default=False)

    # TODO : have this return left and right columns to be formatted by caller
    @staticmethod
    def help_text():
        return """  Frequency sweep analysis: {}
  Options for FreqSweepAnalysis:

  --min-freq            Minimum frequency to use for sweep. Default uses system minimum or minimum found in parsed data.
  --max-freq            Maximum frequency to use for sweep. Default uses system maximum or maximum found in parsed data.
  --enable-turbo        Allows turbo to be tested when determining best per-region frequencies. (default disables turbo)
""".format(FreqSweepAnalysis.__doc__)

    def __init__(self, profile_prefix, output_dir, verbose, iterations, min_freq, max_freq, enable_turbo):
        super(FreqSweepAnalysis, self).__init__(profile_prefix, output_dir, verbose, iterations)
        self._perf_margin = 0.1
        self._enable_turbo = enable_turbo
        self._min_freq = min_freq
        self._max_freq = max_freq

    def launch(self, config):
        if 'GEOPM_EFFICIENT_FREQ_RID_MAP' in os.environ:
            del os.environ['GEOPM_EFFICIENT_FREQ_RID_MAP']
        if 'GEOPM_EFFICIENT_FREQ_ONLINE' in os.environ:
            del os.environ['GEOPM_EFFICIENT_FREQ_ONLINE']

        sys_min, sys_max = FreqSweepAnalysis.sys_freq_avail()
        if self._min_freq is None or self._min_freq < sys_min:
            if self._verbose:
                sys.stderr.write("<geopmpy>: Warning: Invalid or unspecified min_freq; using system minimum: {}.\n".format(sys_min))
            self._min_freq = sys_min
        if self._max_freq is None or self._max_freq > sys_max:
            if self._verbose:
                sys.stderr.write("<geopmpy>: Warning: Invalid or unspecified max_freq; using system maximum: {}.\n".format(sys_max))
            self._max_freq = sys_max
        num_step = 1 + int((self._max_freq - self._min_freq) / FreqSweepAnalysis.step_freq)
        freqs = [FreqSweepAnalysis.step_freq * ss + self._min_freq for ss in range(num_step)]
        for iteration in range(self._iterations):
            for freq in freqs:
                profile_name = FreqSweepAnalysis.fixed_freq_name(self._name, freq)
                report_path = os.path.join(self._output_dir, profile_name + '_{}.report'.format(iteration))
                trace_path = os.path.join(self._output_dir, profile_name + '_{}.trace'.format(iteration))
                options = {'agent': 'energy_efficient',
                           'frequency_min': freq,
                           'frequency_max': freq}
                agent_conf = geopmpy.io.AgentConf(self._name + '_agent.config', options)
                agent_conf.write()
                if config.app_argv and not os.path.exists(report_path):
                    os.environ['GEOPM_EFFICIENT_FREQ_MIN'] = str(freq)
                    os.environ['GEOPM_EFFICIENT_FREQ_MAX'] = str(freq)
                    argv = ['dummy', '--geopm-ctl', config.geopm_ctl,
                                     '--geopm-agent', agent_conf.get_agent(),
                                     '--geopm-policy', agent_conf.get_path(),
                                     '--geopm-report', report_path,
                                     '--geopm-trace', trace_path,
                                     '--geopm-profile', profile_name]
                    if config.do_geopm_barrier:
                        argv.append('--geopm-barrier')
                    argv.append('--')
                    argv.extend(config.app_argv)
                    launcher = geopmpy.launcher.factory(argv, config.num_rank, config.num_node)
                    launcher.run()
                elif os.path.exists(report_path):
                    sys.stderr.write('<geopmpy>: Warning: output file "{}" exists, skipping run.\n'.format(report_path))
                else:
                    raise RuntimeError('<geopmpy>: output file "{}" does not exist, but no application was specified.\n'.format(report_path))

    def find_files(self):
        super(FreqSweepAnalysis, self).find_files('*_freq_*.report')

    def summary_process(self, parse_output):
        output = {}
        report_df = parse_output
        output['region_freq_map'] = self._region_freq_map(report_df)
        output['means_df'] = self._region_means_df(report_df)
        return output

    def summary(self, process_output):
        if self._verbose:
            sys.stdout.write(all_region_data_pretty(process_output['means_df']))

        region_freq_str = self._region_freq_str(process_output['region_freq_map'])
        sys.stdout.write(self._region_freq_str_pretty(process_output['region_freq_map']))

    def plot_process(self, parse_output):
        regions = parse_output.index.get_level_values('region').unique().tolist()
        return {region: self._runtime_energy_sweep(parse_output, region)
                for region in regions}

    def plot(self, process_output):
        for region, df in process_output.iteritems():
            geopmpy.plotter.generate_runtime_energy_plot(df, region, self._output_dir)

    def _region_freq_map(self, report_df):
        """
        Calculates the best-fit frequencies for each region for a single
        mix ratio.
        """
        optimal_freq = dict()
        min_runtime = dict()

        freq_pname = FreqSweepAnalysis.get_freq_profiles(report_df, self._name)

        is_once = True
        for freq, profile_name in freq_pname:

            # Since we are still attempting to perform a run in the turbo range, we need to skip this run when
            # determining the best per region frequencies below.  The profile_name that corresponds to the
            # turbo run is always the first in the list.
            if not self._enable_turbo and (freq, profile_name) == freq_pname[0]:
                continue

            region_mean_runtime = report_df.loc[pandas.IndexSlice[:, profile_name, :, :, :, :, :, :, :], ].groupby(level='region')
            for region, region_df in region_mean_runtime:
                runtime = region_df['runtime'].mean()
                if is_once:
                    min_runtime[region] = runtime
                    optimal_freq[region] = freq
                elif min_runtime[region] > runtime:
                    min_runtime[region] = runtime
                    optimal_freq[region] = freq
                elif min_runtime[region] * (1.0 + self._perf_margin) > runtime:
                    optimal_freq[region] = freq
            is_once = False
        return optimal_freq

    def _region_freq_str(self, region_freq_map):
        """
        Format the mapping of region names to their best-fit frequencies.
        """
        return json.dumps(region_freq_map)

    def _region_freq_str_pretty(self, region_freq_map):
        s = '\nRegion frequency map: \n'
        for k, v in region_freq_map.iteritems():
            s += '    {}: {}\n'.format(k, v)
        return s

    def _runtime_energy_sweep(self, df, region):
        freq_pname = FreqSweepAnalysis.get_freq_profiles(df, self._name)
        data = []
        freqs = []
        for freq, profile_name in freq_pname:
            freqs.append(freq)
            freq_df = df.loc[pandas.IndexSlice[:, profile_name, :, :, :, :, :, :, :], ]

            region_mean_runtime = freq_df.groupby(level='region')['runtime'].mean()
            region_mean_energy = freq_df.groupby(level='region')['energy_pkg'].mean()

            data.append([region_mean_runtime[region],
                         region_mean_energy[region]])

        return pandas.DataFrame(data,
                                index=freqs,
                                columns=['runtime', 'energy_pkg'])

    def _region_means_df(self, report_df):
        idx = pandas.IndexSlice

        report_df = FreqSweepAnalysis.profile_to_freq_mhz(report_df)

        cols = ['energy_pkg', 'runtime', 'mpi_runtime', 'frequency', 'count']

        means_df = report_df.groupby(['region', 'freq_mhz'])[cols].mean()
        # Define ref_freq to be three steps back from the end of the list.  The end of the list should always be
        # the turbo frequency.
        ref_freq = report_df.index.get_level_values('freq_mhz').unique().tolist()[-4]

        # Calculate the energy/runtime comparisons against the ref_freq
        ref_energy = means_df.loc[idx[:, ref_freq], ]['energy_pkg'].reset_index(level='freq_mhz', drop=True)
        es = pandas.Series((means_df['energy_pkg'] - ref_energy) / ref_energy, name='DCEngVar_%')
        means_df = pandas.concat([means_df, es], axis=1)

        ref_runtime = means_df.loc[idx[:, ref_freq], ]['runtime'].reset_index(level='freq_mhz', drop=True)
        rs = pandas.Series((means_df['runtime'] - ref_runtime) / ref_runtime, name='TimeVar_%')
        means_df = pandas.concat([means_df, rs], axis=1)

        bs = pandas.Series(means_df['runtime'] * (1.0 + self._perf_margin), name='runtime_bound')
        means_df = pandas.concat([means_df, bs], axis=1)

        # Calculate power and kwh
        p = pandas.Series(means_df['energy_pkg'] / means_df['runtime'], name='power')
        means_df = pandas.concat([means_df, p], axis=1)

        # Modify column order so that runtime bound occurs just after runtime
        cols = means_df.columns.tolist()
        tmp = cols.pop(7)
        cols.insert(2, tmp)

        return means_df[cols]

    @staticmethod
    def sys_freq_avail():
        """
        Returns a list of the available frequencies on the current platform.
        """
        with open('/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_min_freq') as fid:
            min_freq = 1e3 * float(fid.readline())
        with open('/proc/cpuinfo') as fid:
            for line in fid.readlines():
                if line.startswith('model name\t:'):
                    sticker_freq = float(line.split('@')[1].split('GHz')[0]) * 1e9
                    break
            max_freq = sticker_freq + FreqSweepAnalysis.step_freq

        return min_freq, max_freq

    @staticmethod
    def get_freq_profiles(df, prefix):
        """
        Finds all profiles from fixed frequency runs and returns the
        frequencies and profiles in decending order. Profile names should be formatted
        according to fixed_freq_name().
        """
        profile_name_list = df.index.get_level_values('name').unique().tolist()
        freq_list = [float(pn.split('_freq_')[-1].split('_')[0])
                     for pn in profile_name_list
                     if prefix in pn and '_freq_' in pn.split(prefix)[1]]
        freq_pname = zip(freq_list, profile_name_list)
        freq_pname.sort(reverse=True)
        return freq_pname

    @staticmethod
    def fixed_freq_name(prefix, freq):
        """Returns the formatted name for fixed frequency runs."""
        return '{}_freq_{}'.format(prefix, freq)

    @staticmethod
    def profile_to_freq_mhz(df):
        profile_name_map = {}
        names_list = df.index.get_level_values('name').unique().tolist()
        for name in names_list:
            profile_name_map[name] = int(float(name.split('_freq_')[-1]) * 1e-6)
        df = df.rename(profile_name_map)
        df.index = df.index.set_names('freq_mhz', level='name')
        return df


def baseline_comparison(parse_output, comp_name):
    """
    Used to compare a set of runs for a profile of interest to a baseline profile including verbose data.
    """
    comp_df = parse_output.loc[pandas.IndexSlice[:, comp_name, :, :, :, :, :, :, :], ]
    baseline_df = parse_output.loc[parse_output.index.get_level_values('name') != comp_name]
    baseline_df = FreqSweepAnalysis.profile_to_freq_mhz(baseline_df)

    # Reduce the data
    cols = ['energy_pkg', 'runtime', 'mpi_runtime', 'frequency', 'count']
    baseline_means_df = baseline_df.groupby(['region', 'freq_mhz'])[cols].mean()
    comp_means_df = comp_df.groupby(['region', 'name'])[cols].mean()

    # Add power column
    p = pandas.Series(baseline_means_df['energy_pkg'] / baseline_means_df['runtime'], name='power')
    baseline_means_df = pandas.concat([baseline_means_df, p], axis=1)
    p = pandas.Series(comp_means_df['energy_pkg'] / comp_means_df['runtime'], name='power')
    comp_means_df = pandas.concat([comp_means_df, p], axis=1)

    # Calculate energy savings
    es = pandas.Series((baseline_means_df['energy_pkg'] - comp_means_df['energy_pkg'].reset_index('name', drop=True))\
                       / baseline_means_df['energy_pkg'], name='energy_savings') * 100
    baseline_means_df = pandas.concat([baseline_means_df, es], axis=1)

    # Calculate runtime savings
    rs = pandas.Series((baseline_means_df['runtime'] - comp_means_df['runtime'].reset_index('name', drop=True))\
                       / baseline_means_df['runtime'], name='runtime_savings') * 100
    baseline_means_df = pandas.concat([baseline_means_df, rs], axis=1)

    return baseline_means_df


class OfflineBaselineComparisonAnalysis(Analysis):
    """
    Compares the energy efficiency plugin in offline mode to the
    baseline at sticker frequency.  Launches freq sweep and run to be
    compared.  Uses baseline comparison function to do analysis.
    """

    @staticmethod
    def add_options(parser, enforce_required):
        FreqSweepAnalysis.add_options(parser, enforce_required)

    @staticmethod
    def help_text():
        return "  Offline analysis: {}\n{}".format(OfflineBaselineComparisonAnalysis.__doc__, FreqSweepAnalysis.help_text())

    def __init__(self, profile_prefix, output_dir, verbose, iterations, min_freq, max_freq, enable_turbo):
        super(OfflineBaselineComparisonAnalysis, self).__init__(profile_prefix=profile_prefix,
                                                                output_dir=output_dir,
                                                                verbose=verbose,
                                                                iterations=iterations)
        self._sweep_analysis = FreqSweepAnalysis(profile_prefix=self._name,
                                                 output_dir=output_dir,
                                                 verbose=verbose,
                                                 iterations=iterations,
                                                 min_freq=min_freq,
                                                 max_freq=max_freq,
                                                 enable_turbo=enable_turbo)
        self._enable_turbo = enable_turbo
        self._sweep_parse_output = None
        self._freq_pnames = []
        self._min_freq = min_freq
        self._max_freq = max_freq

    def launch(self, config):
        """
        Run the frequency sweep, then run the desired comparison configuration.
        """
        options = {'agent': 'energy_efficient',
                   'frequency_min': self._min_freq,
                   'frequency_max': self._max_freq}
        agent_conf = geopmpy.io.AgentConf(self._name + '_agent.config', options)
        agent_conf.write()

        # Run frequency sweep
        self._sweep_analysis.launch(config)
        self._min_freq = self._sweep_analysis._min_freq
        self._max_freq = self._sweep_analysis._min_freq
        self._sweep_analysis.find_files()
        parse_output = self._sweep_analysis.parse()
        process_output = self._sweep_analysis.summary_process(parse_output)
        region_freq_str = self._sweep_analysis._region_freq_str(process_output['region_freq_map'])
        if self._verbose:
            sys.stdout.write(self._sweep_analysis._region_freq_str_pretty(process_output['region_freq_map']))

        # Run offline frequency agent
        for iteration in range(self._iterations):
            os.environ['GEOPM_EFFICIENT_FREQ_RID_MAP'] = region_freq_str
            if 'GEOPM_EFFICIENT_FREQ_ONLINE' in os.environ:
                del os.environ['GEOPM_EFFICIENT_FREQ_ONLINE']
            profile_name = self._name + '_offline'
            report_path = os.path.join(self._output_dir, profile_name + '_{}.report'.format(iteration))
            trace_path = os.path.join(self._output_dir, profile_name + '_{}.trace'.format(iteration))

            if config.app_argv and not os.path.exists(report_path):
                os.environ['GEOPM_EFFICIENT_FREQ_MIN'] = str(self._min_freq)
                os.environ['GEOPM_EFFICIENT_FREQ_MAX'] = str(self._max_freq)
                argv = ['dummy', '--geopm-ctl', config.geopm_ctl,
                                 '--geopm-agent', agent_conf.get_agent(),
                                 '--geopm-policy', agent_conf.get_path(),
                                 '--geopm-report', report_path,
                                 '--geopm-trace', trace_path,
                                 '--geopm-profile', profile_name]
                if config.do_geopm_barrier:
                    argv.append('--geopm-barrier')
                argv.append('--')
                argv.extend(config.app_argv)
                launcher = geopmpy.launcher.factory(argv, config.num_rank, config.num_node)
                launcher.run()
            elif os.path.exists(report_path):
                sys.stderr.write('<geopmpy>: Warning: output file "{}" exists, skipping run.\n'.format(report_path))
            else:
                raise RuntimeError('<geopmpy>: output file "{}" does not exist, but no application was specified.\n'.format(report_path))

    def find_files(self):
        super(OfflineBaselineComparisonAnalysis, self).find_files('*_offline*.report')
        self._sweep_analysis.find_files()

    def parse(self):
        """
        Combines reports from the sweep with other reports to be
        compared, which are determined by the profile name passed at
        construction time.
        """
        # each keeps track of only their own report paths, so need to combine parses
        sweep_output = self._sweep_analysis.parse()
        app_output = super(OfflineBaselineComparisonAnalysis, self).parse()
        self._sweep_parse_output = sweep_output

        # Print the region frequency map
        sweep_summary_process = self._sweep_analysis.summary_process(sweep_output)
        region_freq_str = self._sweep_analysis._region_freq_str(sweep_summary_process['region_freq_map'])
        sys.stdout.write(self._sweep_analysis._region_freq_str_pretty(sweep_summary_process['region_freq_map']))

        self._freq_pnames = FreqSweepAnalysis.get_freq_profiles(self._sweep_parse_output, self._sweep_analysis._name)

        parse_output = self._sweep_parse_output.append(app_output)
        parse_output.sort_index(ascending=True, inplace=True)

        return parse_output

    def summary_process(self, parse_output):
        comp_name = self._name + '_offline'
        baseline_comp_df = baseline_comparison(parse_output, comp_name)
        return baseline_comp_df

    def summary(self, process_output):
        name = self._name + '_offline'
        ref_freq_idx = 0 if self._enable_turbo else 1
        ref_freq = int(self._freq_pnames[ref_freq_idx][0] * 1e-6)

        rs = 'Summary for {}\n\n'.format(name)
        rs += 'Energy Decrease compared to {} MHz: {:.2f}%\n'.format(ref_freq, process_output.loc[pandas.IndexSlice['epoch', ref_freq], 'energy_savings'])
        rs += 'Runtime Decrease compared to {} MHz: {:.2f}%\n\n'.format(ref_freq, process_output.loc[pandas.IndexSlice['epoch', ref_freq], 'runtime_savings'])
        rs += 'Epoch data:\n'
        rs += str(process_output.loc[pandas.IndexSlice['epoch', :], ].sort_index(ascending=False)) + '\n'
        rs += '-' * 120 + '\n'
        sys.stdout.write(rs + '\n')

        if self._verbose:
            sweep_means_df = self._sweep_analysis._region_means_df(self._sweep_parse_output)
            rs = '=' * 120 + '\n'
            rs += 'Frequency Sweep Data\n'
            rs += '=' * 120 + '\n'
            rs += all_region_data_pretty(sweep_means_df)
            rs += '=' * 120 + '\n'
            rs += 'Offline Analysis Data\n'
            rs += '=' * 120 + '\n'
            rs += all_region_data_pretty(process_output)
            sys.stdout.write(rs + '\n')

    def plot_process(self, parse_output):
        sys.stdout.write("<geopmpy>: Warning: No plot implemented for this analysis type.\n")

    def plot(self, process_output):
        pass


class OnlineBaselineComparisonAnalysis(Analysis):
    """
    Compares the energy efficiency plugin in online mode to the
    baseline at sticker frequency.  Launches freq sweep and run to be
    compared.  Uses baseline comparison function to do analysis.
    """

    @staticmethod
    def add_options(parser, enforce_required):
        FreqSweepAnalysis.add_options(parser, enforce_required)

    @staticmethod
    def help_text():
        return "  Online analysis: {}\n{}".format(OnlineBaselineComparisonAnalysis.__doc__, FreqSweepAnalysis.help_text())

    def __init__(self, profile_prefix, output_dir, verbose, iterations, min_freq, max_freq, enable_turbo):
        super(OnlineBaselineComparisonAnalysis, self).__init__(profile_prefix=profile_prefix,
                                                               output_dir=output_dir,
                                                               verbose=verbose,
                                                               iterations=iterations)
        self._sweep_analysis = FreqSweepAnalysis(profile_prefix=self._name,
                                                 output_dir=output_dir,
                                                 verbose=verbose,
                                                 iterations=iterations,
                                                 min_freq=min_freq,
                                                 max_freq=max_freq,
                                                 enable_turbo=enable_turbo)
        self._enable_turbo = enable_turbo
        self._freq_pnames = []
        self._min_freq = min_freq
        self._max_freq = max_freq

    def launch(self, config):
        """
        Run the frequency sweep, then run the desired comparison configuration.
        """
        # Run frequency sweep
        self._sweep_analysis.launch(config)
        self._min_freq = self._sweep_analysis._min_freq
        self._max_freq = self._sweep_analysis._min_freq

        # Run online frequency agent
        for iteration in range(self._iterations):
            os.environ['GEOPM_EFFICIENT_FREQ_ONLINE'] = 'yes'
            if 'GEOPM_EFFICIENT_FREQ_RID_MAP' in os.environ:
                del os.environ['GEOPM_EFFICIENT_FREQ_RID_MAP']

            profile_name = self._name + '_online'
            report_path = os.path.join(self._output_dir, profile_name + '_{}.report'.format(iteration))
            trace_path = os.path.join(self._output_dir, profile_name + '_{}.trace'.format(iteration))

            options = {'agent': 'energy_efficient',
                       'frequency_min': self._min_freq,
                       'frequency_max': self._max_freq}
            agent_conf = geopmpy.io.AgentConf(self._name + '_agent.config', options)
            agent_conf.write()
            if config.app_argv and not os.path.exists(report_path):
                os.environ['GEOPM_EFFICIENT_FREQ_MIN'] = str(self._min_freq)
                os.environ['GEOPM_EFFICIENT_FREQ_MAX'] = str(self._max_freq)
                argv = ['dummy', '--geopm-ctl', config.geopm_ctl,
                                 '--geopm-agent', agent_conf.get_agent(),
                                 '--geopm-policy', agent_conf.get_path(),
                                 '--geopm-report', report_path,
                                 '--geopm-trace', trace_path,
                                 '--geopm-profile', profile_name]
                if config.do_geopm_barrier:
                    argv.append('--geopm-barrier')
                argv.append('--')
                argv.extend(config.app_argv)
                launcher = geopmpy.launcher.factory(argv, config.num_rank, config.num_node)
                launcher.run()
            elif os.path.exists(report_path):
                sys.stderr.write('<geopmpy>: Warning: output file "{}" exists, skipping run.\n'.format(report_path))
            else:
                raise RuntimeError('<geopmpy>: output file "{}" does not exist, but no application was specified.\n'.format(report_path))

    def find_files(self):
        super(OnlineBaselineComparisonAnalysis, self).find_files('*_online*.report')
        self._sweep_analysis.find_files()

    def parse(self):
        """
        Combines reports from the sweep with other reports to be
        compared, which are determined by the profile name passed at
        construction time.
        """
        # each keeps track of only their own report paths, so need to combine parses
        sweep_output = self._sweep_analysis.parse()
        app_output = super(OnlineBaselineComparisonAnalysis, self).parse()
        parse_output = sweep_output

        # Print the region frequency map
        sweep_summary_process = self._sweep_analysis.summary_process(sweep_output)
        region_freq_str = self._sweep_analysis._region_freq_str(sweep_summary_process['region_freq_map'])
        sys.stdout.write(self._sweep_analysis._region_freq_str_pretty(sweep_summary_process['region_freq_map']))

        self._freq_pnames = FreqSweepAnalysis.get_freq_profiles(parse_output, self._sweep_analysis._name)
        parse_output = parse_output.append(app_output)
        parse_output.sort_index(ascending=True, inplace=True)
        return parse_output

    def summary_process(self, parse_output):
        comp_name = self._name + '_online'
        baseline_comp_df = baseline_comparison(parse_output, comp_name)
        return baseline_comp_df

    def summary(self, process_output):
        name = self._name + '_online'
        ref_freq_idx = 0 if self._enable_turbo else 1
        ref_freq = int(self._freq_pnames[ref_freq_idx][0] * 1e-6)

        rs = 'Summary for {}\n\n'.format(name)
        rs += 'Energy Decrease compared to {} MHz: {:.2f}%\n'.format(ref_freq, process_output.loc[pandas.IndexSlice['epoch', ref_freq], 'energy_savings'])
        rs += 'Runtime Decrease compared to {} MHz: {:.2f}%\n\n'.format(ref_freq, process_output.loc[pandas.IndexSlice['epoch', ref_freq], 'runtime_savings'])
        rs += 'Epoch data:\n'
        rs += str(process_output.loc[pandas.IndexSlice['epoch', :], ].sort_index(ascending=False)) + '\n'
        rs += '-' * 120 + '\n'
        sys.stdout.write(rs + '\n')

        if self._verbose:
            rs = '=' * 120 + '\n'
            rs += 'Online Analysis Data\n'
            rs += '=' * 120 + '\n'
            rs += all_region_data_pretty(process_output)
            sys.stdout.write(rs)

    def plot_process(self, parse_output):
        sys.stdout.write("<geopmpy>: Warning: No plot implemented for this analysis type.\n")

    def plot(self, process_output):
        pass


class StreamDgemmMixAnalysis(Analysis):
    """
    Runs a full frequency sweep, then offline and online modes of the
    energy efficieny plugin. The energy and runtime of the
    application best-fit, per-phase offline mode, and per-phase
    online mode are compared to the run a sticker frequency.
    """

    @staticmethod
    def add_options(parser, enforce_required):
        FreqSweepAnalysis.add_options(parser, enforce_required)

    @staticmethod
    def help_text():
        return "  Stream-DGEMM mix analysis: {}\n{}".format(StreamDgemmMixAnalysis.__doc__, FreqSweepAnalysis.help_text())

    def __init__(self, profile_prefix, output_dir, verbose, iterations, min_freq, max_freq, enable_turbo):
        super(StreamDgemmMixAnalysis, self).__init__(profile_prefix=profile_prefix,
                                                     output_dir=output_dir,
                                                     verbose=verbose,
                                                     iterations=iterations)

        self._enable_turbo = enable_turbo
        self._sweep_analysis = {}
        self._offline_analysis = {}
        self._online_analysis = {}
        self._min_freq = min_freq
        self._max_freq = max_freq
        self._mix_ratios = [(1.0, 0.25), (1.0, 0.5), (1.0, 0.75), (1.0, 1.0),
                            (0.75, 1.0), (0.5, 1.0), (0.25, 1.0)]
        loop_count = 10
        dgemm_bigo = 20.25
        stream_bigo = 1.449
        dgemm_bigo_jlse = 35.647
        dgemm_bigo_quartz = 29.12
        stream_bigo_jlse = 1.6225
        stream_bigo_quartz = 1.7941
        hostname = socket.gethostname()
        if hostname.endswith('.alcf.anl.gov'):
            dgemm_bigo = dgemm_bigo_jlse
            stream_bigo = stream_bigo_jlse
        else:
            dgemm_bigo = dgemm_bigo_quartz
            stream_bigo = stream_bigo_quartz

        for (ratio_idx, ratio) in enumerate(self._mix_ratios):
            profile_prefix = self._name + '_mix_{}'.format(ratio_idx)
            app_conf_name = os.path.join(self._output_dir, profile_prefix + '_app.config')
            app_conf = geopmpy.io.BenchConf(app_conf_name)
            app_conf.set_loop_count(loop_count)
            app_conf.append_region('dgemm',  ratio[0] * dgemm_bigo)
            app_conf.append_region('stream', ratio[1] * stream_bigo)
            app_conf.append_region('all2all', 1.0)
            app_conf.write()

            source_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            app_path = os.path.join(source_dir, '.libs', 'geopmbench')
            # if not found, use geopmbench from user's PATH
            if not os.path.exists(app_path):
                app_path = "geopmbench"
            app_argv = [app_path, app_conf_name]
            # Analysis class that runs the frequency sweep (will append _freq_XXXX to name)
            self._sweep_analysis[ratio_idx] = FreqSweepAnalysis(profile_prefix=profile_prefix,
                                                                output_dir=self._output_dir,
                                                                verbose=self._verbose,
                                                                iterations=self._iterations,
                                                                min_freq=self._min_freq,
                                                                max_freq=self._max_freq,
                                                                enable_turbo=self._enable_turbo)
            # Analysis class that includes a full sweep plus the plugin run with freq map
            self._offline_analysis[ratio_idx] = OfflineBaselineComparisonAnalysis(profile_prefix=profile_prefix,
                                                                                  output_dir=self._output_dir,
                                                                                  verbose=self._verbose,
                                                                                  iterations=self._iterations,
                                                                                  min_freq=self._min_freq,
                                                                                  max_freq=self._max_freq,
                                                                                  enable_turbo=self._enable_turbo)
            # Analysis class that runs the online plugin
            self._online_analysis[ratio_idx] = OnlineBaselineComparisonAnalysis(profile_prefix=profile_prefix,
                                                                                output_dir=self._output_dir,
                                                                                verbose=self._verbose,
                                                                                iterations=self._iterations,
                                                                                min_freq=self._min_freq,
                                                                                max_freq=self._max_freq,
                                                                                enable_turbo=self._enable_turbo)

    def launch(self, config):
        for (ratio_idx, ratio) in enumerate(self._mix_ratios):
            self._sweep_analysis[ratio_idx].launch(config)
            self._offline_analysis[ratio_idx].launch(config)
            self._online_analysis[ratio_idx].launch(config)

    def find_files(self):
        super(StreamDgemmMixAnalysis, self).find_files('*_mix*report')

    def parse(self):
        parse_output = super(StreamDgemmMixAnalysis, self).parse()
        return parse_output

    def summary_process(self, parse_output):
        df = parse_output
        name_prefix = self._name

        runtime_data = []
        energy_data = []
        app_freq_data = []
        online_freq_data = []
        series_names = ['offline application', 'offline per-phase', 'online per-phase']
        regions = df.index.get_level_values('region').unique().tolist()

        energy_result_df = pandas.DataFrame()
        runtime_result_df = pandas.DataFrame()
        for (ratio_idx, ratio) in enumerate(self._mix_ratios):
            name = self._name + '_mix_{}'.format(ratio_idx)

            optimal_freq = self._sweep_analysis[ratio_idx]._region_freq_map(df)

            freq_temp = [optimal_freq[region]
                         for region in sorted(regions)]
            app_freq_data.append(freq_temp)

            freq_pname = FreqSweepAnalysis.get_freq_profiles(parse_output, name)

            baseline_freq, baseline_name = freq_pname[0]
            best_fit_freq = optimal_freq['epoch']
            best_fit_name = FreqSweepAnalysis.fixed_freq_name(name, best_fit_freq)

            baseline_df = df.loc[pandas.IndexSlice[:, baseline_name, :, :, :, :, :, :, :], ]

            best_fit_df = df.loc[pandas.IndexSlice[:, best_fit_name, :, :, :, :, :, :, :], ]
            combo_df = baseline_df.append(best_fit_df)
            comp_df = baseline_comparison(combo_df, best_fit_name)
            offline_app_energy = comp_df.loc[pandas.IndexSlice['epoch', int(baseline_freq * 1e-6)], 'energy_savings']
            offline_app_runtime = comp_df.loc[pandas.IndexSlice['epoch', int(baseline_freq * 1e-6)], 'runtime_savings']

            offline_df = df.loc[pandas.IndexSlice[:, name + '_offline', :, :, :, :, :, :, :], ]
            combo_df = baseline_df.append(offline_df)
            comp_df = baseline_comparison(combo_df, name + '_offline')
            offline_phase_energy = comp_df.loc[pandas.IndexSlice['epoch', int(baseline_freq * 1e-6)], 'energy_savings']
            offline_phase_runtime = comp_df.loc[pandas.IndexSlice['epoch', int(baseline_freq * 1e-6)], 'runtime_savings']

            online_df = df.loc[pandas.IndexSlice[:, name + '_online', :, :, :, :, :, :, :], ]
            combo_df = baseline_df.append(online_df)
            comp_df = baseline_comparison(combo_df, name + '_online')
            online_phase_energy = comp_df.loc[pandas.IndexSlice['epoch', int(baseline_freq * 1e-6)], 'energy_savings']
            online_phase_runtime = comp_df.loc[pandas.IndexSlice['epoch', int(baseline_freq * 1e-6)], 'runtime_savings']

            row = pandas.DataFrame([[offline_app_energy, offline_phase_energy, online_phase_energy]],
                                   columns=series_names, index=[ratio_idx])
            energy_result_df = energy_result_df.append(row)

            row = pandas.DataFrame([[offline_app_runtime, offline_phase_runtime, online_phase_runtime]],
                                   columns=series_names, index=[ratio_idx])
            runtime_result_df = runtime_result_df.append(row)

        # produce combined output
        app_freq_df = pandas.DataFrame(app_freq_data, columns=sorted(regions))
        return energy_result_df, runtime_result_df, app_freq_df

    def plot_process(self, parse_output):
        return self.summary_process(parse_output)

    def summary(self, process_output):
        rs = 'Summary:\n'
        energy_result_df, runtime_result_df, app_freq_df = process_output
        rs += 'Energy\n'
        rs += '{}\n'.format(energy_result_df)
        rs += 'Runtime\n'
        rs += '{}\n'.format(runtime_result_df)
        rs += 'Application best-fit frequencies\n'
        rs += '{}\n'.format(app_freq_df)
        sys.stdout.write(rs)
        return rs

    def plot(self, process_output):
        sys.stdout.write('Plot:\n')
        energy_result_df, runtime_result_df, app_freq_df = process_output
        geopmpy.plotter.generate_bar_plot_sc17(energy_result_df, 'Energy-to-Solution Decrease', self._output_dir)
        geopmpy.plotter.generate_bar_plot_sc17(runtime_result_df, 'Time-to-Solution Increase', self._output_dir)
        geopmpy.plotter.generate_app_best_freq_plot_sc17(app_freq_df, 'Offline auto per-phase best-fit frequency', self._output_dir)


def main(argv):
    help_str = """
Usage: {argv_0} [-h|--help] [--version]
       {argv_0} ANALYSIS_TYPE --help
       {argv_0} ANALYSIS_TYPE [-n NUM_RANK -N NUM_NODE | --skip-launch ]
                [-p PROFILE_PREFIX] [--iterations ITERATIONS] [--verbose]
                [--summary] [--plot] [-o OUTPUT_DIR] -- EXEC [EXEC_ARGS]

geopmanalysis - Used to run applications and analyze results for specific
                GEOPM use cases.

  ANALYSIS_TYPE values: freq_sweep, offline, online, stream_mix,
                        power_sweep, balancer, node_efficiency,
                        node_power.

  -h, --help            show this help message and exit
  -t, --analysis-type   type of analysis to perform
  -n, --num-rank        total number of application ranks to launch with
  -N, --num-node        number of compute nodes to launch onto
  -o, --output-dir      the output directory for reports, traces, and plots (default '.')
  -p, --profile-prefix  prefix to prepend to profile name when launching
  --summary             create a text summary of the results
  --plot                generate plots of the results
  -a, --use-agent       temporary option that enables the new agent code path
  -s, --skip-launch     do not launch jobs, only analyze existing data
  -v, --verbose         print verbose debugging information
  --geopm-ctl           launch type for the GEOPM controller (default 'process')
  --iterations          number of experiments to run per analysis type
  --version             show the GEOPM version number and exit

""".format(argv_0=sys.argv[0])
    version_str = """\
GEOPM version {version}
Copyright (c) 2015, 2016, 2017, 2018, Intel Corporation. All rights reserved.
""".format(version=__version__)

    analysis_type_map = {'freq_sweep': FreqSweepAnalysis,
                         'offline': OfflineBaselineComparisonAnalysis,
                         'online': OnlineBaselineComparisonAnalysis,
                         'stream_mix': StreamDgemmMixAnalysis,
                         'power_sweep': PowerSweepAnalysis,
                         'balancer': BalancerAnalysis,
                         'node_efficiency': NodeEfficiencyAnalysis,
                         'node_power': NodePowerAnalysis}

    if '--help' in argv or '-h' in argv:
        sys.stdout.write(help_str)
        if len(argv) >= 2 and argv[0] in analysis_type_map:
            sys.stdout.write(analysis_type_map[argv[0]].help_text())
        return 0
    if '--version' in argv:
        sys.stdout.write(version_str)
        return 0

    if os.getenv("GEOPM_AGENT", None) is not None:
        raise RuntimeError('Use --use-agent option instead of environment variable to enable agent code path.')

    if len(argv) < 1:
        sys.stderr.write("<geopmpy> Error: analysis type is required.\n")
        sys.stderr.write(help_str)
        return 1
    analysis_type = argv[0]
    argv = argv[1:]

    if analysis_type not in analysis_type_map:
        raise SyntaxError('Analysis type "{}" unrecognized. Available types: {}'.format(analysis_type, ' '.join(analysis_type_map.keys())))

    # Common arguments
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     add_help=False,
                                     argument_default=argparse.SUPPRESS)

    parser.add_argument('-n', '--num-rank', dest='num_rank',
                        action='store', default=None, type=int)
    parser.add_argument('-N', '--num-node', dest='num_node',
                        action='store', default=None, type=int)
    parser.add_argument('-o', '--output-dir', dest='output_dir',
                        action='store', default='.')
    parser.add_argument('-p', '--profile-prefix', dest='profile_prefix',
                        action='store', default='')
    parser.add_argument('app_argv', metavar='APP_ARGV',
                        action='store', nargs='*', default=None)
    parser.add_argument('-s', '--skip-launch', dest='skip_launch',
                        action='store_true', default=False)
    parser.add_argument('--geopm-ctl', dest='geopm_ctl',
                        action='store', default='process')
    parser.add_argument('--iterations',
                        action='store', default=1, type=int)
    parser.add_argument('-v', '--verbose',
                        action='store_true', default=False)
    parser.add_argument('--summary',
                        action='store_true', default=False)
    parser.add_argument('--plot',
                        action='store_true', default=False)

    # special options for the analysis type
    enforce_required = False
    if '--skip-launch' in argv or '-s' in argv:
        enforce_required = True
    analysis_type_map[analysis_type].add_options(parser, enforce_required)

    args = parser.parse_args(argv)
    options = vars(args)

    skip_launch = options.pop('skip_launch')
    do_summary = options.pop('summary')
    do_plot = options.pop('plot')

    # TODO: I think iterations can be a launch option too
    launch_options = {}
    for opt in ['num_rank', 'num_node', 'geopm_ctl', 'app_argv']:
        launch_options[opt] = options.pop(opt)

    analysis = analysis_type_map[analysis_type](**options)

    if not skip_launch:
        # if launching, must run within an allocation to make sure all runs use
        # the same set of nodes
        if launch_options['num_rank'] is None or launch_options['num_node'] is None:
            raise RuntimeError('--num-rank and --num-node are required for launch; use --skip-launch to run analysis only.')
        if 'SLURM_NNODES' in os.environ:
            num_node = int(os.getenv('SLURM_NNODES'))
        elif 'COBALT_NODEFILE' in os.environ:
            with open(os.getenv('COBALT_NODEFILE')) as fid:
                num_node = len(fid.readlines())
        else:
            num_node = -1
        if num_node != launch_options['num_node']:
            raise RuntimeError('Launch must be made inside of a job allocation and application must run on all allocated nodes.')

        launch_config = LaunchConfig(do_geopm_barrier=False, **launch_options)
        analysis.launch(launch_config)

    if do_summary or do_plot:
        analysis.find_files()
        parse_output = analysis.parse()
    else:
        sys.stdout.write("Neither summary nor plot was generated.  Rerun with --summary and/or --plot to perform analysis.\n")
    if do_summary:
        process_output = analysis.summary_process(parse_output)
        analysis.summary(process_output)
    if do_plot:
        process_output = analysis.plot_process(parse_output)
        analysis.plot(process_output)

    return 0
