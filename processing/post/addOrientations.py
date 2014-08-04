#!/usr/bin/env python
# -*- coding: UTF-8 no BOM -*-

import os,sys,string,itertools,re,math,numpy
from collections import defaultdict
from optparse import OptionParser
import damask

scriptID = '$Id$'
scriptName = scriptID.split()[1]

# --------------------------------------------------------------------
#                                MAIN
# --------------------------------------------------------------------

parser = OptionParser(option_class=damask.extendableOption, usage='%prog options [file[s]]', description = """
Add quaternion and/or Bunge Euler angle representation of crystal lattice orientation.
Orientation is given by quaternion, Euler angles,
rotation matrix, or crystal frame coordinates (i.e. component vectors of rotation matrix).

""", version = string.replace(scriptID,'\n','\\n')
)

outputChoices = ['quaternion','eulers']
parser.add_option('-o', '--output',     dest='output', action='extend', type='string', metavar='<string LIST>',
                                        help = 'output orientation formats (%s)'%(','.join(outputChoices)))
parser.add_option('-s', '--symmetry',   dest='symmetry', action='store', type='choice', 
                                        choices=damask.Symmetry.lattices[1:], metavar='string',
                                        help = 'crystal symmetry (%s) [cubic]'%(', '.join(damask.Symmetry.lattices[1:])))
parser.add_option('-r', '--rotation',   dest='rotation', action='store', type='float', nargs=4, metavar='float float float float',
                                        help = 'angle and axis to (pre)rotate orientation')
parser.add_option('-e', '--eulers',     dest='eulers', action='store', type='string', metavar='string',
                                        help = 'Euler angles label')
parser.add_option('-d', '--degrees',    dest='degrees', action='store_true',
                                        help = 'Euler angles are given in degrees [%default]')
parser.add_option('-m', '--matrix',     dest='matrix', action='store', type='string', metavar='string',
                                        help = 'orientation matrix label')
parser.add_option('-a',                 dest='a', action='store', type='string', metavar='string',
                                        help = 'crystal frame a vector label')
parser.add_option('-b',                 dest='b', action='store', type='string', metavar='string',
                                        help = 'crystal frame b vector label')
parser.add_option('-c',                 dest='c', action='store', type='string', metavar='string',
                                        help = 'crystal frame c vector label')
parser.add_option('-q', '--quaternion', dest='quaternion', action='store', type='string', metavar='string',
                                        help = 'quaternion label')
parser.set_defaults(output = [])
parser.set_defaults(symmetry = 'cubic')
parser.set_defaults(rotation = [0.,1.,1.,1.])       # no rotation about 1,1,1
parser.set_defaults(degrees = False)

(options, filenames) = parser.parse_args()

datainfo = {                                                               # list of requested labels per datatype
             'tensor':     {'len':9,
                            'label':[]},
             'vector':     {'len':3,
                            'label':[]},
             'quaternion': {'len':4,
                            'label':[]},
           }

if not set(options.output).issubset(set(outputChoices)):
  parser.error('output must be chosen from %s...'%(', '.join(outputChoices)))

if options.eulers     != None:  datainfo['vector']['label'] += [options.eulers];                input = 'eulers'
if options.a          != None and \
   options.b          != None and \
   options.c          != None:  datainfo['vector']['label'] += [options.a,options.b,options.c]; input = 'frame'
if options.matrix     != None:  datainfo['tensor']['label'] += [options.matrix];                input = 'matrix'
if options.quaternion != None:  datainfo['quaternion']['label'] += [options.quaternion];        input = 'quaternion'

inputGiven = 0
for datatype,info in datainfo.items():
  inputGiven += len(info['label'])
if inputGiven != 1: parser.error('select exactly one input format...')

toRadians = math.pi/180.0 if options.degrees else 1.0                                               # rescale degrees to radians
options.output = map(lambda x: x.lower(), options.output)

r = damask.Quaternion().fromAngleAxis(toRadians*options.rotation[0],options.rotation[1:])

# ------------------------------------------ setup file handles ---------------------------------------  

