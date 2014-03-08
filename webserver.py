import json
import flask
from flask import Flask, render_template, Response
app = Flask(__name__, static_path="/static")

import math
from pprint import pprint
import random
import time

freqs_e = {}
freqs_m = {}
freqs_k = {}
raw_noise = []

from lib import simplexnoise as sn
import noise
@app.route("/sample_noise")
def sample_noise():
    print "Generating noise"
    global freqs_e
    global freqs_m
    global freqs_k
    global raw_noise
    freqs_e = {}
    freqs_m = {}
    freqs_k = {}
    raw_noise = []

    offset = time.time()

    max_x = 1200
    max_y = 600
    octaves=6
    persistence=.25
    scale=2
    smoothness=.003  # .003 works OK
    f=simplex2
    grid = tuple(
        tuple(colorize(
            f(  # Elevation
                octaves=octaves,
                persistence=persistence,  # amplitude
                scale=scale,  # frequency
                x=x*smoothness,
                y=y*smoothness
            ),
            f(  # Moisture
                octaves=octaves,
                persistence=persistence,  # amplitude
                scale=scale,  # frequency
                x=(x+offset)*smoothness,
                y=(y+offset)*smoothness
            )
        ) for y in xrange(max_y))
        for x in xrange(max_x)
    )
            
    print "Returning noise"

    # Log data
    print "Elevation: ",
    pprint(freqs_e)
    print "Moisture:  ",
    pprint(freqs_m)
    print "Pairs:  ",
    pprint(freqs_k)
    random.shuffle(raw_noise)
    with open("static/raw_noise.log", "w+") as f:
        f.write("\n".join(str(round(x, 1)) for x in raw_noise[:1000]))

    return Response(json.dumps(dict(grid=grid)), mimetype="application/json")

def colorize(elevation, moisture):
    #c = linear_interpolation(0, 255, elevation)
#    return (c, c, c)

    terrains = {
        # (elevation,moisture)
        (0,1): (85, 125, 166),  # Shallow water
        (0,2): (85, 125, 166),  # Shallow water
        (0,3): (85, 125, 166),  # Shallow water
        (0,4): (54, 54, 97),  # Deep water
        (0,5): (54, 54, 97),  # Deep water
        (0,6): (54, 54, 97),  # Deep water

        (1,1): (189, 116, 23),  # Subtropical desert
        (1,2): (113, 161, 59),  # Grassland
        (1,3): (4, 38, 8),  # Tropical seasonal forest
        (1,4): (4, 38, 8),  # Tropical seasonal forest
        (1,5): (42, 92, 11),  # Tropical rainforest
        (1,6): (42, 92, 11),  # Tropical rainforest

        (2,1): (196, 171 ,40),  # Temperate desert
        (2,2): (113, 161, 59),  # Grassland
        (2,3): (113, 161, 59),  # Grassland
        (2,4): (128, 143, 18),  # Temperate deciduous forest
        (2,5): (128, 143, 18),  # Temperate deciduous forest
        (2,6): (68, 82, 47),  # Temperate rainforest

        (3,1): (196, 171 ,40),  # Temperate desert
        (3,2): (196, 171 ,40),  # Temperate desert
        (3,3): (221, 244, 133),  # Shrubland
        (3,4): (221, 244, 133),  # Shrubland
        (3,5): (204, 212, 187),  # Taiga
        (3,6): (204, 212, 187),  # Taiga

        (4,1): (153, 153, 153),  # Scorched
        (4,2): (187, 187, 187),  # Bare
        (4,3): (221, 221, 187),  # Tundra
        (4,4): (248, 248, 248),  # Snow
        (4,5): (248, 248, 248),  # Snow
        (4,6): (248, 248, 248),  # Snow
    }

    raw_noise.append(elevation)

    def segment(x, a, b, segments):
        total = sum(segments)
        increment = (b-a)/(total*1.0)  # Floating division!
        bin_sizes = [increment * segment for segment in segments]
        bottom = a
        for i in xrange(len(bin_sizes)):
            bottom += bin_sizes[i]
            if x <= bottom:
                return i
        return len(segments)-1

    ek = segment(elevation, -1, 1, [90, 30, 30, 30, 50])
    mk = segment(moisture, -1, 1, [30, 30, 30, 30, 30, 30])+1
    #if elevation < -.75:
    #    ek = 0
    #elif elevation < 0:
    #    ek = 1
    #elif elevation < .3:
    #    ek = 2
    #elif elevation < 1:
    #    ek = 3
    #else:
    #    ek = 4

    #if moisture < 0:
    #    mk = 1
    #elif moisture < .5:
    #    mk = 2
    #elif moisture < 1:
    #    mk = 3
    #elif moisture < 1.6:
    #    mk = 4
    #elif moisture < 1.8:
    #    mx = 5
    #else:
    #    mk = 6

    key = (ek, mk)

    if key[0] not in freqs_e:
        freqs_e[key[0]] = 1
    else:
        freqs_e[key[0]] += 1

    if key[1] not in freqs_m:
        freqs_m[key[1]] = 1
    else:
        freqs_m[key[1]] += 1

    if key not in freqs_k:
        freqs_k[key] = 1
    else:
        freqs_k[key] += 1

    try:
        return terrains[key]
    except:
        print (
            linear_interpolation(0, 4, elevation),
            linear_interpolation(1, 6, moisture)
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
    f = (1 - math.cos(ft)) * .5
    return  a*(1-f) + b*f

def smooth(x, y):
    corners = ( Noise(x-1, y-1)+Noise(x+1, y-1)+Noise(x-1, y+1)+Noise(x+1, y+1) ) / 16
    sides   = ( Noise(x-1, y)  +Noise(x+1, y)  +Noise(x, y-1)  +Noise(x, y+1) ) /  8
    center  =  Noise(x, y) / 4
    return corners + sides + center

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
