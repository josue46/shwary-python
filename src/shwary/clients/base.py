class BaseClient:
    """Base client class to reduce duplication between sync and async clients."""

    def __init__(self):
        pass

    def request(self, method, endpoint, **kwargs):
        """Make a request to the given endpoint."""  
        # Implementation would go here
        pass

    def handle_response(self, response):
        """Handle the response from the request."""  
        # Implementation would go here
        pass