files = []
if filenames == []:
  files.append({'name':'STDIN', 'input':sys.stdin, 'output':sys.stdout, 'croak':sys.stderr})
else:
  for name in filenames:
    if os.path.exists(name):
      files.append({'name':name, 'input':open(name), 'output':open(name+'_tmp','w'), 'croak':sys.stderr})

# ------------------------------------------ loop over input files ----------------------------------
for file in files:
  if file['name'] != 'STDIN': file['croak'].write('\033[1m'+scriptName+'\033[0m: '+file['name']+'\n')
  else: file['croak'].write('\033[1m'+scriptName+'\033[0m\n')

  table = damask.ASCIItable(file['input'],file['output'],False)                                     # make unbuffered ASCII_table
  table.head_read()                                                                                 # read ASCII header info
  table.info_append(string.replace(scriptID,'\n','\\n') + '\t' + ' '.join(sys.argv[1:]))

  active = defaultdict(list)
  column = defaultdict(dict)
  missingColumns = False

  for datatype,info in datainfo.items():
    for label in info['label']:
      key = '1_%s'%label
      if key not in table.labels:
        file['croak'].write('column %s not found...\n'%key)
        missingColumns = True                                                                       # break if label not found
      else:
        active[datatype].append(label)
        column[datatype][label] = table.labels.index(key)                                           # remember columns of requested data

  if missingColumns:
    continue

# ------------------------------------------ assemble header --------------------------------------- 
  for output in options.output:
    if output == 'quaternion':
      table.labels_append(['%i_quaternion_%s'%(i+1,options.symmetry) for i in xrange(4)])
    if output == 'eulers':
      table.labels_append(['%i_eulers_%s'%(i+1,options.symmetry) for i in xrange(3)])
  table.head_write()

# ------------------------------------------ process data ----------------------------------------  
  outputAlive = True
  while outputAlive and table.data_read():                                                          # read next data line of ASCII table
    if input == 'eulers':
      o = damask.Orientation(Eulers=toRadians*numpy.array(map(float,table.data[column['vector'][options.eulers]:\
                                                                               column['vector'][options.eulers]+datainfo['vector']['len']])),
                             symmetry=options.symmetry).reduced()
    elif input == 'matrix':
      o = damask.Orientation(matrix=numpy.array([map(float,table.data[column['tensor'][options.matrix]:\
                                                                      column['tensor'][options.matrix]+datainfo['tensor']['len']])]),
                             symmetry=options.symmetry).reduced()
    elif input == 'frame':
      o = damask.Orientation(matrix=numpy.array([map(float,table.data[column['vector'][options.a]:\
                                                                      column['vector'][options.a]+datainfo['vector']['len']] + \
                                                           table.data[column['vector'][options.b]:\
                                                                      column['vector'][options.b]+datainfo['vector']['len']] + \
                                                           table.data[column['vector'][options.c]:\
                                                                      column['vector'][options.c]+datainfo['vector']['len']]
                                                    )]).reshape(3,3),
                             symmetry=options.symmetry).reduced()
    elif input == 'quaternion':
      o = damask.Orientation(quaternion=numpy.array(map(float,table.data[column['quaternion'][options.quaternion]:\
                                                                         column['quaternion'][options.quaternion]+datainfo['quaternion']['len']])),
                             symmetry=options.symmetry).reduced()

    o.quaternion = r*o.quaternion

    for output in options.output:
      if output == 'quaternion':
        table.data_append(o.asQuaternion())
      if output == 'eulers':
        table.data_append(o.asEulers('Bunge'))
    outputAlive = table.data_write()                                                                # output processed line

# ------------------------------------------ output result ---------------------------------------  
  outputAlive and table.output_flush()                                                              # just in case of buffered ASCII table

  file['input'].close()                                                                             # close input ASCII table (works for stdin)
  file['output'].close()                                                                            # close output ASCII table (works for stdout)
  if file['name'] != 'STDIN':
    os.rename(file['name']+'_tmp',file['name'])                                                     # overwrite old one with tmp new
