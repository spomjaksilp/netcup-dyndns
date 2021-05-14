"""
Helper to get the external ip.
"""

from ipaddress import IPv4Address, AddressValueError
from requests.exceptions import ConnectionError
from fritzconnection.lib.fritzstatus import FritzStatus

import logging

from requests import get


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


class ExternalIpify(ExternalIP):
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


class ExternalFritzbox(ExternalIP):
    """
    This implementation uses the FRITZ!Box API (TR-064 protocol over UPnP).
    """
    fritzbox_ip = ""

    def __init__(self, fritzbox_ip):
        self.fritzbox_ip = fritzbox_ip

    @property
    def ip(self) -> IPv4Address:
        try:
            fc = FritzStatus(address=self.fritzbox_ip)
            ip = IPv4Address(fc.external_ip)
        except AddressValueError:
            logging.error(f"unable to get external ip from FRITZ!Box {self.fritzbox_ip}")
            return None
        except ConnectionError:
            logging.error(f"unable to connect to FRITZ!Box {self.fritzbox_ip}")
            return None

        logging.debug(f"found external ip to be {ip}")
        return ip
