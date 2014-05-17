from __future__ import division
from __future__ import absolute_import

from npcworld.lib import events, utils

import simplejson as json
import flask
from flask import Flask, render_template, Response, redirect, request
app = Flask(__name__, static_path="/static")

import threading

from fn.uniform import *
from fn import recur, _

from collections import namedtuple


freqs_e = {}
freqs_m = {}
freqs_t = {}

from lib import engine

from collections import namedtuple
Cell = namedtuple("Cell", "type_ x y")

logger = utils.logger

@app.route("/movement")
def movement():
    logger.info("Starting event stream")
    def streamer():
        logger.info("This is the event stream")
        logger.debug("Queue size to browser: %d", events.browser_events.qsize())
        logger.debug("Queue ID to browser: %s", id(events.browser_events))
        while True:
            event = events.browser_events.get()
            logger.debug("Got event from browser queue")
            yield event
            logger.debug("Yielded event")
        logger.warn("Aborting event stream")

    return Response(streamer(), mimetype="text/event-stream");

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
    return redirect("/static/terrain.png", code=302)

@app.route("/cell_type")
def query_cell_type():
    grid = dpc.get_or_create("grid", make_world_grid, 60*60)
    return grid[int(request.args.get("x"))][int(request.args.get("y"))]

threading.Thread(target=engine.run_game).start()
logger.info("Game thread started")
if __name__ == "__main__":
    logger.debug("Main running")

    app.run(host="0.0.0.0", debug=True)

    #import cProfile
    #cProfile.run("sample_noise()", sort="cumulative")
