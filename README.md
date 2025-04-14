srcomapi (SpeedrunComAPI) ![travis-ci](https://travis-ci.org/corsaka/srcomapi.svg?branch=master)
=========================

A Python3 implementation of version 1 of the speedrun.com REST API. (not `pip install srcomapi` yet. working on it)

For the undocumented/experimental version 2 of the speedrun.com REST API, check out [ManicJamie/speedruncompy](https://github.com/ManicJamie/speedruncompy).

Does not support Python 2. 2.7 hit EOL in 2020. C'mon.

Usage
=====

Documentation of the API itself is available at [speedruncomorg/api](https://github.com/speedruncomorg/api/), and should be referenced heavily.

The `mock` function of this script is broken because search() returns a list where get() doesn't.
It might work, but if you get a TypeError due to string slicing, assume it's mock's fault, not your code.

Start
-----

```python
>>> import srcomapi, srcomapi.datatypes as DataType
>>> api = srcomapi.SpeedrunCom(); api.debug = 1
```

Searching for a game
--------------------

```python
# It's recommended to cache the game ID and use it for future requests.
# Data is cached for the current session by classname/id so future
# requests for the same game are instantaneous.
>>> api.search(DataType.Game, {"name": "super mario sunshine"})
[<Game "Super Mario Sunshine">, ...]
>>> game = _[0]
```

Getting the current world record for a game category
----------------------------------------------------

Properties are accessed as if they were attributes.

```python
>>> game.categories
[<Category "Any%">, ...]
>>> _[0].records[0].runs
[{'place': 1, 'run': <Run v1pxjz68/n2y3r8do/zq2qnwrz 985>}, ...]
>>> _[0]["run"].times
{'primary_t': 985, ...}
# primary_t is the time in seconds
```

Getting a dict containing all runs from a game
----------------------------------------------

```python
sms_runs = {}
for category in game.categories:
  if not category.name in sms_runs:
    sms_runs[category.name] = {}
  if category.type == 'per-level':
    for level in game.levels:
      sms_runs[category.name][level.name] = DataType.Leaderboard(api, data=api.get("leaderboards/{}/level/{}/{}?embed=variables".format(game.id, level.id, category.id)))
  else:
    sms_runs[category.name] = DataType.Leaderboard(api, data=api.get("leaderboards/{}/category/{}?embed=variables".format(game.id, category.id)))
# {'Any%': <Leaderboard v1pxjz68/n2y3r8do>, '120 Shines': <Leaderboard v1pxjz68/z27o9gd0>, ...}
```

Embeds will be automatically converted to DataTypes for ease of use when they're included in the parameters for the original GET (`?embed=variables`).