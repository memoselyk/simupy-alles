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
    #11   # Grain
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
print 'Loading world...'
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

waste_producers = []# f for f in fabs_in_welt if is_producer_of_good(f, WASTE_INDEX) ]
waste_consumers = []# f for f in fabs_in_welt if is_consumer_of_good(f, WASTE_INDEX) ]

coal_producers = []# f for f in fabs_in_welt if is_producer_of_good(f, COAL_INDEX) ]
coal_consumers = []# f for f in fabs_in_welt if is_consumer_of_good(f, COAL_INDEX) ]

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
from scipy.cluster.vq import kmeans # ,kmeans2,vq
import scipy.cluster.hierarchy as sch

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

map_alpha=0.60
CGREEN = np.array([0.0, 1.0, 0.0, map_alpha])
CBLUE  = np.array([0.0, 0.0, 1.0, map_alpha])
CRED   = np.array([1.0, 0.0, 0.0, map_alpha])

map_bg = np.empty([groesse_y, groesse_x, 4])

print 'Generating bg map'
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

centroids = np.array( prod_points + cons_points )
X = centroids[:,0]
Y = centroids[:,1]

#fig = plt.figure(figsize=(10,10)) 
#axes = plt.subplot(1,1,1) 
#axes = subplot(1,1,1)

#
# Disable voronoi routing
#segments = voronoi(X,Y) 
#lines = matplotlib.collections.LineCollection(segments, color='0.95')
#axes.add_collection(lines) 

#axis([0,1,0,1])

delaunayTriang = matplotlib.tri.Triangulation(X,Y)
routeIndexes = delaunayTriang.edges

def calculateRouteDistance(r_idx):
    r_s, r_e = routeIndexes[r_idx]
    r_s = centroids[r_s]
    r_e = centroids[r_e]
    # Eucledian distance
    import math
    return math.sqrt( (r_e[0] - r_s[0])**2 + (r_e[1] - r_s[1])**2 )

distances = [ calculateRouteDistance(i) for i in range(len(routeIndexes)) ]

print 'Min distance : %s' % min(distances)
print 'Max distance : %s' % max(distances)

drange = max(distances) - min(distances)

#routeColors = [ 0.05 + 0.7*(drange - (d - min(distances)))/drange for d in distances ]
#routeColors = [ (c,c,c,1.0) for c in routeColors ]

delaunayRoutes = []
for si, ei in routeIndexes :
    delaunayRoutes.append( (centroids[si], centroids[ei]) )

routesUsage = [ 0 for n in routeIndexes ]

class Route:
    def __init__(self, nodes, edge_idx, cumdist):
        self.seq = tuple(nodes)
        self.edges = tuple(edge_idx)
        self.cumdist = cumdist

    def __cmp__(self, other):
        return cmp(self.cumdist, other.cumdist)

def get_all_edges(start, exception):
    connected_edges = []
    for num, pts in enumerate(routeIndexes) :
        p0, p1 = pts
        if p0 != start and p1 != start :
            continue
        # Start is in p0 or p1
        if p1 == start :
            p0, p1 = (p1, p0)
        # Start is p0
        if p1 in exception :
            continue
        connected_edges.append((num, (p0,p1)))
    return connected_edges

def find_route_by_distance(s_idx, e_idx) :
    import bisect

    print 'Finding route between %d - %d' % (s_idx, e_idx)

    potential_routes = [ Route([s_idx], [], 0) ]
    visited_nodes = set([])

    while True :    # FIXME: can give other condition??
        current_best = potential_routes.pop(0)
        last_point = current_best.seq[-1]
        
        next_edges = get_all_edges(last_point, visited_nodes)

        for edg_idx, pts in next_edges :
            next_pt = pts[1]
            edg_dist = distances[edg_idx]
            new_route = Route(
                    current_best.seq + (next_pt, ),
                    current_best.edges + (edg_idx, ) ,
                    current_best.cumdist + edg_dist )

            if next_pt == e_idx : return new_route

            bisect.insort(potential_routes, new_route)

        visited_nodes.add(last_point)
        # Debugging info
        #print '... working with %d routes and %d visited nodes' % (len(potential_routes), len(visited_nodes))
        #for proute in potential_routes :
        #    print '    -> %d , %r' % (proute.cumdist, proute.edges)

def centroid_index_of_fab(fabx):
    if isinstance(fabx, simworld.fabrik_t) :
        fkoord = fabx.pos.get_2d()
    else :
        fkoord = fabx
    indxs = set( np.where(centroids == fkoord.coords())[0] )

    if len(indxs) == 0 : return -1

    return min(indxs)   # Hopefully the first index is used

# Attempt to generate a random path
from random import sample
#start_pt , end_pt = sample( range(len(delaunayTriang.x)+1) , 2)

route_lengths = []

