"""
Helper to get the external ip.
"""

from requests import get
from ipaddress import IPv4Address
import logging

class ExternalIP:
    """
    Base class.
    Do not use this directly, instead inherit and implement!
    """

    def __init__(self):
        pass

    @property
    def ip(self) -> IPv4Address:
        """
        Implement this method as a property.
        :return:
        """
        raise NotImplementedError


class ExternalIpify:
    """
    This implementation uses the https://www.ipify.org/ API.
    """

    API_URL = "https://api.ipify.org"

    @property
    def ip(self) -> IPv4Address:
        r = get(self.API_URL)

        # raise if request unsuccessful
        r.raise_for_status()

        ip = IPv4Address(r.text)
        logging.debug(f"found external ip to be {ip}")
        return ip
