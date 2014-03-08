import json
import flask
from flask import Flask, render_template, Response
app = Flask(__name__, static_path="/static")

import math

from lib import simplexnoise as sn
import noise
@app.route("/sample_noise")
def sample_noise():
    print "Generating noise"
    max_x = 1200
    max_y = 600
    octaves=5
    persistence=.25
    scale=1
    smoothness=.003
    f=simplex2
    grid = tuple(
        tuple(f(
            octaves=4,
            persistence=.5,  # amplitude
            scale=2,  # frequency
            x=x*smoothness,
            y=y*smoothness
        ) for y in xrange(max_y))
        for x in xrange(max_x)
    )
            
    print "Returning noise"
    return Response(json.dumps(dict(grid=grid)), mimetype="application/json")

def simplex1(octaves, persistence, scale, x, y):
        return sn.scaled_octave_noise_2d(
            octaves=octaves,
            persistence=persistence,  # amplitude
            scale=scale,  # frequency
            loBound=0,
            hiBound=255,
            x=x*smoothness,
            y=y*smoothness
        )

def simplex2(octaves, persistence, scale, x, y):
    return noise.snoise2(x, y, octaves, persistence, scale)
    return cosine_interpolation(0, 255, noise.snoise2(x, y, octaves, persistence, scale))

def linear_interpolation(a, b, x):
    return  a*(1-x) + b*x

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
