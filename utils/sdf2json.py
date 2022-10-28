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

import os
import os.path
import argparse
import json
from sdf_timing import sdfparse

def get_path_sufixes(path):
    sufixes = []
    [path,sufix] = os.path.splitext(path)
    while sufix:
        sufixes.insert(0,sufix[1:])
        [path,sufix] = os.path.splitext(path)
    return sufixes

def get_path_noextname(path):
    sufixes = []
    [path,sufix] = os.path.splitext(path)
    while sufix:
        sufixes.insert(0,sufix[1:])
        [path,sufix] = os.path.splitext(path)
    return path

opt_parser = argparse.ArgumentParser(description='Converts SDFs into JSON data format.')
opt_parser.add_argument('--dir', type=str, required=True, help='Path to a directory where to write out JSONs.', metavar='<path>')
opt_parser.add_argument('--indent', type=int, default=None, help='Indentation specifier for `json.dump()`. Number of spaces.', metavar='N')
opt_parser.add_argument('files', nargs='+', help='List of SDF files to parse.', metavar='file')
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
                of = os.path.join(args.dir, os.path.basename(get_path_noextname(f)) + ".json")
                with open(of,'w') as outfile:
                    print("Writing %s ..." % of);
                    json.dump(sdf,outfile, indent=args.indent)
