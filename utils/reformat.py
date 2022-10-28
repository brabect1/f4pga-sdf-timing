# Copyright 2022 Tomas Brabec
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import os.path
import argparse
from sdf_timing import sdfparse, sdfwrite

# Define command-line API
opt_parser = argparse.ArgumentParser(
        description='Reads input SDFs and writes out back into SDFs in a target directory.'
        );
opt_parser.add_argument('--dir', type=str, default='.',
        help='Path to a directory where to write out parsed SDFs.', metavar='<path>'
        );
opt_parser.add_argument('--stdout', default=False, action='store_true',
        help='Print to standard output instead to a file.'
        );
opt_parser.add_argument('--force', default=False, action='store_true',
        help='Overwrites the output file if already exists.'
        );
opt_parser.add_argument('--indent', type=int, default=2, metavar='N',
        help='Number of spaces for indentation.'
        );
opt_parser.add_argument('files', nargs='+', metavar='file',
        help='List of SDF files to parse.'
        );

# parse command line arguments
args = opt_parser.parse_args();


if not os.path.isdir(args.dir):
    print("Not a directory: " + str(args.dir));
else:
    for f in args.files:
        if not os.path.exists(f):
            print("Does not exists: '%s'" % f);
        else:
            with open(f) as sdffile:
                print("Reading %s ..." % f);
                sdf = sdfparse.parse(sdffile.read())
                if not args.stdout:
                    of = os.path.join(args.dir, os.path.basename(f))
                    if os.path.exists(of) and not args.force:
                        print("File already exists, not writing: %s" % of);
                        continue;

                    with open(of,'w') as outfile:
                        print("Writing %s ..." % of);
                        sdfwrite.print_sdf(sdf, indent=args.indent*' ', channel=outfile)
                else:
                    sdfwrite.print_sdf(sdf, indent=args.indent*' ')

