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
  rad = float(sys.argv[2])
except :
  print '--> Warning: The radius has been set to a very small qty, the circles may not be visible'
  rad = 1.0
q = 2* (rad**2)


filter_catg = (
    #10  # Bulk goods
    #7   # Wood
    #9   # Gasoline/Oil
    -1
)

COAL_INDEX  = 13 # coal
WASTE_INDEX = 36 # waste

bipolar_field = False #True

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

fabs_in_welt = [ welt.get_factory_at(i) for i in range(welt.get_factory_count()) ]

assert len(fabs_in_welt) == welt.get_factory_count()

def is_producer_of_good(fab, indx=-1):
    if indx == -1 :
        if filter_catg == -1 : return len(fab.get_ausgang()) > 0
        return filter_catg in [ g.get_typ().catg_index for g in fab.get_ausgang() ]
    else :
        return indx in [ g.get_typ().index for g in fab.get_ausgang() ]

def is_consumer_of_good(fab, indx=-1):
    if indx == -1 :
        if filter_catg == -1 : return len(fab.get_eingang()) > 0
        return filter_catg in [ g.get_typ().catg_index for g in fab.get_eingang() ]
    else :
        return indx in [ g.get_typ().index for g in fab.get_eingang() ]

interesting_fabs = [ f for f in fabs_in_welt if is_producer_of_good(f) or is_consumer_of_good(f) ]

producers_fabs = [ f for f in fabs_in_welt if is_producer_of_good(f) ]
consumers_fabs = [ f for f in fabs_in_welt if is_consumer_of_good(f) ]

waste_producers = [ f for f in fabs_in_welt if is_producer_of_good(f, WASTE_INDEX) ]
waste_consumers = [ f for f in fabs_in_welt if is_consumer_of_good(f, WASTE_INDEX) ]

coal_producers = [ f for f in fabs_in_welt if is_producer_of_good(f, COAL_INDEX) ]
coal_consumers = [ f for f in fabs_in_welt if is_consumer_of_good(f, COAL_INDEX) ]

def get_points(flist, sign=1) :
    return [ (f.pos.get_2d().coords(), sign) for f in flist ]

def get_x_list(flist) :
    return [ f.pos.get_2d().x for f in flist ]

def get_y_list(flist) :
    return [ f.pos.get_2d().y for f in flist ]

#points = [ (f.pos.get_2d().coords(), 1) for f in interesting_fabs ]
prod_points = get_points( producers_fabs )
cons_points = get_points( consumers_fabs, -1 if bipolar_field else 1 )

# Now do the plotting

import numpy as np
import pylab as plt
import matplotlib.cm as cm

np.seterr(divide='ignore')

groesse_x = welt.get_settings().groesse_x
groesse_y = welt.get_settings().groesse_y
fac = 1

# Create some sample data
dx = np.linspace(0, groesse_x-1, num=groesse_x*fac )
dy = np.linspace(0, groesse_y-1, num=groesse_y*fac )
X,Y = np.meshgrid(dx,dy)

def field_for_points(points):
    # Init Z
    Z = (X + Y)*0

    for point, sign in points :
        Z += sign / ( ( X-point[0] )**2 + ( Y-point[1] )**2 )
    # Scale to adjust radius
    Z = q * Z

    # Clip values to avoid scalling
    Z = Z.clip( -1, 1 )
    # Reduce the shadow extent
    if not bipolar_field :
        Z = Z ** 4 #Z = np.trunc(Z)

    null_threshold = 0.001 if bipolar_field else 0.4
    Z = np.where( abs(Z) > null_threshold , Z, 0)

    #Z = Z.round(2)
    return Z / ( np.sign(Z) ** 2 )

CGREEN = np.array([0.0, 1.0, 0.0])
CBLUE  = np.array([0.0, 0.0, 1.0])
CRED   = np.array([1.0, 0.0, 0.0])

map_bg = np.empty([groesse_y, groesse_x, 3]) #X*0
k = simworld.koord(0,0)
for kx in range(groesse_x) :
    k.x = kx
    for ky in range(groesse_y) :
        k.y = ky
        #k = simworld.koord(kx,ky)
        gr = welt.lookup_kartenboden(k)
        map_bg[ky][kx] = CBLUE if gr.is_wasser else CGREEN
        if gr.hat_wege : map_bg[ky][kx] = CRED

plt.imshow( map_bg ,
        interpolation='nearest',
        cmap = cm.winter)

if bipolar_field :
    plt.imshow( field_for_points(prod_points) + field_for_points(cons_points) ,
            interpolation='nearest', alpha=0.6,
            cmap = cm.RdBu_r)
else :
    plt.imshow( field_for_points(prod_points) ,
            interpolation='nearest', alpha=0.6,
            cmap = cm.Reds)

    plt.imshow( field_for_points(cons_points) ,
            interpolation='nearest', alpha=0.6,
            cmap = cm.Blues)

plt.grid(True)

#plt.xticks(np.arange(0, groesse_x +1), [])
#plt.yticks(np.arange(0, groesse_y +1), [])

#plt.colorbar()

# MARKERS
#    's' : (4,math.pi/4.0,0),   # square
#    'o' : (0,0,3),            # circle
#    '^' : (3,0,0),             # triangle up
#    '>' : (3,math.pi/2.0,0),   # triangle right
#    'v' : (3,math.pi,0),       # triangle down
#    '<' : (3,3*math.pi/2.0,0), # triangle left
#    'd' : (4,0,0),             # diamond
#    'p' : (5,0,0),             # pentagon
#    'h' : (6,0,0),             # hexagon
#    '8' : (8,0,0),             # octagon
#    '+' : (4,0,2),             # plus
#    'x' : (4,math.pi/4.0,2)    # cross


#
# Generation of scatter plots
marker_size = 5**2

plt.scatter(x=get_x_list(coal_producers), y=get_y_list(coal_producers), marker='^',
c='k', s=marker_size, lw=0.0 )
plt.scatter(x=get_x_list(coal_consumers), y=get_y_list(coal_consumers), marker='^',
c='k', s=marker_size, lw=0.0 )

plt.scatter(x=get_x_list(waste_producers), y=get_y_list(waste_producers), marker='s',
c='k', s=marker_size, lw=0.0 )
plt.scatter(x=get_x_list(waste_consumers), y=get_y_list(waste_consumers), marker='s',
c='k', s=marker_size, lw=0.0 )

#plt.tight_layout(pad=0.5)

plt.show()
#plt.savefig('test.png', bbox_inches='tight')

