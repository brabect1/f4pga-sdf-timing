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
from io import StringIO

# add `sdf_timing` source tree into PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sdf_timing import sdfparse, sdfyacc, sdflex, sdfwrite
from ply import yacc
from .test_syntax_elements import NullLogger, reconfigure, parse


# Performs full SDF syntax tests by parsing an input syntax, writing it
# out to a string buffer and comparing with the expected output.
class TestParseAndWrite(unittest.TestCase):

    def setUp(self):
        reconfigure(errorlog=NullLogger);
        self.buf = StringIO();

    def test_1(self):
        data ='''
(DELAYFILE
  (SDFVERSION "3.0")
  (TIMESCALE 100 ps)
  // this is a comment
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
)
'''
        sdf = parse(data);
        sdfwrite.print_sdf( sdf, channel=self.buf );
        act = self.buf.getvalue();
        exp = '''(DELAYFILE
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
        self.assertEqual( act, exp );

    def test_2(self):
        data ='''(DELAYFILE (SDFVERSION "3.0") (DESIGN "BIGCHIP"))'''
        sdf = parse(data);
        sdfwrite.print_sdf( sdf, channel=self.buf );
        act = self.buf.getvalue();
        exp = '''(DELAYFILE
  (SDFVERSION "3.0")
  (DESIGN "BIGCHIP")
)'''
        self.assertEqual( act, exp );

