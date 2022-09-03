#!/usr/bin/env python3
import logging
import os
import json

from flask import Flask, request, Response
from pathlib import PurePath

from dyndns import update_dyndns
from nc_api import DNSRecord, DNSRecordSet

app = Flask(__name__)

settings_file = os.environ.get("DYNDNS_SETTINGS", "settings.json")
settings = {}
with open(settings_file) as f:
    settings = json.load(f)

logging.basicConfig(level=getattr(logging, settings.get("LOG_LEVEL", "INFO")))


@app.route("/<key>")
def dyndns_serve(key: str) -> Response:
    # load subdomains
    with open(PurePath(settings_file).parent / settings["SUBDOMAINS"]) as f:
        subs = json.load(f)
    domainname = subs["domainname"]
    subs = {x["key"]: x["hostname"] for x in subs["hosts"]}

    if key not in subs:
        return Response(status=403)
    subdomain = subs[key]

    args = request.args

    if not {"ipv4", "ipv6"} & set(args.keys()):
        return Response(response="Provide an ipv4 or ipv6 or both.", status=400)

    logging.debug(
        "Set the subdomain %s to the IPv4: %s and IPv6: %s",
        subdomain,
        args.get("ipv4", "-"),
        args.get("ipv6", "-"),
    )

    records = DNSRecordSet(dnsrecords=[])
    if "ipv4" in args:
        records.add(DNSRecord(hostname=subdomain, type="A", destination=args["ipv4"]))
    if "ipv6" in args:
        records.add(
            DNSRecord(hostname=subdomain, type="AAAA", destination=args["ipv6"])
        )
    logging.debug(records)
    update_dyndns(settings, domainname, records, update=True)

    return Response(status=200)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=os.environ.get("DYNDNS_PORT", 8081), debug=True)
