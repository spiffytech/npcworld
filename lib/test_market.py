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
    npc = market.NPC()
    updated_npc = market.lumberjack_produce(npc)
    assert updated_npc.inventory.wood == npc.inventory.wood+4
    assert updated_npc.inventory.food == npc.inventory.food-1

def test_farmer_produce():
    npc = market.NPC()
    updated_npc = market.farmer_produce(npc)
    assert updated_npc.inventory.food == npc.inventory.food+4
    assert updated_npc.inventory.wood == npc.inventory.wood-1

def test_miner_produce():
    npc = market.NPC()
    updated_npc = market.miner_produce(npc)
    assert updated_npc.inventory.ore == npc.inventory.ore+4
    assert updated_npc.inventory.food == npc.inventory.food-1
