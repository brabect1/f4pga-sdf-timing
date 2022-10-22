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

import json
from sdf_timing import sdfparse, sdfyacc, sdflex
from ply import yacc

class NullLogger(yacc.PlyLogger):
    def debug(self, msg=None, *args, **kwargs):
        pass

    info = debug
    warning = debug
    error = debug

def reconfigure(debug=False,write_tables=False,startsym=None, errorlog=None, debuglog=None):
    sdfyacc.parser = yacc.yacc(debug=debug, write_tables=write_tables, start=startsym, module=sdfyacc, errorlog=errorlog, debuglog=debuglog);
    sdfparse.init();

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

reconfigure(startsym='interconnect', errorlog=NullLogger);
sdf = parse(slice_interconnect);
print( sdf );
print( json.dumps(sdf, indent=2) );
