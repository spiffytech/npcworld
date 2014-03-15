import json
import flask
from flask import Flask, render_template, Response, redirect
app = Flask(__name__, static_path="/static")

import math
from functools import partial
import os.path
from PIL import Image
from pprint import pprint
import random
import time

freqs_e = {}
freqs_m = {}
freqs_t = {}
raw_noise = []

from lib import simplexnoise as sn
import noise
@app.route("/sample_noise")
def sample_noise():
    print "Generating noise"
    global freqs_e
    global freqs_m
    global freqs_t
    global raw_noise
    freqs_e = {}
    freqs_m = {}
    freqs_t = {}
    raw_noise = []

    offset = time.time()/10000.0
    offset += (offset-int(offset)) * 1000

    max_x = 1100
    max_y = 600

    octaves=9  # Higher than 10 makes no difference
    persistence=.5
    scale=2
    smoothness=.004  # .003 works OK
    #color_fn = colorize
    #color_fn = colorize2
    color_fn = colorize_multi
    #color_fn = simple_color
    f = partial(simplex3,
        octaves=octaves,
        persistence=persistence,  # amplitude
        scale=scale  # frequency
    )
    grid = tuple(
        tuple(color_fn(
            f(
                x=(x+offset)*smoothness,
                y=(y+offset)*smoothness,
                z=0
            ),
            x=(x+offset)*smoothness,
            y=(y+offset*2)*smoothness,
            f=f
        ) for x in xrange(max_x))
        for y in xrange(max_y)
    )
            
    print "Returning noise"

    # Log data
    print "Elevation: ",
    pprint(freqs_e)
    print "Moisture:  ",
    pprint(freqs_m)
    print "Pairs:  ",
    pprint(freqs_t)
    random.shuffle(raw_noise)
    with open("static/raw_noise.log", "w+") as f:
        f.write("\n".join(str(round(x, 1)) for x in raw_noise[:1000]))

    render_to_png("terrain.png", grid)
    return redirect("/static/terrain.png", code=302)
    #return Response(json.dumps(dict(grid=grid)), mimetype="application/json")

def render_to_png(filename, data):
    image = Image.new('RGB', (len(data[0]), len(data)))  # type, size
    out = []
    for row in data:
        for pixel in row:
            out.append(tuple(pixel))
    image.putdata(out)
    image.save(os.path.join("static", filename))  # takes type from filename extension

def simple_color(val, x, y, f):
    c = sine_interpolation(0, 255, val)
    return (c, c, c)

def segmentize(x, a, b, segments):
    total = sum(segments)
    increment = (b-a)/(total*1.0)  # Floating division!
    bottom = a
    for i,v in enumerate(increment * segment for segment in segments):
        bottom += v
        if x <= bottom:
            return i
    return len(segments)-1

def colorize(elevation, x, y, f):
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

    raw_noise.append(elevation)  # Logging

    ek = segmentize(elevation, -1, 1,  [10, 10, 10, 10])
    mk = segmentize(moisture, -1, 1,  [15, 20, 10, 10, 20, 10])
    key = (ek, mk)

    if key[0] not in freqs_e:
        freqs_e[key[0]] = 1
    else:
        freqs_e[key[0]] += 1

    if key[1] not in freqs_m:
        freqs_m[key[1]] = 1
    else:
        freqs_m[key[1]] += 1

    terrain = ek_map[key]
    if terrain not in freqs_t:
        freqs_t[terrain] = 1
    else:
        freqs_t[terrain] += 1

    try:
        return terrains[terrain]
    except:
        print (
            linear_interpolation(0, 4, elevation),
            linear_interpolation(1, 6, moisture)
        )
        raise

def colorize2(val, x, y, f):
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

    m = {
        0: "deep_water",
        1: "shallow_water",
        2: "shrubland",  # beaches
        3: "temperate_desert",
        4: "grassland",
        5: "tropical_seasonal_forest",
        6: "temperate_deciduous_forest",
        7: "tundra",
        8: "taiga",
        9: "snow",
    }
    
    k = segmentize(val, -1, 1,  [90, 30, 10, 10, 10, 10, 10, 10, 10, 15])
    return terrains[m[k]]

def colorize_multi(val, x, y, f):
    iw = segmentize(
        f(
            x=x+((x**2)/180)*.01,
            y=y+((y**2)/180)*.01,
            z=0
        ), -1, 1, [20, 5, 25]
    )
    if iw == 0:
        return  (54, 54, 97)  # Deep water
    elif iw == 1:
        return (85, 125, 166)  # Shallow water

    return colorize(val, x, y, f)


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

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)

    #import cProfile
    #cProfile.run("sample_noise()", sort="cumulative")
