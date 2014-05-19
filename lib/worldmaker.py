import math
from dijkstar import Graph, find_path
from filecache import filecache
from PIL import Image
import os.path
from functools import partial
import random
import time

from pprint import pprint

from npcworld.lib import simplexnoise as sn
import noise

random.seed(time.time)

@filecache(60*60)
def make_world_grid():
    print "Generating noise"
    global freqs_e
    global freqs_m
    global freqs_t
    freqs_e = {}
    freqs_m = {}
    freqs_t = {}

    offset = random.randint(0, 1000000)

    max_x = 1100
    max_y = 600

    octaves=9  # Higher than 10 makes no difference
    persistence=.5
    scale=2
    smoothness=.004  # .003 works OK
    f = partial(simplex3,
        octaves=octaves,
        persistence=persistence,  # amplitude
        scale=scale,  # frequency
    )
    grid = tuple(
        tuple(make_terrain(
            f(
                x=(x+offset)*smoothness,
                y=(y+offset*2)*smoothness,
                z=0
            ),
            x=(x+offset)*smoothness,
            y=(y+offset*2)*smoothness,
            f=f
        ) for y in xrange(max_y))
        for x in xrange(max_x)
    )
    print len(grid), len(grid[0])
            
    print "Returning noise"

    # Log data
    print "Elevation: ",
    pprint(freqs_e)
    print "Moisture:  ",
    pprint(freqs_m)
    print "Pairs:  ",
    pprint(freqs_t)

    return grid

def colorize_minimap(grid):
    terrains = {
        "deep_water": (54, 54, 97),  
        "shallow_water": (85, 125, 166),  

        "subtropical_desert": (189, 116, 23),  
        "grassland": (113, 161, 59),  
        "tropical_seasonal_forest": (4, 38, 8),  
        "tropical_rainforest": (42, 92, 11),  

        "temperate_desert": (196, 171 ,40),  
        "grassland": (113, 161, 59),  
        "temperate_deciduous_forest": (128, 143, 18),  
        "temperate_rainforest": (68, 82, 47),  

        "temperate_desert": (196, 171 ,40),  
        "shrubland": (221, 244, 133),  
        "taiga": (204, 212, 187),  

        "scorched": (153, 153, 153),  
        "bare": (187, 187, 187),  
        "tundra": (221, 221, 187),  
        "snow": (248, 248, 248),  
    }

    # TODO: Tuples instead of lists
    colors = []
    for i, row in enumerate(grid):
        colors.append([])
        for cell in row:
            colors[i].append(terrains[cell])

    return colors
    return tuple(tuple(terrains[cell] for cell in row) for row in grid)  # Seems to get rows and columns confused

def segmentize(x, a, b, segments):
    total = sum(segments)
    increment = (b-a)/(total*1.0)  # Floating division!
    bottom = a
    for i,v in enumerate(increment * segment for segment in segments):
        bottom += v
        if x <= bottom:
            return i
    return len(segments)-1

