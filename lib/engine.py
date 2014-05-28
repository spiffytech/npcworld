from collections import namedtuple
from fn import _, recur
import itertools
import time

from npcworld.lib.utils import logger
from npcworld.lib import ai, events, utils, worldmaker

from npcworld.lib.attr_update import attr_update

def calc_next_tick_time(current_tick, current_time=None):  # current_time parameter used for unit testing
    if current_time is None:
        t = time.time()
    else:
        t = current_time
    expected_next_tick = current_tick + utils.frames_to_secs(1)
    next_tick = max(expected_next_tick, t)
    delta = max(0, next_tick - t)  # Time delta to next tick. If we take < 1 frame's time to render a frame, sleep until the next frame tick. If we're taking longer than 1 frame's time to render each frame, don't sleep. 
    if delta == 0:
        logger.warn("Frame ran too long by %f secs", t - expected_next_tick)

    return (
        next_tick,
        delta
    )

def run_game():
    logger.info("Running the game")
    grid = utils.dpc.get_or_create("grid", worldmaker.make_world_grid, 60*60)
    utils.dpc.get_or_create("render_minimap", lambda: worldmaker.render_to_png("terrain.png", worldmaker.colorize_minimap(grid)), 60*60)
    graph = utils.dpc.get_or_create("graph", lambda: worldmaker.make_graph(grid), 60*60)
    logger.info("Graph made")

    Worldstate = namedtuple("Worldstate", "entities ticks grid graph")
    worldstate = Worldstate(
        entities=tuple(),
        ticks=0,
        grid=grid,
        graph=graph,

        #For event handling, consider having each Event contain an applicator function. That way you don't need global functions available for all events, some specialized logic can just return a specialized applicator function. You can still return globally-available applicators if you want to do something generic. TODO: Figure out how this plays with sorting event handling order.

    )

    logger.info("Starting game loop")
    game_loop(worldstate, time.time())
    logger.critical("Movement stream loop ended early!")

@recur.tco
def game_loop(worldstate, current_tick_time, ttl=None):
    logger.debug("New tick: %d", worldstate.ticks)

    events_ = itertools.chain(
        ai.dot_ai(worldstate),
        events.process_browser_events(worldstate)
    )
    worldstate = events.handle_events(worldstate, events_)  # TODO: New variable name, because FP

    new_worldstate = attr_update(
        worldstate,
        ticks=_+1,  # Elapsed ticks in game
    )

    next_tick_time, delta = calc_next_tick_time(current_tick_time)  # Get times for next frame
    logger.debug("Sleeping for %s (%s%%)", delta, round(delta * 1000, 2))
    time.sleep(delta)

    # TTL stuff is in place to let us unit test this function, which we can't do if it runs forever
    if ttl is None:
        new_ttl = ttl
    else:
        new_ttl = ttl - 1
    if ttl == 0:
        continue_ = False
    else:
        continue_ = True

    return continue_, (new_worldstate, next_tick_time, new_ttl)
