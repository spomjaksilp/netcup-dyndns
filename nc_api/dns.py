"""
Specifies the dataclasses which are used.
These are equivalent to the datatypes defined in netcups's nc_api.
Thy can be exported as a dictionary by using the dataclasses.asdict() method.
On the other hand requests can take this dict and parse it to json.
This let's you directly pass these instances to the nc_api and make for a very transparent process.
"""

import dataclasses
from dataclasses import dataclass
from typing import List

from tabulate import tabulate

from .exceptions import *


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
    This does not correspond to a nc_api datatype and therefore does not inherit the mixin's json method.
    """
    hostname: str
    destination: str
    type: str
    id: int = None
    priority: int = 0
    deleterecord: bool = False
    state: str = None

    def needs_update(self, record) -> bool:
        """
        Checks if the records needs to be updated, currently only checks mandatory fields regarding dyndns.
        :param record: DNSRecord to check against
        :return: True if changed, False if not
        """
        return self.destination != record.destination or self.type != record.type


@dataclass
class DNSRecordSet(JSONMixin):
    """
    Basically a list of DNSRecord instances, but this maps to the datatype used by netcup.
    Also contains some helper methods.
    """
    dnsrecords: List[DNSRecord]

    def __contains__(self, hostname: str) -> bool:
        """
        Providing dunder method to check if a record woth the given hostname exists in the set.
        :param hostname: the hostname as string
        :return: True if present, False if not
        """
        try:
            self.get_by_hostname(hostname=hostname)
            return True
        except RecordUnknown:
            return False

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

    def add(self, record: DNSRecord):
        """
        Modifies the recordset.
        If an entry with matching hostname if present, modify it.
        If no entry is present, create a new one.
        :param record: a new valid dns record
        :return: None
        """
        self.dnsrecords.append(record)



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