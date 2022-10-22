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

# add `sdf_timing` source tree into PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sdf_timing import sdfparse, sdfyacc, sdflex
from ply import yacc

# Implements a "silent" PlyLogger. It is used to avoid various parser
# errors and warnings on unused grammer symbols, which would get reported
# once we start changing the parser's start symbol.
class NullLogger(yacc.PlyLogger):
    def debug(self, msg=None, *args, **kwargs):
        pass

    info = debug
    warning = debug
    error = debug

# Compiles a new parser with the given configuration.
#
# Unfortunately, `sdf_timing` current API supports no customization
# and, in genetral, is very stiff. Unless that changes, we do need
# to tap its internals for any customization.
def reconfigure(debug=False,write_tables=False,startsym=None, errorlog=None, debuglog=None):
    sdfyacc.parser = yacc.yacc(debug=debug, write_tables=write_tables, start=startsym, module=sdfyacc, errorlog=errorlog, debuglog=debuglog);
    sdfparse.init();

# Alternative implementation of `sdfparse.parse`. This implementation
# returns the output of PLY's parser (while `sdfparse.parse` compiles
# a custom structure representing an SDF file structure).
#
# As we are going to parse individual grammar/syntax elements, the parser
# output would not match the expected structure of `sdfparse.parse`, which
# would then return an empty result. Hence we need the output directly
# from the parser itself.
def parse(input):
    sdfparse.init()
    sdflex.input_data = input
    return sdfyacc.parser.parse(sdflex.input_data)


slice_cell ='''
(CELL
 (CELLTYPE "BIGCHIP")
 (INSTANCE top)
 (DELAY
  (ABSOLUTE
   (INTERCONNECT mck b/c/clk (.6:.7:.9))
   (INTERCONNECT d[0] b/c/d (.4:.5:.6))
  )
 )
)
'''

slice_sdffile = '''
(DELAYFILE
(SDFVERSION "3.0")
(TIMESCALE 100 ps)
)
'''

slice_interconnect ='''
(INTERCONNECT mck b/c/clk (.6:.7:.9))
'''

class TestSyntaxElements(unittest.TestCase):

    null_logger = None;

    # Compiles a delay dictionary from a triplet value.
    # We use this method for better maintence of changes in the SDF dictionary
    # key names.
    def compile_delay(self, triple):
        return {'min': triple[0], 'avg': triple[1], 'max': triple[2]};

    def setUp(self):
        self.null_logger = NullLogger;

    #-------------------------------------
    # rvalue
    #-------------------------------------
    # [1] Open Verilog Internationa, Standard Delay Format Specification v3.0, May 1995
    #
    # From spec [1]:
    #
    #   Each rvalue is either a single `RNUMBER` or an `rtriple`, containing three
    #   `RNUMBER`s separated by colons, in parentheses.
    #
    #   Syntax
    #         rvalue ::= ( RNUMBER? )
    #                ||= ( rtriple? )
    #
    #   The use of single `RNUMBER`s and `rtriple`s should not be mixed in the same
    #   SDF file. All `RNUMBER`s can have negative, zero or positive values.
    #   The use of triples in SDF allows you to carry three sets of data in the same
    #   file. Each number in the triple is an alternative value for the data and is
    #   typically selected from the triple by the annotator or analysis tool on an
    #   instruction from the user. The prevailing use of the three numbers is to
    #   represent *minimum*, *typical* and *maximum* values computed at three
    #   process/operating conditions for the entire design. Any one or any two
    #   (but not all three) of the numbers in a triple may be omitted if the
    #   separating colons are left in place. This indicates that no value has been
    #   computed for that data, and the annotator should not make any changes if
    #   that number is selected from the triple. For absolute delays, this is not the
    #   same as entering a value of 0.0.
    #
    # `rvalue`s are used to define delay values, `delval`s. There is a note in `delval`
    # description that allows use of *empty* `rvalue`. From [1]:
    #
    #   ... Note that since any `rvalue`
    #   can be an empty pair of parentheses, each type of delay data can be
    #   annotated or omitted as the need arises.

    def test_rvalue_empty(self):
        data ='()'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [None,None,None] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_three_int_1(self):
        data ='(1:2:3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [1,2,3] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_three_int_2(self):
        data ='(-1:0:1)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [-1,0,1] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_two_int_1(self):
        data ='(1:2:)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [1,2,None] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_two_int_2(self):
        data ='(1::3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [1,None,3] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_two_int_3(self):
        data ='(:2:3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [None,2,3] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_one_int_1(self):
        data ='(1::)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [1,None,None] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_one_int_2(self):
        data ='(:2:)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [None,2,None] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_one_int_3(self):
        data ='(::3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [None,None,3] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    def test_rvalue_triple_missing_lpar(self):
        data ='1:2:3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_triple_missing_rpar(self):
        data ='(1:2:3'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_triple_missing_doublecolon_1(self):
        data ='(1:23)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_triple_missing_doublecolon_2(self):
        data ='(12:3)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_rvalue_single_int_1(self):
        data ='(123)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        sdf = parse(data);
        exp = self.compile_delay( [123,123,123] );
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );

    #-------------------------------------
    # interconnect delay
    #-------------------------------------

    def test_interconnect_simple_1(self):
        data ='(INTERCONNECT a b (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'b', 'type': 'interconnect'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_interconnect_simple_2(self):
        data ='(INTERCONNECT a/b/c e/f (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a/b/c', 'to_pin': 'e/f', 'type': 'interconnect'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_interconnect_empty_delay(self):
        data ='(INTERCONNECT a b ())'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'b', 'type': 'interconnect'};
        act = {k: sdf[k] for k in exp.keys()};
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_interconnect_missing_port(self):
        data ='(INTERCONNECT a (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_interconnect_missing_ports(self):
        data ='(INTERCONNECT (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_interconnect_missing_delay(self):
        data ='(INTERCONNECT a b)'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_interconnect_missing_lpar(self):
        data ='INTERCONNECT a b (1:2:3))'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

    def test_interconnect_missing_rpar(self):
        data ='(INTERCONNECT a b (1:2:3)'
        reconfigure(startsym='interconnect', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);


        ##import json
        ##print( json.dumps( sdf, indent=2) );
        

if __name__ == '__main__':
    unittest.main()

