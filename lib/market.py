from __future__ import division
from collections import namedtuple
from functools import partial
import math
import random
from fn import _, Stream
from fn.iters import *

from attr_update import attr_update

def pseudo_normal():
    return (Math.random()*2-1)+(Math.random()*2-1)+(Math.random()*2-1);

def rand_from_normal():
    return Math.round(rnd_snd()*stdev+mean);

# Look at ways to set default values on namedtuples from http://stackoverflow.com/questions/11351032/named-tuple-and-optional-keyword-arguments

Market = namedtuple("Market", ["bid", "ask"])
Inventory = namedtuple("Inventory", ["wood", "food", "ore", "metal", "tools", "dollars"])
Inventory.__new__ = partial(Inventory.__new__, wood=10, food=10, ore=10, metal=10, tools=10, dollars=0)

ResourceDelta = namedtuple("ResourceDelta", ["wood", "food", "ore", "metal", "tools", "dollars"])
ResourceDelta.__new__ = partial(ResourceDelta.__new__, wood=0, food=0, ore=0, metal=0, tools=0, dollars=0)

#Bid = namedtuple("Bid", ["npc", "resource", "price"])
#Ask = namedtuple("Ask", ["npc", "resource", "price"])
Trade = namedtuple("Trade", ["resource", "price", "type", "status"])
Trade.__new__ = partial(Trade.__new__, status=None)

def has_wood(obj):
    return obj.wood > 0
def has_food(obj):
    return obj.food > 0
def has_ore(obj):
    return obj.ore > 0
def has_metal(obj):
    return obj.metal > 0
def has_tools(obj):
    return obj.tools > 0

BeliefIntervals = namedtuple("BeliefIntervals", ["wood", "food", "ore", "metal", "tools"])
BeliefIntervals.__new__ = partial(BeliefIntervals.__new__, wood=None, food=None, ore=None, metal=None, tools=None)

NPC = namedtuple("NPC", ["occupation", "inventory", "belief_intervals"])
NPC.__new__ = partial(
    NPC.__new__,
    occupation=None,
    inventory=Inventory(),
    belief_intervals=BeliefIntervals(),
)

trade_history = ()

def miner_produce(npc):
    inventory = npc.inventory
    if has_food(inventory): 
        if has_tools(inventory):
            delta = dict(food=inventory.food-1, ore=inventory.ore+4)
        else:
            delta = dict(food=inventory.food-1, ore=inventory.ore+2)
    else:
        delta = {}
    return attr_update(npc, "inventory", **delta)
        
def farmer_produce(npc):
    inventory = npc.inventory
    if has_wood(inventory): 
        if has_tools(inventory):
            delta = dict(wood=inventory.wood-1, food=inventory.food+4)
        else:
            delta = dict(wood=inventory.wood-1, food=inventory.food+2)
    else:
        delta = {}
    return attr_update(npc, "inventory", **delta)

def lumberjack_produce(npc):
    inventory = npc.inventory
    if has_food(inventory): 
        if has_tools(inventory):
            delta = dict(food=inventory.food-1, wood=inventory.wood+2)
        else:
            delta = dict(food=inventory.food-1, wood=inventory.wood+1)
    else:
        delta = {}
    return attr_update(npc, "inventory", **delta)

def refiner_produce(npc):
    inventory = npc.inventory
    if has_food(inventory):
        if has_tools(inventory):
            delta = dict(ore=0, food=inventory.food-1, metal=inventory.metal+1)
        elif inventory.ore >= 2:
            delta = dict(ore=inventory.ore-2, food=inventory.food-1, metal=inventory.metal+1)
    else:
        delta = {}
    return attr_update(npc, "inventory", **delta)


def get_work_fn(npc):
    occupation_work = dict(
        farmer=farmer_produce,
        lumberjack=lumberjack_produce,
        miner=miner_produce,
        refiner=refiner_produce,
    )
    return occupation_work[npc.occupation]

def do_work(npc):
    return get_work_fn(npc)(npc)

