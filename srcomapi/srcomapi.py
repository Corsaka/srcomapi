import requests
import inspect
import warnings
from http.client import responses
from os.path import dirname

import srcomapi
import srcomapi.datatypes as DataType
from .exceptions import APIRequestException

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
        self._datatypes = {v.endpoint:v for k,v in inspect.getmembers(DataType, inspect.isclass) if hasattr(v, "endpoint")}
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

    def get_games(self, **kwargs):
        """This function is deprecated. Use search(DataType.Game) instead."""
        warnings.warn("This function is deprecated. Use search(DataType.Game) instead.",DeprecationWarning)
        return self.search(DataType.Game, **kwargs)

    def get_game(self, id):
        """Simple abstraction to get an individual game.

        :param id: Game ID in the API. Name will work but will redirect.
        :return: `DataType<Game>` object.
        :rtype: srcomapi.DataType.Game"""
        return DataType.Game(self, data=self.get("games/" + id))

    def get_user(self, id):
        """Simple abstraction to get an individual user.

        :param id: User ID in the API.
        :return: `DataType<User>` object.
        :rtype: srcomapi.DataType.User"""
        return DataType.User(self, data=self.get("users/" + id))

    def get_series(self, id):
        """Simple abstraction to get an individual series.

        :param id: Series ID in the API.
        :return: `DataType<Series>` object.
        :rtype: srcomapi.DataType.Series"""
        return DataType.Series(self, data=self.get("series/" + id))

    def get_run(self, id):
        """Simple abstraction to get an individual run.

        :param id: Run ID in the API.
        :return: `DataType<Run>` object.
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