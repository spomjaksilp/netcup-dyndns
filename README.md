# netcup-dyndns
**A dynamic DNS updater written in python.**

*Well actually it turned out to be the starting point for a complete dns api client :D*

This project is heavily inspired by @stecklars project:
https://github.com/stecklars/dynamic-dns-netcup-api

## Obvious requirements
 * netcup api key and api password (you can generate them in the customer control panel)
 * at least one domain
 
## Technical requirements
 * `python >= 3.7` yes, you read right. This software makes use of some new features, especially `dataclasses` to construct the api data types
 * `pipenv` is used to build the environment and execute the script
 
 Python in the required version is no default in most linux distribution, but you can run in in a docker container.
 Included is a Dockerfile based on `python:3.9-alpine`.
 Build this by `docker build -t nc_dyndns_python .` and run by `docker run nc_dyndns_python:latest`.
 
## Installation (if you run `python 3.7` or higher)
 * download the repository  `git clone https://github.com/spomjaksilp/netcup-dyndns.git`
 * change into the directory and run `pipenv install`
 
## Dyndns usage
 run `pipenv run dyndns --help` for information on options:
 ```
Usage: dyndns.py [OPTIONS] CONF HOSTS

  This script updates dns zone ttl and records based on the HOST file. See
  an example in hosts.sample. If not destination is specified, it uses the
  external ip found with ipify's api (https://www.ipify.org/).

  Additionally the api credentials must be passed via the settings.json file
  (again see settings.json.sample).

  !!! Please review your config in hosts.json, this script will NOT check
  the sanity of your dns entries. !!!

Options:
  -u, --update       update settings, defaults to False.
  -v, --verbose      debugging output.
  -t, --ttl INTEGER  change zone ttl to integer, defaults to not change ttl.
  --help             Show this message and exit.

```

## Server usage
You can also use this repository as a DynDNS server (based on Flask) on a trusted host.
With that, you can call an URL with predefined parameters and the server will update the DNS settings.

The service accepts URLs in the form:
```
http://myhost.com/<key>?ipv4=<ipv4>&ipv6=<ipv6>
```

### Deployment

1. Provide a `settings.json` as described in the next section.
   The server recognizes the environment variable `DYNDNS_SETTINGS` as file path (default is `settings.json`).
2. Provide a `subdomains.json` as described further down.
3. Connect the Flask app to your webserver. For example, this is possible with [gunicorn](https://gunicorn.org/) and systemd.
   For that, adjust the paths in `dnydns-server.service`, copy it in `/etc/systemd/system/`, and start it.
   Adjust also your webserver. For example, with nginx, add these lines:
```
location /dyndns/ {
	proxy_pass http://localhost:40404/;
}
```
 
## API settings
 This `settings.json` file configures the api credentials.
 ```json
{
  "API_URL":        "https://ccp.netcup.net/run/webservice/servers/endpoint.php?JSON",
  "API_PASSWORD":   "0123456789",
  "API_KEY":        "abcdefg",
  "CUSTOMER_ID":    "13"
}
```

If you would like to use your [FRITZ!Box](https://en.wikipedia.org/wiki/Fritz!Box) for getting your external ip, you need to add its ip address in this `json` file:
 ```
  "FRITZBOX_IP":    "192.168.178.1"
```

If you will run the service as a server, you need to provide a few additional entries:

 * The file path to the `subdomains.json` file (relative to `settings.json`)
```
  "SUBDOMAINS": "subdomains.json"
```
 * A log level (optional)
```
  "LOG_LEVEL": "DEBUG"
```

## Host records
This `hosts.json` file specifies the hosts to be updated.

If no `destination` is specified, the found external ip will be used.
```json
{
  "zone":
  {
    "domainname": "example.com"
  },
  "hosts":  [
    {
      "hostname":     "alice",
      "type":         "A"
    },
    {
      "hostname":     "bob",
      "type":         "CNAME",
      "destination":  "alice.example.com"
    },
    {
      "hostname":     "charlie",
      "type":         "CNAME",
      "destination":  "alice.example.com"
    }
  ]
}
```

## Subdomains
When run in server mode, an additional file specifies a mapping between the key and the hostname:
```json
{
  "domainname": "example.com",
  "hosts":  [
    {
      "hostname": "alice",
      "key":      "3is83sen"
    },
    {
      "hostname": "bob",
      "key":      "s8dfwske"
    }
  ]
}
```
With that file the domain `alice.example.com` can be updated by calling the URL:
```
http://myhost.com/3is83sen?ipv4=10.10.10.10
```

## API usage examples
 If you want to use api, please take a look at the source files.
 
Getting the external IP with www.ipify.org API (default):
 ```python
from nc_api.utils.external_ip import ExternalIpify

print(ExternalIpify().ip)
```

Getting the external IP with [FRITZ!Box API](https://github.com/kbr/fritzconnection) (alternative, if you own one):
 ```python
from nc_api.utils.external_ip import ExternalFritzbox

print(ExternalFritzbox("192.168.178.1").ip)
```

Retrieving dns zone info and dns records:
```python
import json

from nc_api import NcAPI

with open("settings.json") as fp:
    settings = json.load(fp)

# usage in a contextmanager makes sure the session is ended properly
with NcAPI(api_url=settings["API_URL"],
           api_key=settings["API_KEY"],
           api_password=settings["API_PASSWORD"],
           customer_id=settings["CUSTOMER_ID"]) as api:

    zone = api.infoDnsZone(domainname="example.com")
    print(zone.table())

    recordset = api.infoDnsRecords(domainname="example.com")
    print(recordset.table())
```