#for consumer in consumers_fabs :
#    end_pt = centroid_index_of_fab( consumer )
for producer in producers_fabs :
    start_pt = centroid_index_of_fab( producer )

    consumer_count = 0

#    for supplier in consumer.get_suppliers() :
#        start_pt = centroid_index_of_fab( supplier )
    for destination in producer.get_consumers() :
        end_pt = centroid_index_of_fab( destination )
        
        # Not all suppliers/consumers handle good of interest
        if start_pt == -1 or end_pt == -1 : continue    # Silently skipping

        # Some Fabriks generate and consume the same type of Good
        if start_pt == end_pt :
            print 'Skipping route between %d (%s) -> %d (%s)' % (start_pt, centroids[start_pt], end_pt, centroids[end_pt] )
            continue

        if consumer_count == 1 : break
        consumer_count += 1

        print 'Calculating route between %d (%s) -> %d (%s)' % (start_pt, centroids[start_pt], end_pt, centroids[end_pt] )

        given_route = find_route_by_distance(start_pt, end_pt)
        print 'Found best route : %r' % (given_route.seq, )
        print '  with %d edges : %r' % (len(given_route.edges), given_route.edges )
        print '  with cost  : %s' % given_route.cumdist

        route_lengths.append( len(given_route.edges) )

        # TODO Remember long routes for further display

        for edg_idx in given_route.edges :
            routesUsage[edg_idx] += 1

print 'Route length range %d - %d' % (min(route_lengths), max(route_lengths))

route_lengths = np.array( route_lengths )
print 'Lengths: ', np.histogram( route_lengths, bins=np.arange(route_lengths.max() +2) -0.5 )

print 'Route usage range %d - %d' % (min(routesUsage), max(routesUsage))

print 'Usage hist :', np.histogram( routesUsage, bins=np.arange(max(routesUsage) +2) -0.5 )

compacted_route_usage = sorted(set(routesUsage))
if compacted_route_usage[0] != 0 :
    compacted_route_usage.insert(0,0)

routesUsage = [ compacted_route_usage.index(u) for u in routesUsage ]

print 'Route usage NEW range %d - %d' % (min(routesUsage), max(routesUsage))

colors_4_routes = [
        (0  , 1.0, 1.0, 1.0),  # Cyan
        (0  , 0  , 1.0, 1.0),  # Blue
        (1.0, 0  , 1.0, 1.0),  # Magenta
        (1.0, 0  , 0  , 1.0),  # Red
        (0  , 0  , 0  , 1.0),  # Black
    ]
#
# Deprecated code
#routeColors = [ (0.85 if usage == 0 else 0.05) for usage in routesUsage ]
#routeColors = [ (c,c,c,1.0) for c in routeColors ]
routeColors = [ 
    ((0.85,0.85,0.85,1.0) if usage == 0 
    else colors_4_routes[(usage-1) % len(colors_4_routes)]) 
    for usage in routesUsage ]

line_styles = [
    'solid',
    #'dashdot',
    'dashed',
    'dotted',
]

#routeStyles = [ line_styles[((u-1)/len(colors_4_routes))%3] for u in routesUsage ]

routeWidths = [ ( (u-1)/( len(colors_4_routes) ) +1 if u != 0 else 0 ) for u in routesUsage ]

routeStyles = [ line_styles[ (s-1) % len(line_styles) ] for s in routeWidths ]

routesCollection = matplotlib.collections.LineCollection( delaunayRoutes, color=routeColors, linewidths=routeWidths, linestyles=routeStyles )

#
# 'Plot' start and end points
marker_size = 8**2
marker_color = 'k'
#plt.scatter(x=[ X[start_pt] ], y=[ Y[start_pt] ], marker='^',
#        c=marker_color, s=marker_size, lw=0.0 )
#plt.scatter(x=[ X[end_pt] ], y=[ Y[end_pt] ], marker='s',
#        c=marker_color, s=marker_size, lw=0.0 )

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

#plt.tight_layout(pad=0.5)

saved_axis = plt.axis()
print 'Axis: %r ' % (plt.axis(), )

axes = plt.subplot(1,1,1) 
#axes.add_collection(lines) 

axes.add_collection(routesCollection)

print 'Axis: %r ' % (plt.axis(), )

plt.axis(saved_axis)

print 'Axis restored:  %r ' % (plt.axis(), )

fig = plt.gcf()
fig.set_size_inches(16.0,16.0)

F = plt.gcf()
# Now check everything with the defaults:
DPI = F.get_dpi()
print "DPI:", DPI
DefaultSize = F.get_size_inches()
print "Default size in Inches", DefaultSize
print "Which should result in a %i x %i Image"%(DPI*DefaultSize[0], DPI*DefaultSize[1])
# the default is 100dpi for savefig:
F.savefig("test1.png")

plt.show()
#plt.savefig('test.png', bbox_inches='tight')

