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

import unittest
import os
import sys
import re
from io import StringIO

# add `sdf_timing` source tree into PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sdf_timing import sdfparse, sdfyacc, sdflex, sdfwrite
from ply import yacc
from .test_syntax_elements import NullLogger, reconfigure, parse


# Defines a data set to be tested. The structure is a list of records,
# where each record is a 3-element list such that 1st element is a description,
# 2nd element is the input data and 3rd element is the expected data.
# Hence::
#
#     [ [<desc>, <intput>, <expected>], [<desc>, <intput>, <expected>], ...]
#
testdata = [
['minimum_sdf',
'''(DELAYFILE (SDFVERSION "3.0"))''',
'''\
(DELAYFILE
  (SDFVERSION "3.0")
)
'''
],
['comment',
'''\
(DELAYFILE
  // some comment
  (SDFVERSION "3.0")
)''',
'''\
(DELAYFILE
  (SDFVERSION "3.0")
)'''
],
['retain_path',
'''\
(DELAYFILE
  (SDFVERSION "3.0")
  (TIMESCALE 100 ps)
  (CELL
    (CELLTYPE "somecell")
    (INSTANCE someinst)
    (DELAY
      (ABSOLUTE
        (IOPATH mck b/c/clk (RETAIN (1)) (2))
        (COND en==1'b1 (IOPATH d[0] b/c/d (RETAIN (0.3)) (0.4:0.4:0.4)))
      )
    )
  )
)''',
'''\
(DELAYFILE
  (SDFVERSION "3.0")
  (TIMESCALE 100 ps)
  (CELL
    (CELLTYPE "somecell")
    (INSTANCE someinst)
    (DELAY
      (ABSOLUTE
        (IOPATH mck b/c/clk (RETAIN (1)) (2))
        (COND en == 1'b1 (IOPATH d[0] b/c/d (RETAIN (0.3)) (0.4:0.4:0.4)))
      )
    )
  )
)'''
],
];


# Removes empty lines and trims leading and trailing whitespace from
# a (generally multi-line) string.
def trim_whitespace(string):
    return "\n".join([l.strip() for l in string.splitlines() if l.strip()]);


# Performs full SDF syntax tests by parsing an input syntax, writing it
# out to a string buffer and comparing with the expected output.
class TestParseAndWrite(unittest.TestCase):

    def setUp(self):
        reconfigure(errorlog=NullLogger);
        self.buf = StringIO();

    def test_testdata(self):
        for data in testdata:
            with self.subTest( data[0], data = data ):
                exp = trim_whitespace( data[2] );
                sdf = parse( data[1] );
                self.buf.truncate(0);
                self.buf.seek(0);
                sdfwrite.print_sdf( sdf, channel=self.buf );
                act = trim_whitespace( self.buf.getvalue() );
                self.assertEqual( act, exp );