def make_terrain(perlin, x, y, f):
    iw = segmentize(
        f(
            x=x+((x**2)/180)*.01,
            y=y+((y**2)/180)*.01,
            z=0
        ), -1, 1, [20, 5, 25]
    )
    if iw == 0:
        return  "deep_water"
    elif iw == 1:
        return "shallow_water"

    ek_map = {
        # (elevation,moisture)
        (0,0): "subtropical_desert",
        (0,1): "grassland",
        (0,2): "tropical_seasonal_forest",
        (0,3): "tropical_seasonal_forest",
        (0,4): "tropical_rainforest",
        (0,5): "tropical_rainforest",

        (1,0): "temperate_desert",
        (1,1): "grassland",
        (1,2): "grassland",
        (1,3): "temperate_deciduous_forest",
        (1,4): "temperate_deciduous_forest",
        (1,5): "temperate_rainforest",

        (2,0): "temperate_desert",
        (2,1): "temperate_desert",
        (2,2): "shrubland",
        (2,3): "shrubland",
        (2,4): "taiga",
        (2,5): "taiga",

        (3,0): "scorched",
        (3,1): "bare",
        (3,2): "tundra",
        (3,3): "snow",
        (3,4): "snow",
        (3,5): "snow",
    }

    moisture = f(x=x, y=y, z=2)

    #elevation, moisture = sine_interpolation(-1, 1, elevation), sine_interpolation(-1, 1, moisture)

    ek = segmentize(perlin, -1, 1,  [15, 8, 10, 8])
    mk = segmentize(perlin, -1, 1,  [15, 20, 8, 10, 20, 10])
    key = (ek, mk)

    if key[0] not in freqs_e:
        freqs_e[key[0]] = 1
    else:
        freqs_e[key[0]] += 1

    if key[1] not in freqs_m:
        freqs_m[key[1]] = 1
    else:
        freqs_m[key[1]] += 1

    try:
        return ek_map[key]
    except:
        print (
            linear_interpolation(0, 4, perlin),  # elevation
            linear_interpolation(1, 6, perlin)  # moisture
        )
        raise

def simplex1(octaves, persistence, scale, x, y):
        return sn.octave_noise_2d(
            octaves=octaves,
            persistence=persistence,  # amplitude
            scale=scale,  # frequency
            x=x*smoothness,
            y=y*smoothness
        )

def simplex2(octaves, persistence, scale, x, y):
    return noise.snoise2(x, y, octaves, persistence, scale)
    return cosine_interpolation(0, 255, noise.snoise2(x, y, octaves, persistence, scale))

def simplex3(octaves, persistence, scale, x, y, z):
    return noise.snoise3(x, y, z, octaves, persistence, scale)
    return cosine_interpolation(0, 255, noise.snoise2(x, y, octaves, persistence, scale))

def linear_interpolation(a, b, x):
    ret = (x * (b - a) / 2 + (b + a) / 2)

    #ret =  a*(1-x) + b*x
    if ret < a:  # Sometimes returns .99966 for a=1, etc.
        return a
    elif ret > b:
        return b
    else:
        return ret

def cosine_interpolation(a, b, x):
    ft = x * 3.1415927
    f = (1 - math.sin(ft)) * .5
    return  a*(1-f) + b*f

def sine_interpolation(a, b, x):
    ft = x * 3.1415927
    f = (1 - math.cos(ft)) * .5
    return  a*(1-f) + b*f

def smooth(x, y):
    corners = ( Noise(x-1, y-1)+Noise(x+1, y-1)+Noise(x-1, y+1)+Noise(x+1, y+1) ) / 16
    sides   = ( Noise(x-1, y)  +Noise(x+1, y)  +Noise(x, y-1)  +Noise(x, y+1) ) /  8
    center  =  Noise(x, y) / 4
    return corners + sides + center

def render_to_png(filename, data):
    image = Image.new('RGB', (len(data), len(data[0])))  # type, size
    # TODO: tuples
    out = []
    for col in range(len(data[0])):
        for row in range(len(data)):
            cell = data[row][col]
            out.append(tuple(cell))
    image.putdata(out)
    image.save(os.path.join("static", filename))  # takes type from filename extension

@filecache(60*60)
def make_graph(grid):
    graph = Graph()
    for x in range(len(grid)):
        for y, cell in enumerate(grid[x]):
            neighbors = get_neighbors(grid, x, y)
            for neighbor in neighbors:
                graph.add_edge(
                    (x, y),
                    (neighbor["x"], neighbor["y"]),
                )

    return graph

def get_neighbors(grid, x, y):
    max_x = len(grid)  # x
    max_y = len(grid[0])  # y
    neighbors = []
    for i in (-1, 0, 1):
        for j in (-1, 0, 1):
            if 0 <= x + i < max_x and 0 <= y + j < max_y:  # Allow referencing self, to ensure we can route to self if desired
                neighbors.append(dict(x=x+i, y=y+j))

    return neighbors

