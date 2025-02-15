import srcomapi

def setup_api():
    return srcomapi.SpeedrunCom(mock=True,debug=3)

def test_search_for_game():
    api = setup_api()
    game = api.search(srcomapi.datatypes.Game, {"name": "super mario sunshine"})[0]
    assert game.name == "Super Mario Sunshine"

def test_world_record():
    api = setup_api()
    game = srcomapi.datatypes.Game(api, id="v1pxjz68") #Super Mario Sunshine
    record = game.categories[0].records[0]
    assert isinstance(record.runs[0]["run"], srcomapi.datatypes.Run)

def test_long_record_request():
    api = setup_api()
    game_id = "nd2ee5ed" #Dead Cells
    category_id = "7kjp314k" #Any% (Early Access)
    runs = api.search(srcomapi.datatypes.Run, {"game": game_id, "category": category_id, "status": "verified", "order-by": "date", "max": 200})
    assert isinstance(runs[0], srcomapi.datatypes.Run) and len(runs) > 200