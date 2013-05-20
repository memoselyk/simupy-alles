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
# Make a list of all consumer-only fabriks
top_consumers = []  # consumer only fabs
isolated_fabs = []  # Isolated fabs (enery_gen)
fabs_per_type = {}
for i in range(welt.get_factory_count()) :
    fab = welt.get_factory_at(i)
    type_name = fab.besch.name
    if len(fab.get_ausgang()) == 0 :
        if len(fab.get_eingang()) == 0 :
            isolated_fabs.append(fab)
        else :
            top_consumers.append(fab)
    if type_name in fabs_per_type :
        fabs_per_type[type_name].append(fab)
    else :
        fabs_per_type[type_name] = [ fab ]


print 'Found %d isolated fabs...' % len(isolated_fabs)
for f in isolated_fabs :
    print '  + %-20s - %s' % ( f.name, f.pos.get_2d().get_fullstr())
PRINT_SEP()

print 'Found %d End Consumers...' % len(top_consumers)
for f in top_consumers :
    print '  + %-20s - %s' % ( f.name, f.pos.get_2d().get_fullstr())

PRINT_SEP()
#
# Generate a sample supply chain for each top-consumer
print ' Consumer\'s supply chain : '

fab_besch_table = simworld.get_fabesch_table()

top_consumer_types = set([ f.besch.name for f in top_consumers ])

moved_goods = set([])

def find_producer(good_type):
    prods = []
    for fab_type in fab_besch_table.values() :
        if fab_type.produkte == 0 : continue
        prod_goods_idx = [ 
                fab_type.get_produkt(i).ware_besch.index 
                for i in range(fab_type.produkte) ]
        if good_type.index in prod_goods_idx :
            prods.append(fab_type)
    return prods

def print_fabrik_for_chain(level, f_desc, indx=-1, produced_good=None):
    supplies = [ f_desc.get_lieferant(i) for i in range(f_desc.lieferanten) ]
    x = produced_good
    print "%s-%d %-45s\t:%-18s - % 3d" % (
        '  '*level,
        indx,
        "%s (%s)" % (_t(f_desc.name), f_desc.name), 
        #'[%d]' % len(supplies) if supplies else '' )
        '' if x is None else ' (% 2d) %s' % (x.ware_besch.catg_index, _t(x.ware_besch.name)),
        len(fabs_per_type.get(f_desc.name, [])) 
    )
    if x : moved_goods.add(x.ware_besch)

    for num, good_in in enumerate( supplies ) :
        producers = find_producer(good_in.ware_besch)
        for fab_prod in producers :
            if fabs_per_type.get(fab_prod.name, []) :
                print_fabrik_for_chain(level+1, fab_prod, num, good_in)

for num, consumer_type in enumerate(top_consumer_types) :
    f_desc = fab_besch_table[consumer_type]
    print_fabrik_for_chain(0, f_desc, num)
    PRINT_SEP()

#
# Stats
# TODO: Fabs per good category
goods_list = welt.get_goods_list()

print '%d vs %d' % (len(goods_list), len(moved_goods))

for x in sorted(moved_goods, key=lambda x: _t(x.name) ) :
    print '%-15s (%d, %d)' % (_t(x.name), x.catg_index, x.index)

per_good_producers = {}
per_good_consumers = {}


