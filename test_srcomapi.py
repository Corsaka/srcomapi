import srcomapi

def setup_api():
    return srcomapi.SpeedrunCom(mock=True,debug=0)

def test_search_for_game():
    api = setup_api()
    game = api.search(srcomapi.datatypes.Game, {"name": "super mario sunshine"})[0]
    assert game.name == "Super Mario Sunshine"

def test_world_record():
    api = setup_api()
    game = srcomapi.datatypes.Game(api, id="v1pxjz68") #Super Mario Sunshine
    record = game.categories[0].records[0]
    wr = record.runs[0]
    assert isinstance(wr["run"], srcomapi.datatypes.Run)
    assert wr["place"] == 1

def test_long_record_request():
    api = setup_api()
    game_id = "nd2ee5ed" #Dead Cells
    category_id = "7kjp314k" #Any% (Early Access)
    runs = api.search(srcomapi.datatypes.Run, {"game": game_id, "category": category_id, "status": "verified", "order-by": "date", "max": 200})
    assert isinstance(runs[0], srcomapi.datatypes.Run) and len(runs) > 200

#note these are almost certainly broken until mock gets fixed, but if you toggle it to False it'll work just fine
test_search_for_game() 
test_world_record()
test_long_record_request()