import requests
import inspect
import warnings
from http.client import responses
from os.path import dirname

import srcomapi
import srcomapi.datatypes as DataType
from .exceptions import APIRequestException,APIAuthenticationRequired

# libraries for mocking
import json
import gzip

with open(dirname(srcomapi.__file__) + "/.version") as f:
    __version__ = f.read().strip()
API_URL = "https://www.speedrun.com/api/v1/"
TEST_DATA = dirname(srcomapi.__file__) + "/test_data/"

class SpeedrunCom(object):
    """The class of the API connection.

    Instantiate with `SpeedrunCom(api_key,user_agent,mock,debug)`.
    None are required - default values are listed as part of members below.

    Members:
     api_key: str = None
      A user's API key obtained from `https://www.speedrun.com/api/auth`.
     user_agent: str = "corsaka:srcomapi/<version>"
      The User Agent reported to the website. SRCom recommends the format `name/version`, e.g `my-bot/4.2`.
     mock: bool = False
      Whether to use test_data (True) or to query the actual API (False).
     debug: int = 0
      If >=1, prints target URI when getting information from the website.
      If >=2, prints the attribute's name whenever accessing one.

    Functions:
     get(endpoint, **kwargs) -> data: Query an endpoint of the API with custom data.
     search(datatype:DataType, params:dict[str,Any]) -> data: Readable version of get, by datatype.
     get_game(id:str) -> data: Quick form of get for games, by SRCom ID.
     get_user(id:str) -> data: Quick form of get for users, by SRCom ID.
     get_series(id:str) -> data: Quick form of get for series, by SRCom ID.
     get_run(id:str) -> data: Quick form of get for runs, by SRCom ID.
    """
    def __init__(self, api_key=None, user_agent="corsaka:srcomapi/"+__version__, mock=False, debug=0):
        self._datatypes = {v.endpoint:v for _,v in inspect.getmembers(DataType, inspect.isclass) if hasattr(v, "endpoint")}
        self.api_key = api_key
        self.user_agent = user_agent
        self.mock = mock
        self.debug = debug

    def get(self, endpoint, **kwargs):
        """Request data from a specific endpoint of the API.
        
        :param endpoint: The targeted endpoint.
        :param **kwargs: Optional arguments for the GET HTTP request.
        :return: JSON response data from the API.
        :rtype: dict"""
        headers = {"User-Agent": self.user_agent}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        kwargs.update({"headers": headers})
        uri = API_URL + endpoint
        if self.debug >= 1: print("GET "+uri)
        if self.mock:
            mock_endpoint = ".".join(endpoint.split("/")[0::2])
            try:
                with gzip.open(TEST_DATA + mock_endpoint + ".json.gz") as f:
                    data = json.loads(f.read().decode("utf-8"))["data"]
            except FileNotFoundError:
                response = requests.get(uri, **kwargs)
                if response.status_code != 404:
                    with gzip.open(TEST_DATA + mock_endpoint + ".json.gz", "wb") as f:
                        """SRC allows up to 200 entries max per request 
                        so we're making requests until we get all entries
                        https://github.com/speedruncomorg/api/blob/master/version1/pagination.md
                        """
                        json_to_write = response.json()
                        data = response.json()["data"]
                        try:
                            response_size = response.json()['pagination']['size']
                            response_max_size = response.json()['pagination']['max']
                            while response_size == response_max_size: #if request size is the maximum allowed we haven't reached the end of entries
                                uri = response.json()['pagination']['links'][-1]["uri"] #SRC gives us the link to use for next request
                                response = requests.get(uri)
                                response_size = response.json()['pagination']['size']
                                response_max_size = response.json()['pagination']['max']
                                data.extend(response.json()["data"])
                        except KeyError:
                            pass
                        json_to_write['data'] = data
                        f.write(json.dumps(json_to_write).encode("utf-8"))
                else:
                    raise APIRequestException((response.status_code, responses[response.status_code], uri[len(API_URL):]), response)
        else:
            response = requests.get(uri, **kwargs)
            if response.status_code >= 400:
                raise APIRequestException((response.status_code, responses[response.status_code], uri[len(API_URL):]), response)
            data = response.json()["data"]
            try:
                response_size = response.json()['pagination']['size']
                response_max_size = response.json()['pagination']['max']
                while response_size == response_max_size: 
                    uri = response.json()['pagination']['links'][-1]["uri"] 
                    response = requests.get(uri)
                    response_size = response.json()['pagination']['size']
                    response_max_size = response.json()['pagination']['max']
                    data.extend(response.json()["data"])
            except KeyError:
                pass
        return data

    def post(self, endpoint, data, **kwargs):
        if self.mock: print("does nothing"); return #TODO: implement
        if not self.api_key:
            raise APIAuthenticationRequired()
        kwargs.update({"headers": {"User-Agent":self.user_agent, "X-API-Key":self.api_key}})
        uri = API_URL + endpoint
        if self.debug >= 1: print("POST "+uri)
        response = requests.post(uri, json=data, **kwargs)
        if response.status_code == 400:
            print(response.json()["message"])
            for error in response.json()["errors"]:
                print(error)

        if response.status_code >= 400:
            raise APIRequestException((response.status_code, responses[response.status_code], uri[len(API_URL):]), response)
        
        return response.json()["data"]

    def put(self, endpoint, data, **kwargs):
        if self.mock: print("does nothing"); return #TODO: implement
        if not self.api_key:
            raise APIAuthenticationRequired()
        kwargs.update({"headers": {"User-Agent":self.user_agent, "X-API-Key":self.api_key}})
        uri = API_URL + endpoint
        if self.debug >= 1: print("PUT "+uri)
        response = requests.put(uri, json=data, **kwargs)
        if response.status_code == 400:
            print(response.json()["message"])
            for error in response.json()["errors"]:
                print(error)

        if response.status_code >= 400:
            raise APIRequestException((response.status_code, responses[response.status_code], uri[len(API_URL):]), response)
        
        return response.json()["data"]

    def delete(self, endpoint, data, **kwargs):
        if self.mock: print("does nothing"); return #TODO: implement
        if not self.api_key:
            raise APIAuthenticationRequired()
        kwargs.update({"headers": {"User-Agent":self.user_agent, "X-API-Key":self.api_key}})
        uri = API_URL + endpoint
        if self.debug >= 1: print("DELETE "+uri)
        response = requests.delete(uri, json=data, **kwargs)
        if response.status_code == 400:
            print(response.json()["message"])
            for error in response.json()["errors"]:
                print(error)

        if response.status_code >= 400:
            raise APIRequestException((response.status_code, responses[response.status_code], uri[len(API_URL):]), response)
        
        return response.json()["data"]

    def get_games(self, **kwargs):
        """This function is deprecated. Use search(DataType.Game) instead."""
        warnings.warn("This function is deprecated. Use search(DataType.Game) instead.",DeprecationWarning)
        return self.search(DataType.Game, **kwargs)

    def get_game(self, id):
        """Simple abstraction to get an individual game.

        :param id: Game ID in the API. Name will work but will redirect.
        :return: A `Game` object.
        :rtype: srcomapi.DataType.Game"""
        return DataType.Game(self, data=self.get("games/" + id))

    def get_user(self, id):
        """Simple abstraction to get an individual user.

        :param id: User ID in the API.
        :return: A `User` object.
        :rtype: srcomapi.DataType.User"""
        return DataType.User(self, data=self.get("users/" + id))

    def get_series(self, id):
        """Simple abstraction to get an individual series.

        :param id: Series ID in the API.
        :return: A `Series` object.
        :rtype: srcomapi.DataType.Series"""
        return DataType.Series(self, data=self.get("series/" + id))

    def get_run(self, id):
        """Simple abstraction to get an individual run.

        :param id: Run ID in the API.
        :return: A `Run` object.
        :rtype: srcomapi.DataType.Run"""
        return DataType.Run(self, data=self.get("runs/" + id))

    def search(self, datatype, params):
        """Returns a generator that uses the given datatype and search params to get results
        
        :param datatype: `DataType` object to search.
        :param params: Parameters to search with.
        :return: JSON response data from the website.
        :rtype: dict"""
        response = self.get(datatype.endpoint, params=params)
        return [datatype(self, data=data) for data in response]

    def submit_run(self, category=..., platform=..., times=..., level=None, date=None, region=None, players=None, video=None, comment=None, splitsio=None, variables=None, verified=False, emulated=False):
        """Submit a run to the website. Requires a user's API key!

        The [API Reference](https://github.com/speedruncomorg/api/blob/master/version1/runs.md#post-runs) is a handy guide.

        :param category: The category ID to submit to.
        :param platform: The platform ID used in the run.
        :param times: A `dict[str,float]` or `dict[str,int]` of recorded times for the run.
        :param level: (optional) The level ID to submit to (if the category is per-level).
        :param date: (optional) The date the run was performed, in YYYY-MM-DD format. Defaults to today.
        :param region: (optional) The region ID of the game.
        :param players: (optional) A `list[dict[str,str]]` or `list[User]` of players in the run. Defaults to the API key's user.
        :param video: (optional) The video link.
        :param comment: (optional) The description of the run. Up to 2000 characters.
        :param splitsio: (optional) The run's splitsio ID.
        :param variables: (optional) A `dict[str,dict[str,str]]` of variables associated with the run. Complex formatting - look at API reference.
        :param verified: (optional) Whether the run is verified with submission. Requires a moderator's API key if `True`. Defaults to `False`.
        :param emulated: (optional) Whether the run is emulated or not. Defaults to `False`.
        :return: A `Run` object of the submitted run.
        :rtype: srcomapi.DataType.Run"""

        arguments = locals() #gets all arguments that have values into a local dictionary
        del arguments["self"] #remove the api link from the dictionary

        runData = {}

        if category is Ellipsis:
            raise AttributeError("Category field is mandatory!",name="NoCategory")
        
        if times is Ellipsis:
            raise AttributeError("Times field is mandatory!",name="NoTimes")

        if platform is Ellipsis:
            raise AttributeError("Platform field is mandatory!",name="NoPlatform")

        assert type(times) is dict,"Times field is not a dictionary"
        for k,v in times.items():
            assert type(k) is str,"Non-string value in times dictionary"
            if not (k == "realtime" or k == "realtime_noloads" or k == "ingame"):
                raise AttributeError("Timer dictionary contains invalid timer type '{}'! Valid types: 'realtime', 'realtime_noloads', 'ingame'".format(k),name="InvalidTimerType")
            
            if not (type(v) is float or type(v) is int):
                raise AttributeError("Timer dictionary contains non-numerical value '{}' in '{}'!".format(v,k),name="InvalidTimerValue")
        runData["times"] = times

        if players:
            assert type(players) is list,"players var is not list"
            for player in players:
                if type(player) is DataType.User:
                    player = {"rel":"user","id":player.id}
                assert type(player) is dict,"Invalid datatype in player list"
                for k,v in player.items():
                    assert type(k) is str,"Non-string key in player dictionary"
                    assert type(v) is str,"Non-string value in player dictionary"
                    if k == "rel":
                        if not (v == "user" or v == "guest"):
                            raise AttributeError("Player list contains invalid player type '{}'! Valid types: 'user', 'guest'".format(v),name="InvalidPlayerType")
                    elif k == "id":
                        if not isinstance(self.get_user(v),DataType.User):
                            raise AttributeError("Player ID {} is not valid!".format(v),name="NoPlayerFound")
                    elif k == "name":
                        continue
                    else:
                        raise AttributeError("Player list contains a player with an invalid key '{}'! Valid keys: 'rel', 'id', 'name'".format(k),name="InvalidPlayersDictionaryKey")
            runData["players"] = players

        if variables:
            assert type(variables) is dict,"variables var is not dict"
            for variable,valueDict in variables.items():
                assert type(variable) is str,"Non-string key in variable dictionary"
                assert type(valueDict) is dict,"Variable value is not dictionary"
                for key,val in valueDict.items():
                    assert type(key) is str,"Non-string key in variable value dictionary"
                    assert type(val) is str,"Non-string value in variable value dictionary"
                    if key == "type":
                        if not (val == "pre-defined" or val == "user-defined"):
                            raise AttributeError("Variable value dictionary contains invalid value type '{}'! Valid types: 'pre-defined', 'user-defined'".format(val),name="InvalidVariableValueType")
                    elif key == "value":
                        continue
                    else:
                        raise AttributeError("Variable value dictionary contains a value with invalid key '{}'! Valid keys: 'type', 'value'".format(key),name="InvalidVariableValueKey")
            runData["variables"] = variables

        for key,value in arguments.items():
            if value is not None:
                if key == "verified" or key == "emulated":
                    assert type(value) is bool,"Non-bool value in bool variable "+value
                elif key == "times" or key == "players" or key == "variables":
                    continue #we've already done these
                else:
                    assert type(value) is str,"Non-string value in string variable "+value
                runData[key] = value

        return DataType.Run(self, data=self.post("runs",{"run":runData}))

    def update_run_status(self,runId,status,reason=None):
        """Update a run's status. Requires a moderator's API key!
        
        :param runId: The API ID of the run.
        :param status: The new status of the run.
        :param reason: (optional) The reason associated with the status.
        :return: A `Run` object of the updated run.
        :rtype: srcomapi.DataType.Run"""

        if not status == ("rejected","verified","new"):
            raise AttributeError("Invalid status '{}'! Valid statuses: 'rejected', 'verified', 'new'")
        data = {"status":{"status":status}}
        if reason:
            assert status == "rejected","Reason was provided but status is not 'rejected'!"
            assert type(reason) is str,"reason var is not string"
            data["status"]["reason"] = reason

        return DataType.Run(self, data=self.put("runs/{}/status".format(runId),data))

    def update_run_players(self,runId,players):
        """Update your run's players. Requires an API key!  
        Has known bugs documented [here](https://github.com/speedruncomorg/api/issues/87).
        
        :param runId: The API ID of the run.
        :param players: A list of users in the run. Can be a list of `User` objects or a dictionary in SRC's format.
        :return: A `Run` object of the updated run.
        :rtype: srcomapi.Datatype.Run"""

        assert type(players) is list,"players var is not list"
        for player in players:
            if type(player) is DataType.User:
                player = {"rel":"user","id":player.id}
            assert type(player) is dict,"Invalid datatype in player list"
            for k,v in player.items():
                assert type(k) is str,"Non-string key in player dictionary"
                assert type(v) is str,"Non-string value in player dictionary"
                if k == "rel":
                    if not (v == "user" or v == "guest"):
                        raise AttributeError("Player list contains invalid player type '{}'! Valid types: 'user', 'guest'".format(v),name="InvalidPlayerType")
                elif k == "id":
                    if not isinstance(self.get_user(v),DataType.User):
                        raise AttributeError("Player ID {} is not valid!".format(v),name="NoPlayerFound")
                elif k == "name":
                    continue
                else:
                    raise AttributeError("Player list contains a player with an invalid key '{}'! Valid keys: 'rel', 'id', 'name'".format(k),name="InvalidPlayersDictionaryKey")

        return self.put("runs/{}/players".format(runId),{"players":players})

    def delete_run(self,runId):
        """Deletes a run. Requires an API key!
        
        :param runId: The API ID of the run.
        :return: A `Run` object of the deleted run.
        :rtype: srcomapi.Datatype.Run"""
        return DataType.Run(self, data=self.delete("runs/"+runId))