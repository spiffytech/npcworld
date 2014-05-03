import simplejson as json
import flask
from flask import Flask, render_template, Response, redirect, request
app = Flask(__name__, static_path="/static")

import math
from functools import partial
import os.path
from PIL import Image
from pprint import pprint
import random
import sys
import time

from dijkstar import Graph, find_path

random.seed(time.time)

from fn import recur

from dogpile.cache import make_region
dpc = make_region().configure('dogpile.cache.memory')

from collections import namedtuple

from lib.attr_update import attr_update

freqs_e = {}
freqs_m = {}
freqs_t = {}

from lib import simplexnoise as sn
import noise

from collections import namedtuple
Cell = namedtuple("Cell", "type_ x y")

#@app.route("/render_viewport")
#def render_viewport():
#    grid = dpc.get_or_create("grid", make_world_grid, 60*60)
#    width, height = map(int, request.args.get("size").split("x"))
#    scale = .5  # TODO: Get this from browser
#    top_left_a, top_left_b = map(int, request.args.get("top_left").split("x"))
#    tiles = tiles_in_viewport(
#       grid= grid,
#       pos={"a": top_left_a, "b": top_left_b},
#       viewport_width=width,
#       viewport_height=height,
#       scale=scale
#    )
#
#    return Response(json.dumps(dict(tiles=tiles)), mimetype="application/json")
#
def event(e):
    if not hasattr(event, "events"):
        event.events = []
    event.events.append(e)
    def func(f):
        return f
    return func


def movement_stream():
    def build_sse_message(event_type, event_id, data):
        msg = "id: %s\nevent: %s\n" % (event_id, event_type)
        for line in data.strip().split("\n"):
            msg += "data: %s\n" % line
        msg += "\n"
        return str(msg)

    grid = dpc.get_or_create("grid", make_world_grid, 60*60)
    print "Making graph..."
    graph = dpc.get_or_create("graph", lambda: make_graph(grid), 60*60)
    print "Graph made"

    time.sleep(.1)  # Idunno, just give the drawing layer a chance to catch up. Don't know if it's necessary.
    Worldstate = namedtuple("Worldstate", "dots time grid graph")
    worldstate = Worldstate(dots=tuple(), time=0, grid=grid, graph=graph)
    while True:
        browser_notifications = []
        events = dot_ai(worldstate)
        
        @recur.tco
        def handle_events(old_world, new_world, events):
            event = events[0]
            pre, handler, applier  = get_handler(event["class"])
            assert(pre is not None)
            assert(handler is not None)
            assert(applier is not None)
            world_params = pre(old_world)
            results = handler(world_params, event["params"])  # TODO: Add event params to this list
            newer_world = applier(new_world, **results)

            if len(events) == 0:
                return False, new_world
            return True, (old_world, new_world, events[1:])

        @event("notify_browser")
        def notify_browser():
            def pre(worldstate):
                return dict(time=worldstate.time)

            def handler(world_params, event_params):
                # TODO: Don't mutate state. Fix that once ZMQ is in place and we can pub/sub to the browser subscribers.
                browser_notifications.append(build_sse_message(
                    event_type=event_params["event_type"],
                    event_id=world_params["time"],
                    data=json.dumps(event_params["payload"])
                ))
                
            def applier(new_world, **results):
                return new_world

            return pre, handler, applier

        worldstate = handle_events(worldstate, worldstate, events)

        for event in browser_notifications:  # TODO: Move this once the event loop gets separated from the browser subscribers
            yield event

        delta_t = 1
        worldstate = attr_update(worldstate, time=time+t_delta)
        time.sleep(t_delta)

