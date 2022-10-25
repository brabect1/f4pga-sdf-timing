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

    def test_rvalue_triple_none(self):
        data ='(::)'
        reconfigure(startsym='real_triple', errorlog=self.null_logger);
        with self.assertRaises(Exception):
            sdf = parse(data);

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

    #-------------------------------------
    # conditional port expression
    #-------------------------------------

    def test_cond_path_expr_const_1(self):
        data ='1\'b0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'b0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_2(self):
        data ='1\'b1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'b1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_3(self):
        data ='1\'B0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'B0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_4(self):
        data ='1\'B1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'B1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_5(self):
        data ='\'b0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['\'b0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_6(self):
        data ='\'b1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['\'b1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_7(self):
        data ='\'B0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['\'B0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_8(self):
        data ='\'B1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['\'B1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_9(self):
        data ='0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_const_10(self):
        data ='1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_port_1(self):
        data ='a'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_port_2(self):
        data ='a/b/c'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a/b/c'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_port_3(self):
        data ='a.b.c'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a.b.c'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_unary_const_1(self):
        data ='~1\'b0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['~', '1\'b0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_unary_port_1(self):
        data ='~a/b/c'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['~', 'a/b/c'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_unary_port_2(self):
        data ='!x'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['!', 'x'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_1(self):
        data ='a & b'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a','&','b'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_2(self):
        data ='a && 1\'b1'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['a','&&','1\'b1'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_3(self):
        data ='1\'b0 | b'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['1\'b0','|','b'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_4(self):
        data ='x || y'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['x','||','y'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_5(self):
        data ='c.d ^ a/b'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['c.d','^','a/b'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_6(self):
        data ='A==0'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['A','==','0'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_binary_7(self):
        data ='A!=C'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['A','!=','C'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_parenthesis_1(self):
        data ='(A)'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['(','A',')'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_parenthesis_2(self):
        data ='(1\'b1 && A)'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['(','1\'b1','&&','A',')'];
        self.assertEqual( act, exp );

    def test_cond_path_expr_parenthesis_3(self):
        data ='(A&(B|C))'
        reconfigure(startsym='delay_condition', errorlog=self.null_logger);
        act = parse(data);
        exp = ['(','A','&','(','B','|','C',')',')'];
        self.assertEqual( act, exp );

    #-------------------------------------
    # conditional path delay
    #-------------------------------------
    # [1] Open Verilog Internationa, Standard Delay Format Specification v3.0, May 1995
    #
    # From spec [1]:
    #
    #   The `COND` keyword allows the specification of conditional (state-
    #   dependent) input-to-output path delays.
    #
    #   Syntax
    #
    #       ( COND QSTRING? conditional_port_expr
    #           ( IOPATH port_spec port_instance delval_list ) )
    #

    def test_cond_iopath_simple_1(self):
        data ='(COND b (IOPATH a y () ()))'
        reconfigure(startsym='cond_delay', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'b'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! `sdf` is a list of paths
        self.assertEqual( act, exp );

    def test_cond_iopath_simple_2(self):
        data ='(COND x & ~y (IOPATH a y () ()))'
        reconfigure(startsym='cond_delay', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'x & ~ y'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! `sdf` is a list of paths
        self.assertEqual( act, exp );

    def test_cond_iopath_six_vals(self):
        data = '''(COND PA==1'b0&&PB==1'b1&&PS==1'b1 (IOPATH EN PADM () () (0.661::0.682) (3.513::11.574) (0.945::0.964) (3.176::10.900)))'''
        reconfigure(startsym='cond_delay', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'EN', 'to_pin': 'PADM', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'PA == 1\'b0 && PB == 1\'b1 && PS == 1\'b1'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! `sdf` is a list of paths
        self.assertEqual( act, exp );


    #-------------------------------------
    # delay list
    #-------------------------------------

    def test_delay_list_1(self):
        data ='''
        (COND b & a (IOPATH a y () ()))
        (COND a | b (IOPATH a y () ()))
        '''
        reconfigure(startsym='delay_list', errorlog=self.null_logger);
        sdf = parse(data);
        exp = [
                {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'b & a'},
                {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': True, 'cond_equation': 'a | b'}
                ];
        act = [];
        for i in range(0,len(exp)):
            act.append( {k: sdf[i][k] for k in exp[i].keys()} );
        self.assertEqual( act, exp );


    #-------------------------------------
    # width check
    #-------------------------------------

    def test_tcheck_width_simple(self):
        data ='''(WIDTH clk (4.4:7.5:11.3))''';
        reconfigure(startsym='width_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'width', 'is_timing_check': True, 'is_cond': False,
                'from_pin_edge': None, 'to_pin_edge': None};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_tcheck_width_port_negedge_spec(self):
        data ='''(WIDTH (negedge clk) (4.4:7.5:11.3))''';
        reconfigure(startsym='width_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'width', 'is_timing_check': True, 'is_cond': False,
                'from_pin_edge': 'negedge', 'to_pin_edge': 'negedge'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_tcheck_width_port_posedge_spec(self):
        data ='''(WIDTH (posedge path/to/rst) (11))''';
        reconfigure(startsym='width_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'path/to/rst', 'to_pin': 'path/to/rst', 'type': 'width', 'is_timing_check': True,
                'is_cond': False, 'from_pin_edge': 'posedge', 'to_pin_edge': 'posedge'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_tcheck_width_conditional(self):
        data ='''(WIDTH (COND ENABLE (posedge CP)) (1:1:1) )''';
        reconfigure(startsym='width_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'CP', 'to_pin': 'CP', 'type': 'width', 'is_timing_check': True, 'is_cond': True,
                'from_pin_edge': 'posedge', 'to_pin_edge': 'posedge', 'cond_equation': 'ENABLE'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object


    #-------------------------------------
    # period check
    #-------------------------------------

    def test_tcheck_period_simple(self):
        data ='''(PERIOD clk (1::2))''';
        reconfigure(startsym='period_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'period', 'is_timing_check': True, 'is_cond': False,
                'from_pin_edge': None, 'to_pin_edge': None};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_tcheck_period_conditional(self):
        data ='''(PERIOD (COND a/b==1'b0 && !c (negedge clk)) (1))''';
        reconfigure(startsym='period_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'period', 'is_timing_check': True, 'is_cond': True,
                'from_pin_edge': 'negedge', 'to_pin_edge': 'negedge', 'cond_equation': 'a/b == 1\'b0 && ! c'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_tcheck_period_port_posedge_spec(self):
        data ='''(PERIOD (posedge path/to/CK) ())''';
        reconfigure(startsym='period_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'path/to/CK', 'to_pin': 'path/to/CK', 'type': 'period', 'is_timing_check': True,
                'is_cond': False, 'from_pin_edge': 'posedge', 'to_pin_edge': 'posedge'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object


    #-------------------------------------
    # nochange check
    #-------------------------------------

    def test_tcheck_nochange_simple(self):
        data ='''(NOCHANGE wr addr (:1:) (:2:))''';
        reconfigure(startsym='nochange_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'addr', 'to_pin': 'wr', 'type': 'nochange', 'is_timing_check': True, 'is_cond': False,
                'from_pin_edge': None, 'to_pin_edge': None};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_tcheck_nochange_conditional_1st(self):
        data ='''(NOCHANGE (COND 1'b0 por) (posedge rst) (1) (2))''';
        reconfigure(startsym='nochange_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'rst', 'to_pin': 'por', 'type': 'nochange', 'is_timing_check': True, 'is_cond': True,
                'from_pin_edge': 'posedge', 'to_pin_edge': None, 'cond_equation': '1\'b0'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object

    def test_tcheck_nochange_conditional_2nd(self):
        data ='''(NOCHANGE (negedge por) (COND a/b&c (posedge rst)) (1) (2))''';
        reconfigure(startsym='nochange_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = {'from_pin': 'rst', 'to_pin': 'por', 'type': 'nochange', 'is_timing_check': True, 'is_cond': True,
                'from_pin_edge': 'posedge', 'to_pin_edge': 'negedge', 'cond_equation': 'a/b & c'};
        act = {k: sdf[0][k] for k in exp.keys()}; # !!! TODO `sdf` is a list of paths, which is strange here
        self.assertEqual( act, exp );
        #TODO compare delay object


    #-------------------------------------
    # timingcheck
    #-------------------------------------

    def test_timingcheck_1(self):
        data ='''
        (TIMINGCHECK
        (SETUPHOLD d (posedge clk) (3:4:5) (-1:-1:-1))
        (WIDTH clk (4.4:7.5:11.3))
        )
        '''
        reconfigure(startsym='timing_check', errorlog=self.null_logger);
        sdf = parse(data);
        exp = [
                {'from_pin': 'clk', 'to_pin': 'd', 'type': 'setuphold', 'is_cond': False, 'cond_equation': None},
                {'from_pin': 'clk', 'to_pin': 'clk', 'type': 'width', 'is_cond': False, 'cond_equation': None}
                ];
        act = [];
        self.assertEqual( len(sdf), len(exp) );
        for i in range(0,len(exp)):
            act.append( {k: sdf[i][k] for k in exp[i].keys()} );
        self.assertEqual( act, exp );


    #-------------------------------------
    # delay
    #-------------------------------------

    def test_delay_absolute_empty(self):
        data ='''(DELAY (ABSOLUTE))'''
        reconfigure(startsym='delay', errorlog=self.null_logger);
        sdf = parse(data);
        self.assertEqual( sdf, [] );

    def test_delay_absolute_1(self):
        data ='''
        (DELAY
        (ABSOLUTE
        (IOPATH a y (1.5:2.5:3.4) (2.5:3.6:4.7))
        (IOPATH b y (1.4:2.3:3.2) (2.3:3.4:4.3))
        )
        )
        '''
        reconfigure(startsym='delay', errorlog=self.null_logger);
        sdf = parse(data);
        exp = [
                {'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath', 'is_cond': False, 'cond_equation': None},
                {'from_pin': 'b', 'to_pin': 'y', 'type': 'iopath', 'is_cond': False, 'cond_equation': None}
                ];
        act = [];
        self.assertEqual( len(sdf), len(exp) );
        for i in range(0,len(exp)):
            act.append( {k: sdf[i][k] for k in exp[i].keys()} );
        self.assertEqual( act, exp );


    #-------------------------------------
    # cell
    #-------------------------------------

    def test_cell_1(self):
        data ='''
        (CELL
            (CELLTYPE "AND2")
            (INSTANCE top/b/d)
            (DELAY
                (ABSOLUTE
                    (IOPATH a y (1.5:2.5:3.4)(2.5:3.6:4.7))
                    (IOPATH b y (1.4:2.3:3.2)(2.3:3.4:4.3))
                )
            )
        )
        '''
        reconfigure(startsym='cell', errorlog=self.null_logger);
        sdf = parse(data);
        self.assertTrue('AND2' in sdf);

        sdf = sdf['AND2'];
        self.assertTrue('top/b/d' in sdf);

        sdf = sdf['top/b/d'];
        exp = {
                "iopath_a_y": {
                    'from_pin': 'a', 'to_pin': 'y', 'type': 'iopath',
                    'is_cond': False, 'cond_equation': None
                    },
                "iopath_b_y": {
                    'from_pin': 'b', 'to_pin': 'y', 'type': 'iopath',
                    'is_cond': False, 'cond_equation': None
                    }
                };
        self.assertEqual( sdf.keys(), exp.keys() );
        act = {};
        for i in exp.keys():
            act.update( {i: {k: sdf[i][k] for k in exp[i].keys()}} );
        self.assertEqual( act, exp );

        ##TODO import json;
        ##TODO print( json.dumps( sdf, indent=2 ) );


if __name__ == '__main__':
    unittest.main()

