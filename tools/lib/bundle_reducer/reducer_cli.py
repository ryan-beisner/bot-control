#!/usr/bin/python3

# This file is part of bundlereducer, a tool to extract topology
# subsets from deployer bundle yaml files.
#
# Author, maintainer:  Ryan Beisner <ryan.beisner@canonical.com>
#
# Copyright 2015 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranties of
# MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import optparse
import os
import sys
import yaml
import lib.common.tools_common as u

USAGE = '''Usage: %prog [options]

bundle-reducer
==============================================================================
A tool to extract subsets subsets of juju-deployer bundle yaml files.

Default behavior:
  Reduce a bundle to the specified services, including all of the directly-
  related services, and save to an out_nnnnnn.yaml file in the current dir.

Usage examples:
  Reduce to only ceilometer, with all of the directly-related services.  Save
  to a new auto-generated filename in the current dir.
      %prog -i my.yaml -s "ceilometer"

  Reduce to only keystone and cinder, with all of the directly-related
  services, write to a new file, overwrite if it exists, with debug output on.
      %prog -yd -i my.yaml -o my_new.yaml -s "keystone,cinder"

  Reduce to only keystone and cinder, with none of the directly-related
  services, remove all constraints, write to a new file, with debug output on.
      %prog -d -i my.yaml -o my_new.yaml -s "keystone,cinder" --Xr --Xc

  Reduce to only keystone and cinder, plus any related services, and
  overwrite existing file, with debug output on.
      %prog -yd -i my.yaml -o my.yaml -s "keystone,cinder"
'''


def option_handler():
    '''Define and handle command line parameters
    '''
    # Define command line options
    parser = optparse.OptionParser(USAGE)
    parser.add_option('-d', '--debug',
                      help='Enable debug logging.  (Default: False)',
                      dest='debug', action='store_true', default=False)
    parser.add_option('-y', '--yes-overwrite',
                      help='Overwrite the output file.  (Default: False)',
                      dest='overwrite', action='store_true', default=False)
    parser.add_option('-i', '--in-file',
                      help='YAML input (source) file.  (Required, no default)',
                      action='store', type='string', dest='in_file')
    parser.add_option('-o', '--out-file',
                      help='YAML output (destination) file. (Default: '
                      './out_<random>.yaml',
                      action='store', type='string', dest='out_file',
                      default='out_{}.yaml'.format(u.rnd_str(8)))
    parser.add_option('-s', '--services', '--service',
                      help='Comma-separated list of Juju services to include. '
                      '(Default=ALL)',
                      action='store', type='string', dest='include_services',
                      default="ALL")
    parser.add_option('-e', '--exclude',
                      help='Comma-separated list of Juju services to '
                      'exclude. Wins over include and wins over include '
                      'related.  Do not use spaces.  (Default=None)',
                      action='store', type='string', dest='exclude_services')
    parser.add_option('--Xr', '--exclude-related',
                      help='Exclude related services.',
                      dest='exclude_related', action='store_true',
                      default=False)
    parser.add_option('--Xc', '--remove-constraints',
                      help='Remove all constraints for all services.',
                      dest='remove_constraints', action='store_true',
                      default=False)
    parser.add_option('--Xp', '--remove-placements',
                      help='Remove all placements for all services.',
                      dest='remove_placements', action='store_true',
                      default=False)

    params = parser.parse_args()
    (opts, args) = params

    # Handle parameters, inform user
    if opts.debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.info('Logging level set to DEBUG!')
        logging.debug('parse opts: \n{}'.format(
            yaml.dump(vars(opts), default_flow_style=False)))
        logging.debug('arg count: {}'.format(len(args)))
        logging.debug('parse args: {}'.format(args))
    else:
        logging.basicConfig(level=logging.INFO)

    # Validate options
    if not opts.in_file or not opts.out_file or not opts.include_services:
        parser.print_help()
        logging.error('Missing a required option:  input file and/or '
                      'include services.')
        sys.exit(1)

    if os.path.isfile(opts.out_file) and opts.overwrite:
        logging.warning('Output file exists and will be '
                        'overwritten: {}'.format(opts.out_file))
    elif os.path.isfile(opts.out_file) and not opts.overwrite:
        logging.error('Output file exists and will NOT '
                      'be overwritten: {}'.format(opts.out_file))
        raise ValueError('Output file exists, overwrite option not set.')

    if not os.path.isfile(opts.in_file):
        raise ValueError('Input file not found.')

    return (opts, args)


# And, go.
def main():
    opts, args = option_handler()

    # TO-DO
    if str(opts.include_services).upper() == "ALL":
        logging.error('Include ALL services feature not yet implemented.')
        return
    else:
        svcs_include = frozenset(opts.include_services.split(','))

    # Additional Validation
    rm_constraints = opts.remove_constraints
    rm_placements = opts.remove_placements
    exclude_related = opts.exclude_related

    if opts.exclude_services:
        svcs_exclude = frozenset(opts.exclude_services.split(','))
    else:
        svcs_exclude = frozenset([])

    if svcs_include & svcs_exclude:
        logging.warning('Including and excluding the same service, YMMV!')

    # Read the infile
    logging.info('Reading input file: {}'.format(opts.in_file))
    org_bundle_dict = u.read_yaml(opts.in_file)

    # Mangle dict data
    new_bundle_dict = u.extract_services(org_bundle_dict,
                                         svcs_include,
                                         svcs_exclude,
                                         exclude_related,
                                         rm_constraints,
                                         rm_placements)

    # Write the outfile
    logging.info('Writing out file: {}'.format(opts.out_file))
    u.write_yaml(new_bundle_dict, opts.out_file)

if __name__ == '__main__':
    main()