def dot_ai(worldstate):
    import pdb; pdb.set_trace()
    if worldstate.time == 0:  # Second event - move dots
        # TODO: Update this such that it always /looks/ like it's going in the optimal path, even if it actually is
        # E.g., 20,20 -> 139,100 starts with an upward diagonal, even though that /looks like/ it's running away from the target
        def cf(u, v, e, prev_e):
            grid = worldstate.grid
            cell_type = grid[v[0]][v[1]]
            return sys.maxint if cell_type in ["shallow_water", "deep_water"] else 1

        graph = worldstate.graph
        dots = [
            {
                "dot_id": 1,
                "color": "red",
                "x": 10,
                "y": 10,
                "dest": (29, 1),
                "path": find_path(graph, (10, 10), (159, 1), cost_func=cf)[0],  # [0] is path, [1] is cost for each traversal, [2] is total cost
                "costs": find_path(graph, (10, 10), (159, 1), cost_func=cf)[1]  # [0] is path, [1] is cost for each traversal, [2] is total cost
            }, {
                "dot_id": 2,
                "color": "blue",
                "x": 20,
                "y": 20,
                "dest": (30, 1),
                "path": find_path(graph, (20, 20), (139, 100), cost_func=cf)[0],  # [0] is path, [1] is cost for each traversal, [2] is total cost
                "costs": find_path(graph, (20, 20), (139, 100), cost_func=cf)[1]  # [0] is path, [1] is cost for each traversal, [2] is total cost
            }
        ]
        for dot in dots:
            events.append(dict(event_type="new_dot", payload=dot))
        return

    events = []  # TODO: No mutable state. This is just a dummy experimental function, anyway.
    if worldstate.time == 1:  # Second event - move dots
        for dot in worldstate.dots:
            payload = dict(
                dot_id = dot["dot_id"],
                path = dot["path"],
                speed = .1  # sleep time. TODO: Replace this with fixed timestapms instead of sleep durations.
            )
            events.append(dict(event_type="movement", payload=payload))
        return

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

@app.route("/movement")
def movement():
    return Response(movement_stream(), mimetype="text/event-stream");

def viewport_size_in_tiles(width, height, scale):
    TILE_WIDTH = 168
    TILE_HEIGHT = 97
    print "viewport size:", (width, height, scale)
    pprint((
        int(math.ceil(width / (TILE_WIDTH * scale)))*2,
        int(math.ceil(height / (TILE_HEIGHT * scale)))*2
    ))
    return (
        int(math.ceil(width / (TILE_WIDTH * scale)))*2,
        int(math.ceil(height / (TILE_HEIGHT * scale)))*2
    )

def tiles_in_viewport(grid, pos, viewport_width, viewport_height, scale):
    width, height = viewport_size_in_tiles(viewport_width, viewport_height, scale)

    viewport_a = pos["a"]
    viewport_b = pos["b"]

    print "pos =", pos
    print "viewport_a =", (viewport_a, viewport_a + width)
    print "viewport_b =", (viewport_b, viewport_b + height)
    print "width =", width
    print "height =", height

    ret = []
    for a in range(viewport_a, viewport_a + width):
        ret.append([])
        for b in range(viewport_b, viewport_b + height):
            if (a&1) != (b&1):  # Both even / both odd. Prevent duplicate x/y pairs?
                continue
            x = (a+b)/2
            y = (a-b)/2
            assert y >= 0
            ret[-1].append(Cell(x=x, y=y, type_=grid[x][y]))

    all_ = tuple(cell for row in ret for cell in row)

    # Assert no duplicate x or y values
    bins = []
    for x in set(r.x for r in all_):
        bins.append(sorted(tuple(r.y for r in all_ if r.x == x)))
    for bin_ in bins:
        try:
            assert bin_ == range(bin_[0], bin_[-1]+1)
        except AssertionError:
            print bin_
            print range(bin_[0], bin_[-1]+1)
            raise

    bins = []
    for y in set(r.y for r in all_):
        bins.append(sorted(tuple(r.x for r in all_ if r.y == y)))
    for bin_ in bins:
        try:
            assert bin_ == range(bin_[0], bin_[-1]+1)
        except AssertionError:
            print bin_
            print range(bin_[0], bin_[-1]+1)
            raise

    return ret


    ret = tuple(
        tuple(grid[(a+b)/2][(a-b)/2] for b in range(viewport_b, viewport_b + height) if (a&1) == (b&1))
        for a in range(viewport_a, viewport_a + width)
    )
    pprint(ret)
    return ret


@app.route("/sample_noise")
def sample_noise():
    grid = dpc.get_or_create("grid", make_world_grid, 60*60)
    dpc.get_or_create("render_minimap", lambda: render_to_png("terrain.png", colorize_minimap(grid)), 60*60)
    return redirect("/static/terrain.png", code=302)

@app.route("/cell_type")
def query_cell_type():
    grid = dpc.get_or_create("grid", make_world_grid, 60*60)
    return grid[int(request.args.get("x"))][int(request.args.get("y"))]

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


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

    #import cProfile
    #cProfile.run("sample_noise()", sort="cumulative")
