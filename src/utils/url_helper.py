
class URLHelper:
    def __init__(self, url_string):
        self.href = url_string
        if "?" in url_string:
            base_url, query_string = url_string.split("?", 1)
        else:
            base_url, query_string = url_string, ""

        if "://" in base_url:
            protocol_and_host, path = base_url.split("://", 1)
            if "/" in path:
                host, self.pathname = path.split("/", 1)
                self.pathname = "/" + self.pathname
            else:
                self.pathname = "/"
        else:
            self.pathname = "/"

        # Parse query parameters
        self.searchParams = {}
        if query_string:
            for param in query_string.split("&"):
                if "=" in param:
                    key, value = param.split("=", 1)
                    self.searchParams[key] = value
                else:
                    self.searchParams[param] = ""