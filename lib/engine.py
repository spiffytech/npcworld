from collections import namedtuple
from fn import recur
import time

from npcworld.lib.utils import logger
from npcworld.lib import ai, utils

def next_tick_time(current_tick, current_time=None):
    if current_time is None:
        t = time.time()
    else:
        t = current_time
    next_tick = max(t, current_tick + utils.frames_to_secs(1))
    delta = max(0, next_tick - t)  # Time delta to next tick. If we take < 1 frame's time to render a frame, sleep until the next frame tick. If we're taking longer than 1 frame's time to render each frame, don't sleep. 
    if delta == 0:
        logger.warn("Frame ran too long by %d secs", t - next_tick)

    return (
        next_tick,
        delta
    )

def run_game():
    grid = utils.dpc.get_or_create("grid", make_world_grid, 60*60)
    logger.info("Making graph...")
    graph = utils.dpc.get_or_create("graph", lambda: make_graph(grid), 60*60)
    logger.info("Graph made")

    Worldstate = namedtuple("Worldstate", "dots ticks grid graph")
    worldstate = Worldstate(
        dots=tuple(),
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

    events_ = ai.dot_ai(worldstate)
    if events_ is not None:
        worldstate = events.handle_events(worldstate, events_)  # TODO: New variable name, because FP

    new_worldstate = attr_update(
        worldstate,
        ticks=_+1,  # Elapsed ticks in game
    )

    next_tick_time, delta = next_tick_time(current_tick_time)  # Get times for next frame
    logger.debug("Sleeping for %s", delta)
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
