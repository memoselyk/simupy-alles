import sys
import os
if len(sys.argv) < 2 :
    print ' Error please supply save file'
    sys.exit(1)

savefile_path = sys.argv[1]

if not os.path.isfile( savefile_path ) :
    print ' Error, file %s does not exists' % savefile_path
    sys.exit(2)

try :
    n_sup = int(sys.argv[2])
except :
    n_sup = -1
print 'Suppliers limit is %d' % n_sup

import math
import simworld
 
# Alias to save some typing
_t = simworld.translate

def PRINT_SEP() :
    print '-' * 80 # separator

#
# Load the world for searching
welt = simworld.World()
welt.load( savefile_path )

PRINT_SEP()

#
# Make a list of all fabs that have suppliers
fabs_with_suppliers = []
for i in range(welt.get_factory_count()) :
    fab = welt.get_factory_at(i)
    if len(fab.get_suppliers()) != 0 :
        fabs_with_suppliers.append(fab)

print 'Found %d Fabs with suppliers...' % len(fabs_with_suppliers)

def calculate_suppliers_cm(fab):
    orig = fab.pos.get_2d()
    sum_x = 0.0
    sum_y = 0.0
    limited_sups = list(fab.get_suppliers())
    if n_sup != -1 :
        limited_sups = limited_sups[:n_sup]
    for sup_pos in fab.get_suppliers() :
        sum_x = (sup_pos.x - orig.x)
        sum_y = (sup_pos.y - orig.y)
    sum_x = sum_x / len(limited_sups)
    sum_y = sum_y / len(limited_sups)
    return math.sqrt( (sum_x - orig.x)**2 + (sum_y - orig.y)**2 )

#
fabs_cm_list = [ (calculate_suppliers_cm(f), f) for f in fabs_with_suppliers ]

fabs_cm_list.sort(key=lambda x : x[0])

for cm, fab in fabs_cm_list[:10] :
    print '  + (% 8.2f) %-20s - %s' % (cm, fab.name, fab.pos.get_2d().get_fullstr())
 
