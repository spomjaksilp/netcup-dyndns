"""
Specifies the dataclasses which are used.
These are equivalent to the datatypes defined in netcups's nc_api.
Thy can be exported as a dictionary by using the dataclasses.asdict() method.
On the other hand requests can take this dict and parse it to json.
This let's you directly pass these instances to the nc_api and make for a very transparent process.
"""

import dataclasses
from dataclasses import dataclass
from typing import List, Union

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

    def update(self, record) -> bool:
        """
        Update this record with the given one.

        :param record: The record which values should be taken.
        :return: True if something was changed, False if not
        """
        modified = []

        def check_and_write(attr):
            if getattr(self, attr) == getattr(record, attr):
                return
            setattr(self, attr, getattr(record, attr))
            modified.append(None)

        check_and_write("destination")
        check_and_write("type")

        return bool(modified)


@dataclass
class DNSRecordSet(JSONMixin):
    """
    Basically a list of DNSRecord instances, but this maps to the datatype used by netcup.
    Also contains some helper methods.
    """
    dnsrecords: List[DNSRecord]

    def __contains__(self, hostname: str) -> bool:
        """
        Providing dunder method to check if a record with the given hostname exists in the set.
        :param hostname: the hostname as string
        :return: True if present, False if not
        """
        return bool(self.get_by_hostname(hostname=hostname))

    def __iter__(self):
        return iter(self.dnsrecords)

    def table(self) -> str:
        """
        Nice representation.
        :return: string
        """
        r_table = [[r.hostname, r.type, r.destination, r.state] for r in self.dnsrecords]
        return tabulate(r_table, tablefmt="orgtbl", headers=["records", "", "", ""])

    def get_by_hostname(self, hostname):
        """
        Return the records with given hostname.
        :param hostname: a string
        :return: a (possibly empty) list of DNSRecords
        """
        return [r for r in self.dnsrecords if r.hostname == hostname]

    def add(self, record: DNSRecord) -> bool:
        """
        Modifies the recordset.
        If an entry with matching hostname if present, modify it.
        If no entry is present, create a new one.
        If the entry is already present as it, skip it.
        :param record: a new valid dns record
        :return: True, if something was changed. False, otherwise.
        """
        # record with this hostname exists
        same_hosts = self.get_by_hostname(record.hostname)
        if same_hosts:
            # only A and AAAA can be added in parallel.
            if len(same_hosts) == 2:
                # A and AAAA are present
                if record.type not in ["A", "AAAA"]:
                    same_hosts[0].update(record)
                    self.dnsrecords.delete(same_hosts[1])
                    return True
                else:
                    old_record = next(filter(lambda x: x.type == record.type,
                                             same_hosts))
                    return old_record.update(record)
            elif ((record.type == "A" and same_hosts[0].type == "AAAA") or
                  (record.type == "AAAA" and same_hosts[0].type == "A")):
                self.dnsrecords.append(record)
                return True
            else:
                # an arbitrary entry that does not fit to the current one
                return same_hosts[0].update(record)
        else:
            # not present, just append
            self.dnsrecords.append(record)
            return True
        return False


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
