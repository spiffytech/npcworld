import market

def test_default_inventory():
    default_amount = 10
    inventory = market.Inventory()
    assert inventory.wood == default_amount
    assert inventory.food == default_amount
    assert inventory.ore == default_amount
    assert inventory.metal == default_amount
    assert inventory.tools == default_amount

def test_has_wood():
    inventory = market.Inventory(wood=1)
    assert market.has_wood(inventory)

    inventory = market.Inventory(wood=0)
    assert not market.has_wood(inventory)

def test_has_ore():
    inventory = market.Inventory(ore=1)
    assert market.has_ore(inventory)

    inventory = market.Inventory(ore=0)
    assert not market.has_ore(inventory)

def test_has_food():
    inventory = market.Inventory(food=1)
    assert market.has_food(inventory)

    inventory = market.Inventory(food=0)
    assert not market.has_food(inventory)

def test_has_metal():
    inventory = market.Inventory(metal=1)
    assert market.has_metal(inventory)

    inventory = market.Inventory(metal=0)
    assert not market.has_metal(inventory)

def test_has_tools():
    inventory = market.Inventory(tools=1)
    assert market.has_tools(inventory)

    inventory = market.Inventory(tools=0)
    assert not market.has_tools(inventory)

def test_default_npc():
    npc = market.NPC()
    assert npc.inventory == market.Inventory()
    assert npc.occupation is None

def test_lumberjack_produce():
    lumberjack = market.NPC(occupation="lumberjack")
    npc = lumberjack._replace(inventory=market.Inventory(tools=0, food=0))
    updated_npc = market.lumberjack_produce(npc)
    assert updated_npc.inventory == npc.inventory

    npc = lumberjack
    updated_npc = market.lumberjack_produce(npc)
    assert updated_npc.inventory.wood == npc.inventory.wood+2
    assert updated_npc.inventory.food == npc.inventory.food-1

    npc = lumberjack._replace(inventory=market.Inventory(tools=0))
    updated_npc = market.lumberjack_produce(npc)
    assert updated_npc.inventory.wood == npc.inventory.wood+1
    assert updated_npc.inventory.food == npc.inventory.food-1

def test_farmer_produce():
    farmer = market.NPC(occupation="farmer")
    npc = farmer._replace(inventory=market.Inventory(tools=0, wood=0))
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory == npc.inventory

    npc = farmer
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory.food == npc.inventory.food+4
    assert updated_npc.inventory.wood == npc.inventory.wood-1

    npc = farmer._replace(inventory=market.Inventory(tools=0))
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory.food == npc.inventory.food+2
    assert updated_npc.inventory.wood == npc.inventory.wood-1

def test_miner_produce():
    miner = market.NPC(occupation="miner")
    npc = miner._replace(inventory=market.Inventory(tools=0, food=0))
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory == npc.inventory

    npc = miner
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory.ore == npc.inventory.ore+4
    assert updated_npc.inventory.food == npc.inventory.food-1

    npc = miner._replace(inventory=market.Inventory(tools=0))
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory.ore == npc.inventory.ore+2
    assert updated_npc.inventory.food == npc.inventory.food-1

def test_refiner_produce():
    refiner = market.NPC(occupation="refiner")
    npc = refiner._replace(inventory=market.Inventory(tools=0, food=0))
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory == npc.inventory

    npc = refiner
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory.metal == npc.inventory.metal+1
    assert updated_npc.inventory.ore == 0
    assert updated_npc.inventory.food == npc.inventory.food-1

    npc = refiner._replace(inventory=market.Inventory(tools=0))
    updated_npc = market.do_work(npc)
    assert updated_npc.inventory.metal == npc.inventory.metal+1
    assert updated_npc.inventory.ore == npc.inventory.ore-2
    assert updated_npc.inventory.food == npc.inventory.food-1

class TestTrades(object):
    def test_avg_price(self):
        trade_history = tuple(market.Trade(resource=t[0], price=t[1], type="buy") for t in (
            ("wood", 20),
            ("wood", 30),
            ("wood", 35),
            ("wood", 33),
            ("wood", 29),
            ("wood", 20),
            # Things that aren't wood, to ensure filtering for the resource in question works right
            ("food", 90),
            ("food", 70),
        ))
        assert round(market.avg_price("wood", trade_history), 2) == 27.83


    def estimate_npc_price(self):
        lower = 2
        upper = 20
        intervals = market.Intervals(wood=(lower, upper))
        assert lower <= market.estimate_npc_price("wood", intervals) <= upper

    def test_translate_interval(self):
        mean = 50
        interval = (25, 75)
        new_interval = market.translate_interval(interval, mean)
        assert new_interval == interval

        mean = 150
        interval = (40, 60)
        new_interval = market.translate_interval(interval, mean)
        assert new_interval == (45, 65)

    def test_shrink_interval(self):
        assert market.shrink_interval((100, 1000)) == (105, 950)

    def test_expand_interval(self):
        assert market.expand_interval((100, 1000)) == (95, 1050)

    def test_update_beliefs_accepted(self):
        interval=(40, 60)
        mean = 150
        translated_shrunken = market.shrink_interval(market.translate_interval(interval, mean))
        shrunken = market.shrink_interval(interval)

        trade = market.Trade(resource="wood", price=150, type="buy")
        npc = market.NPC(trade_history=(
            market.Trade(resource="wood", price=140, type="buy"),
            market.Trade(resource="wood", price=160, type="buy")
        ), belief_intervals=market.BeliefIntervals(wood=interval))
        new_npc = market.update_beliefs_accepted(npc, trade)
        assert new_npc.belief_intervals.wood == shrunken  # No interval translation

        # Test lower bounds
        trade = market.Trade(resource="wood", price=99, type="buy")
        new_npc = market.update_beliefs_accepted(npc, trade)
        assert new_npc.belief_intervals.wood == translated_shrunken  # Interval translation
        trade = market.Trade(resource="wood", price=100, type="buy")
        new_npc = market.update_beliefs_accepted(npc, trade)
        assert new_npc.belief_intervals.wood == shrunken

        # Test upper bounds
        trade = market.Trade(resource="wood", price=199, type="buy")
        new_npc = market.update_beliefs_accepted(npc, trade)
        assert new_npc.belief_intervals.wood == shrunken  # Interval translation
        trade = market.Trade(resource="wood", price=200, type="buy")
        new_npc = market.update_beliefs_accepted(npc, trade)
        assert new_npc.belief_intervals.wood == translated_shrunken

    def test_update_beliefs_rejected(self):
        interval=(40, 60)
        trade = market.Trade(resource="wood", price=50, type="buy")
        npc = market.NPC(trade_history=(
            market.Trade(resource="wood", price=140, type="buy"),
            market.Trade(resource="wood", price=160, type="buy")
        ), belief_intervals=market.BeliefIntervals(wood=interval))
        new_npc = market.update_beliefs_rejected(npc, trade)
        assert new_npc.belief_intervals.wood == market.expand_interval((45, 65))
