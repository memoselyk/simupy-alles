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
  rad = 1.0
q = 2* (rad**2)


filter_catg = (
    #10  # Bulk goods
    7   # Wood
    #9   # Gasoline/Oil
    #-1
)

COAL_INDEX  = 13 # coal
WASTE_INDEX = 36 # waste

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

def get_points(flist) :
    return [ f.pos.get_2d().coords() for f in flist ]

def get_x_list(flist) :
    return [ f.pos.get_2d().x for f in flist ]

def get_y_list(flist) :
    return [ f.pos.get_2d().y for f in flist ]

#points = [ (f.pos.get_2d().coords(), 1) for f in interesting_fabs ]
prod_points = get_points( producers_fabs )
cons_points = get_points( consumers_fabs )

# Now do the plotting

import numpy as np
import pylab as plt
import matplotlib.cm as cm
import matplotlib
from scipy.cluster.vq import kmeans,kmeans2,vq

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

    for point in points :
        Z += 1 / ( ( X-point[0] )**2 + ( Y-point[1] )**2 )
    # Scale to adjust radius
    Z = q * Z

    # Clip values to avoid scalling
    Z = Z.clip( -1, 1 )
    # Reduce the shadow extent
    Z = Z ** 3 #Z = np.trunc(Z)

    null_threshold = 0.4
    Z = np.where( abs(Z) > null_threshold , Z, 0)

    return Z / ( np.sign(Z) ** 2 )

map_alpha=0.75
CGREEN = np.array([0.0, 1.0, 0.0, map_alpha])
CBLUE  = np.array([0.0, 0.0, 1.0, map_alpha])
CRED   = np.array([1.0, 0.0, 0.0, map_alpha])

map_bg = np.empty([groesse_y, groesse_x, 4])

k = simworld.koord(0,0)
for kx in range(groesse_x) :
    k.x = kx
    for ky in range(groesse_y) :
        k.y = ky
        gr = welt.lookup_kartenboden(k)
        map_bg[ky][kx] = CBLUE if gr.is_wasser else CGREEN
        if gr.hat_wege : map_bg[ky][kx] = CRED

plt.imshow( map_bg ,
        interpolation='nearest')

plt.imshow( field_for_points(prod_points) ,
        interpolation='nearest', alpha=0.4,
        cmap = cm.Reds)

plt.imshow( field_for_points(cons_points) ,
        interpolation='nearest', alpha=0.4,
        cmap = cm.Blues)

#---- Do Clustering
data = np.array( prod_points + cons_points*5 )
K_init = len(cons_points) + 2 # np.array( cons_points ) 
K = len(cons_points)
# computing K-Means with K = 2 (2 clusters)
centroids,_ = kmeans2(data, K_init, minit='random')

print 'With %d observations, got %d centroids' % (K, len(centroids))
#print '%r' % K_init
#print '%r' % centroids
K = len(centroids)
# assign each sample to a cluster
idx,_ = vq(data,centroids)

def plot_k_mean_clustering():
    import itertools

    cluster_colors = itertools.cycle(['b', 'r', 'c', 'm', 'y', 'g'])

    for ki in range(K):
        color = cluster_colors.next()
        #plot( data[idx==ki,0], data[idx==ki,1], 'o%s' % color )
        #plot( centroids[ki,0], centroids[ki,1], 'xg', markersize=15, lw=20 )
        plt.scatter( data[idx==ki,0], data[idx==ki,1], c=color, marker='o') 
        plt.scatter( centroids[ki,0], centroids[ki,1], s=15**2, c=(0.2,0.4,0.2,0.7), marker='x', lw=2)

# ----------------------------------------------------
# Generate the Voronoi diagrams
#
def circumcircle(P1, P2, P3): 
    ''' 
    Return center of the circle containing P1, P2 and P3 

    If P1, P2 and P3 are colinear, return None 

    Adapted from: 
    http://local.wasp.uwa.edu.au/~pbourke/geometry/circlefrom3/Circle.cpp
    ''' 
    delta_a = P2 - P1 
    delta_b = P3 - P2 
    if np.abs(delta_a[0]) <= 0.000000001 and np.abs(delta_b[1]) <= 0.000000001: 
        center_x = 0.5*(P2[0] + P3[0]) 
        center_y = 0.5*(P1[1] + P2[1]) 
    else: 
        aSlope = delta_a[1]/delta_a[0] 
        bSlope = delta_b[1]/delta_b[0] 
        if np.abs(aSlope-bSlope) <= 0.000000001: 
            return None 
        center_x= (aSlope*bSlope*(P1[1] - P3[1]) + bSlope*(P1[0] + P2 [0]) \
                        - aSlope*(P2[0]+P3[0]))/(2.*(bSlope-aSlope)) 
        center_y = -(center_x - (P1[0]+P2[0])/2.)/aSlope + (P1[1]+P2[1])/2. 
    return center_x, center_y 

def voronoi(X,Y): 
    ''' Return line segments describing the voronoi diagram of X and Y ''' 
    P = np.zeros((X.size+4,2)) 
    P[:X.size,0], P[:Y.size,1] = X, Y 
    # We add four points at (pseudo) "infinity" 
    m = max(np.abs(X).max(), np.abs(Y).max())*1e5 
    P[X.size:,0] = -m, -m, +m, +m 
    P[Y.size:,1] = -m, +m, -m, +m 
    D = matplotlib.tri.Triangulation(P[:,0],P[:,1]) 
    T = D.triangles 
    n = T.shape[0] 
    C = np.zeros((n,2)) 
    for i in range(n): 
        C[i] = circumcircle(P[T[i,0]],P[T[i,1]],P[T[i,2]]) 
    X,Y = C[:,0], C[:,1] 
    segments = [] 
    for i in range(n): 
        for k in D.neighbors[i]: 
            if k != -1: 
                segments.append([(X[i],Y[i]), (X[k],Y[k])]) 
    return segments 

X = centroids[:,0]
Y = centroids[:,1]

#fig = plt.figure(figsize=(10,10)) 
#axes = plt.subplot(1,1,1) 
#axes = subplot(1,1,1)

segments = voronoi(X,Y) 
lines = matplotlib.collections.LineCollection(segments, color='0.75')
#axes.add_collection(lines) 

#axis([0,1,0,1]) 

plt.grid(True)

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
marker_size = 8**2
marker_color = 'k'

plt.scatter(x=get_x_list(coal_producers), y=get_y_list(coal_producers), marker='^',
c=marker_color, s=marker_size, lw=0.0 )
plt.scatter(x=get_x_list(coal_consumers), y=get_y_list(coal_consumers), marker='^',
c=marker_color, s=marker_size, lw=0.0 )

plt.scatter(x=get_x_list(waste_producers), y=get_y_list(waste_producers), marker='s',
c=marker_color, s=marker_size, lw=0.0 )
plt.scatter(x=get_x_list(waste_consumers), y=get_y_list(waste_consumers), marker='s',
c=marker_color, s=marker_size, lw=0.0 )

plot_k_mean_clustering()

#plt.tight_layout(pad=0.5)

saved_axis = plt.axis()
print 'Axis: %r ' % (plt.axis(), )

axes = plt.subplot(1,1,1) 
axes.add_collection(lines) 

print 'Axis: %r ' % (plt.axis(), )

plt.axis(saved_axis)

print 'Axis restored:  %r ' % (plt.axis(), )

plt.show()
#plt.savefig('test.png', bbox_inches='tight')

