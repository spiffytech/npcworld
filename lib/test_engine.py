from __future__ import division
import time

from npcworld.lib import engine, utils

def test_next_tick_time_on_schedule():
    # Best case - 0 delay between current tick and current time
    current_tt = time.time()
    ntt, delta = engine.calc_next_tick_time(current_tt, current_time=current_tt)
    assert ntt == current_tt + utils.frames_to_secs(1)
    assert round(delta, 5) == utils.frames_to_secs(1)


    # Test what happens if we actually do some work during a frame
    ntt, delta = engine.calc_next_tick_time(current_tt, current_time=(current_tt + utils.frames_to_secs(1)/2))
    assert ntt == current_tt + utils.frames_to_secs(1)
    assert round(delta, 5) == utils.frames_to_secs(1)/2

def test_next_tick_time_behind_schedule():
    current_time = time.time()
    current_tick = current_time - utils.frames_to_secs(4)
    ntt, delta = engine.calc_next_tick_time(current_tick, current_time=current_time)
    assert round(ntt, 5) == round(current_time, 5)
    assert delta == 0
