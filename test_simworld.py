import sys
import os
if len(sys.argv) < 2 :
    print ' Error please supply save file'
    sys.exit(1)

savefile_path = sys.argv[1]

if not os.path.isfile( savefile_path ) :
    print ' Error, file %s does not exists' % savefile_path
    sys.exit(2)

import simworld
welt = simworld.World()
welt.load( savefile_path )

s = welt.get_settings()

size_x = s.groesse_x
size_y = s.groesse_y
size_area = size_x * size_y

fab_num = welt.get_factory_count()

print 'World (%s, %s) has %d factories' % (size_x, size_y, fab_num)
print ' fab density = %0.3f tiles^2/fab' % (1.0*size_area/fab_num)

cities = welt.get_staedte()

print ' has %d cities, on avg %5.2f fabs/city' % (len(cities), 1.0*fab_num/len(cities))

# Test for List of all goods in der Welt
#goods = welt.get_goods_list()
#for g in sorted(goods, key=lambda x : x.catg_index) : print '% 2d % 3d %-18s %02s "%-10s" "%-12s"' % (g.catg, g.catg_index, simworld.translate(g.catg_name), g.index, g.mass, simworld.translate(g.name) )

# End of tests
#import sys
#sys.exit(0)