def avg_price(resource):
    '''Histories are lists of lists of Trade items'''
    if len(trade_history) == 0:
        raise RuntimeError("Need trades to estimate the history of")

    def avg(nums):
        """Averages an interable"""
        totals = reduce(lambda x, y: (x[0]+y, x[1]+1), nums, (0,0))
        assert totals[1] != 0
        return totals[0]/totals[1]

    filter_nonzero = lambda t: len(t) > 0
    filter_relevant = lambda trades: tuple(trade for trade in trades if trade.status == "accepted" and trade.resource == resource)

    n = 8
    trades = filter(
        filter_nonzero,
        map(filter_relevant, takelast(n, trade_history))
    )
    averages = map(lambda tuple_: avg(t.price for t in tuple_), trades)
    return avg(averages)

def estimate_market_price(resource):
    return avg_price(trade_history, resource)

def estimate_npc_price(resource, intervals):
    interval = getattr(intervals, resource)
    return random.randint(interval[0], interval[1])

def calc_midpoint(x, y):
    return (x+y)/2

def translate_interval(interval, mean):
    """Translates an interval towards the mean"""
    midpoint = calc_midpoint(*interval)
    increment = (mean - midpoint) * .05
    interval = (interval[0]+increment, interval[1]+increment)
    return interval

def shrink_interval(interval):
    return (interval[0]+(interval[0]*.05), interval[1]-(interval[1]*.05))

def expand_interval(interval):
    return (interval[0]-(interval[0]*.05), interval[1]+(interval[1]*.05))

def update_beliefs(npc, trade):
    fn = update_beliefs_accepted if trade.status == "accepted" else update_beliefs_rejected
    return fn(npc, trade)

def interval_is_divergent(interval, price, mean):
    if not (.66 < (price/mean) < 1.33):
        return translate_interval(interval, mean)
    else:
        return interval

def update_beliefs_accepted(npc, trade):
    mean = avg_price(trade.resource)
    f = F() >> F(interval_is_divergent, price=trade.price, mean=mean) >> shrink_interval

    interval = f(getattr(npc.belief_intervals, trade.resource))

    return attr_update(npc, "belief_intervals", **{trade.resource: interval})

def update_beliefs_rejected(npc, trade):
    mean = avg_price(trade.resource)
    interval = getattr(npc.belief_intervals, trade.resource)
    interval = translate_interval(interval, mean)
    interval = expand_interval(interval)

    npc = attr_update(npc, "belief_intervals", **{trade.resource: interval})
    return npc


def get_sell_resource(occupation):
    return dict(
        farmer="food",
        lumberjack="wood",
        miner="ore",
        refiner="metal",
    )[occupation]


def get_buy_resources(occupation):
    return dict(
        farmer = ["wood", "tools"],
        lumberjack = ["food", "tools"],
        miner = ["food", "tools"],
        refiner = ["food", "ore", "tools"],
        blacksmith = ["metal"],
    )[occupation]


def calc_amt_to_trade(favorability, inventory):
    return math.floor(favorability * inventory)


def calc_favorability(interval, mean):
    """Range of 0-1. Low number means our belief range is above the market average, high means we're below."""
    return min(1, max(0, mean-interval[0])/(interval[1]-interval[0]))


def create_ask(npc, resource):
    price = estimate_npc_price(resource, npc.belief_intervals)
    num_to_sell = max(limit, ideal)


def determine_trade_quantity(npc, resource_fn, fav_fn):
    resource = resource_fn(npc.occupation)
    mean = avg_price(resource)
    favorability = fav_fn(getattr(npc.belief_intervals, resource), mean)
    amt_to_trade = calc_amt_to_trade(favorability, getattr(npc.inventory, resource))
    return amt_to_trade


def determine_sale_quantity(npc):
    return determine_trade_quantity(
        npc,
        resource_fn=get_sell_resource,
        fav_fn=calc_favorability  # Low -> we believe something is worth more than the market does now. High -> the market thinks it's worth what we do, sell sell sell!
    )


def determine_purchase_quantity(npc):
    def determine_which_to_buy(resources):  # TODO: Do something more useful here
        return sorted(resources, key=lambda resource: getattr(npc.inventory, resource))[0]

    return determine_trade_quantity(
        npc,
        resource_fn=lambda occupation: determine_which_to_buy(get_buy_resources(occupation)),
        fav_fn=lambda *args, **kwargs: 1-calc_favorability(*args, **kwargs)  # This means we're measuring how far below our belief the market average is. Buy when we belief something is cheap.
    )
