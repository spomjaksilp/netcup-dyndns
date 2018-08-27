from tabulate import tabulate

from dataclasses import dataclass
from typing import List


@dataclass
class DNSRecord:
    """
    Dataclass for a single dns record.
    """
    id: int
    hostname: str
    type: str
    priority: int
    destination: str
    deleterecord: bool
    state: str


@dataclass
class DNS:
    """
    Complete dns information for a given domain.
    """
    name: str
    ttl: int
    serial: str
    refresh: int
    retry: int
    expire: int
    dnssecstatus: bool
    records: List[DNSRecord]

    def __str__(self):
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

        r_table = [[r.hostname, r.type, r.destination, r.state] for r in self.records]

        return tabulate(out_table, tablefmt='orgtbl', headers=["zone info", ""]) + "\n\n"\
               + tabulate(r_table, tablefmt="orgtbl", headers=["records", "", "", ""])
