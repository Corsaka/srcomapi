

class APIRequestException(Exception):
    def __init__(self, message, data):
        super(APIRequestException, self).__init__(message)
        self.data = data

class APINotProvidedException(Exception):
    pass

class APIAuthenticationRequired(Exception):
    def __init__(self):
        super(APIAuthenticationRequired, self).__init__("Authentication is required for this method - check API key!\n")