"""
Specifies the dataclasses which are used.
These are equivalent to the datatypes defined in netcups's api.
Thy can be exported as a dictionary by using the dataclasses.asdict() method.
On the other hand requests can take this dict and parse it to json.
This let's you directly pass these instances to the api and make for a very transparent process.
"""

import dataclasses
from dataclasses import dataclass
from typing import List

from tabulate import tabulate

from dyndns.exceptions import *


class JSONMixin:
    """
    Mixin used to refactor the json export functionality.
    """
    def json(self) -> {}:
        """
        Return data class as json like dictionary.
        See https://docs.python.org/3/library/dataclasses.html.
        :return: json like dictionary
        """
        return dataclasses.asdict(self)


@dataclass
class DNSRecord:
    """
    Dataclass for a single dns record.
    This does not correspond to a api datatype and therefore does not inherit the mixin's json method.
    """
    hostname: str
    destination: str
    type: str
    id: int = None
    priority: int = 0
    deleterecord: bool = False
    state: str = None


@dataclass
class DNSRecordSet(JSONMixin):
    dnsrecords: List[DNSRecord]

    def table(self) -> str:
        """
        Nice representation.
        :return: string
        """
        r_table = [[r.hostname, r.type, r.destination, r.state] for r in self.dnsrecords]
        return tabulate(r_table, tablefmt="orgtbl", headers=["records", "", "", ""])

    def get_by_hostname(self, hostname):
        """
        Return the record with given hostname.
        :param hostname: a string
        :return: a DNSRecord
        """
        for r in self.dnsrecords:
            if r.hostname == hostname:
                return r
        raise RecordUnknown(f"there is nor record with hostname {hostname}")


@dataclass
class DNSZone(JSONMixin):
    """
    Dataclass for dns zone.
    """
    name: str
    ttl: int
    serial: str
    refresh: int
    retry: int
    expire: int
    dnssecstatus: bool

    def table(self) -> str:
        """
        Nice representation.
        :return: string
        """
        out_table = [
            ["domain", self.name],
            ["ttl", self.ttl],
            ["serial", self.serial],
            ["refresh", self.refresh],
            ["retry", self.retry],
            ["expire", self.expire],
            ["dnssec", self.dnssecstatus],
            ]
        return tabulate(out_table, tablefmt='orgtbl', headers=["zone info", ""])