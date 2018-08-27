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
