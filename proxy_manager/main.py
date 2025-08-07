import config

class Proxy:
    def __init__(self, mode=None, host=None, port=None, username=None, password=None, change_ip_url=None):
        if mode is None:
            mode = config.PROXY_MODE
        if host is None:
            host = config.PROXY_HOST
        if port is None:
            port = config.PROXY_PORT
        if username is None:
            username = config.PROXY_USERNAME
        if password is None:
            password = config.PROXY_PASSWORD
        if change_ip_url is None:
            change_ip_url = config.PROXY_CHANGE_IP_URL

        self.mode = mode
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.change_ip_url = change_ip_url

    def get_data(self):
        return {            
            "mode": self.mode,
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
            "changeIpUrl": self.change_ip_url,
            "customName": "My Proxy"
        }
