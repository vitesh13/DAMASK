#!/usr/bin/env python3

import os
import sys
from io import StringIO
from optparse import OptionParser

import damask


scriptName = os.path.splitext(os.path.basename(__file__))[0]
scriptID   = ' '.join([scriptName,damask.version])


# --------------------------------------------------------------------
#                                MAIN
# --------------------------------------------------------------------

parser = OptionParser(option_class=damask.extendableOption, usage='%prog options [ASCIItable(s)]', description = """
Add displacments resulting from deformation gradient field.
Operates on periodic three-dimensional x,y,z-ordered data sets.
Outputs at cell centers or cell nodes (into separate file).

""", version = scriptID)

parser.add_option('-f',
                  '--defgrad',
                  dest    = 'f',
                  metavar = 'string',
                  help    = 'label of deformation gradient [%default]')
parser.add_option('-p',
                  '--pos', '--position',
                  dest    = 'pos',
                  metavar = 'string',
                  help    = 'label of coordinates [%default]')
parser.add_option('--nodal',
                  dest    = 'nodal',
                  action  = 'store_true',
                  help    = 'output nodal (instead of cell-centered) displacements')

parser.set_defaults(f   = 'f',
                    pos = 'pos',
                   )

(options,filenames) = parser.parse_args()

for name in filenames:
    damask.util.report(scriptName,name)

    table = damask.Table.load(StringIO(''.join(sys.stdin.read())) if name is None else name)
    grid,size,origin = damask.grid_filters.cell_coord0_gridSizeOrigin(table.get(options.pos))

    F = table.get(options.f).reshape(tuple(grid)+(-1,),order='F').reshape(tuple(grid)+(3,3))
    if options.nodal:
        damask.Table(damask.grid_filters.node_coord0(grid,size).reshape(-1,3,order='F'),
                     {'pos':(3,)})\
              .add('avg({}).{}'.format(options.f,options.pos),
                   damask.grid_filters.node_displacement_avg(size,F).reshape(-1,3,order='F'),
                   scriptID+' '+' '.join(sys.argv[1:]))\
              .add('fluct({}).{}'.format(options.f,options.pos),
                   damask.grid_filters.node_displacement_fluct(size,F).reshape(-1,3,order='F'),
                    scriptID+' '+' '.join(sys.argv[1:]))\
               .save((sys.stdout if name is None else os.path.splitext(name)[0]+'_nodal.txt'), legacy=True)
    else:
        table.add('avg({}).{}'.format(options.f,options.pos),
                  damask.grid_filters.cell_displacement_avg(size,F).reshape(-1,3,order='F'),
                  scriptID+' '+' '.join(sys.argv[1:]))\
             .add('fluct({}).{}'.format(options.f,options.pos),
                  damask.grid_filters.cell_displacement_fluct(size,F).reshape(-1,3,order='F'),
                  scriptID+' '+' '.join(sys.argv[1:]))\
             .save((sys.stdout if name is None else name), legacy=True)
