"""
This script uses the api to update a list of hosts specified in hosts.json.
An example for this list can be found in hosts.json.sample.
The settings in settings.json have to be given to access the api (again there is an example file).

The syntax for the hosts file is quite straight forward, just use the attribute names of the DNSRecord dataclass
as keywords to construct a list of hosts.
'hostname' and 'type' have to be provided, if no 'destination' is given, the current ip will be used.
All other arguments are optional (default priority is 0).

This script will not check the sanity of your entries!
"""

import json
import logging
from ipaddress import IPv4Address

import click

from nc_api import NcAPI, DNSRecord, DNSRecordSet
from nc_api.utils.external_ip import ExternalIpify, ExternalFritzbox


def import_hosts(hosts: list, ip: IPv4Address) -> DNSRecordSet:
    """
    Imports a list of hosts from the given file.
    :param hosts: array of the records which need to be updated
    :param ip: IPv4Address instance containing target ip (for dyndns)
    :return: DNSRecordSet
    """
    records = DNSRecordSet(dnsrecords=[])
    # construct records from hosts
    for h in hosts:
        # check if destination is given, else use ip argument
        destination = h["destination"] if "destination" in h else str(ip)
        records.add(DNSRecord(hostname=h["hostname"],
                              type=h["type"],
                              destination=destination))

    return records


def modify_recordset(old_set: DNSRecordSet, new_set: DNSRecordSet) -> (DNSRecordSet, bool):
    changed = False
    for new_record in new_set.dnsrecords:
        # record with this hostname exists
        if new_record.hostname in old_set:
            # get record and update it
            old_record = old_set.get_by_hostname(new_record.hostname)
            # check if update needed
            if old_record.needs_update(record=new_record):
                changed = True
                old_record.destination = new_record.destination
                old_record.type = new_record.type

        # does not exist, create it
        else:
            changed = True
            old_set.add(new_record)

    # finally return the modified set
    return old_set, changed


@click.command()
@click.argument("conf", type=click.Path(exists=True))
@click.argument("hosts", type=click.Path(exists=True))
@click.option("--update", "-u", help="update settings, defaults to False.", is_flag=True)
@click.option("--verbose", "-v", help="debugging output.", is_flag=True)
@click.option("--ttl", "-t", type=int, help="change zone ttl to integer, defaults to not change ttl.", default=None)
def dyndns(conf, hosts, update: bool=False, ttl: int=None, verbose: bool=False):
    """
    This script updates dns zone ttl and records based on the HOST file.
    See an example in hosts.sample.
    If not destination is specified, it uses the external ip found with ipify's api (https://www.ipify.org/).

    Additionally the api credentials must be passed via the settings.json file (again see settings.json.sample).

    !!!
    Please review your config in hosts.json, this script will NOT check the sanity of your dns entries.
    !!!
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)

    logging.debug(f"settings path:\t{conf}")
    logging.debug(f"hosts path:\t{hosts}")
    logging.debug(f"update:\t{update}")
    logging.debug(f"ttl:\t{ttl}")

    # read settings from file
    with open(conf) as fp:
        settings = json.load(fp)
    logging.debug(f"settings from file:\t{settings}")

    # get external ip
    fritzbox_ip = settings.get("FRITZBOX_IP")
    if fritzbox_ip is not None:
        logging.debug(f"getting external ip via FRITZ!Box API on {fritzbox_ip}")
        ip = ExternalFritzbox(fritzbox_ip).ip
    else:
        logging.debug(f"getting external ip via ipify API")
        ip = ExternalIpify().ip
    if ip is None:
        logging.error(f"unable to find external ip")
        return
    print(f"found external ip:\t{ip}")

    # read domains from file
    with open(hosts) as fp:
        domains = json.load(fp)
    logging.debug(f"domains from file:\t{domains}")
    
    # api related part
    with NcAPI(api_url=settings["API_URL"],
               api_key=settings["API_KEY"],
               api_password=settings["API_PASSWORD"],
               customer_id=settings["CUSTOMER_ID"]) as api:

        # iterate over all domains
        for domainname, settings in domains.get("zones").items():
            print(f"working on domain:\t{domainname}")

            # read current dns zone
            zone = api.infoDnsZone(domainname=domainname)
            print(zone.table())

            # read current host records
            old_set = api.infoDnsRecords(domainname=domainname)
            print(old_set.table())

            # read the new hosts set for this domain
            new_set = import_hosts(hosts=settings.get("hosts"), ip=ip)

            # modify set
            updated_set, changed = modify_recordset(old_set=old_set, new_set=new_set)
            print("\nupdated set:")
            print(updated_set.table())

            # update ttl
            changed_ttl = "ttl" in settings and settings.get("ttl") != zone.ttl
            if changed_ttl:
                zone.ttl = settings.get("ttl")
                print(f"updated ttl: {zone.ttl}")

            if update:
                print("\n update settings ...")
                if changed_ttl or changed: 
                    if changed_ttl:
                        api.updateDnsZone(zone=zone)
    
                        #read zone again
                        print(api.infoDnsZone(domainname=domainname).table())
                    if changed:
                        api.updateDnsRecords(zone=zone, recordset=updated_set)
    
                        # read current host records
                        print(api.infoDnsRecords(domainname=domainname).table())
                else:
                    print("records did not change, leaving it alone!")

if __name__ == "__main__":
    dyndns()
