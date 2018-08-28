"""
Netcup API implementation.
"""

import logging

from requests import Session

from .exceptions import *
from .dns import DNSRecord, DNSZone, DNSRecordSet


class NcAPI:
    """
    Manage the netcup dns nc_api via requests in a session.
    """

    def __init__(self, api_url: str, api_password: str, api_key: str, customer_id: str):
        self._api_url = api_url
        self._api_key = api_key
        self._api_password = api_password
        self._customer_id = customer_id

        self._session = None
        self._session_id = None

    def __enter__(self):
        self._login()
        return self

    def __exit__(self, *args, **kwargs):
        if self._session_id is not None:
            self._logout()
        if self._session is not None:
            self._session.__exit__(*args, **kwargs)

    def nc_request(self, action: str=None, parameters: dict={}) -> dict:
        """
        Construct a valid nc_api request according to https://ccp.netcup.net/run/webservice/servers/endpoint.php.
        :param action: action name
        :param parameters: additional parameters
        :return: payload dictionary
        """
        assert action is not None, "action has to be provided!"
        # attach nc_api session id bc it is a default parameter
        if action != "login":
            parameters = {"apisessionid":   self._session_id,
                          **parameters,
                          }

        payload = {"action":    action,
                   "param":     {
                       "customernumber":    self._customer_id,
                       "apikey":            self._api_key,
                       **parameters}
                   }

        return payload

    @property
    def session(self) -> Session:
        """
        Return a session object.
        :return: session object
        """
        if self._session is None:
            self._session = Session()

        return self._session

    def _send(self, payload: dict) -> dict:
        """
        Post nc_api request and raise if an error occured.
        :param payload: dictionary of json payload
        :return: request reponse
        """
        logging.debug(f"posting request with payload {payload}")

        r = self.session.post(url=self._api_url, json=payload)

        r.raise_for_status()

        response = r.json()

        # check if successful
        if str.lower(response["status"]) != "success":
            self.__exit__()
            raise APIException(response["longmessage"])

        # return the actual information
        logging.debug(f"request returned success with response {response}")
        return response["responsedata"]

    def _login(self):
        """
        Login to access nc_api.
        :return:
        """
        data = self._send(self.nc_request(action="login", parameters={"apipassword": self._api_password}))

        self._session_id = data["apisessionid"]

        logging.info(f"logged in successfully with session id {self._session_id}")

    def _logout(self):
        """
        Logout.
        :return:
        """
        self._send(self.nc_request(action="logout"))
        logging.info(f"logged out successfully")
        self._session_id = None

    def infoDnsZone(self, domainname: str) -> DNSZone:
        """
        Returns information in the dns zone of given domain.
        :param domainname: domain name like netcup.de
        :return: DNSZone
        """
        response = self._send(self.nc_request(action="infoDnsZone", parameters={"domainname": domainname}))

        # build zone
        zone = DNSZone(name=domainname,
                       ttl=int(response["ttl"]),
                       serial=response["serial"],
                       refresh=int(response["refresh"]),
                       retry=int(response["retry"]),
                       expire=int(response["expire"]),
                       dnssecstatus=response["dnssecstatus"])

        return zone

    def infoDnsRecords(self, domainname: str) -> DNSRecordSet:
        """
        Returns information in the dns records (aka host entries) of given domain.
        :param domainname: domain name like netcup.de
        :return: DNSRecordSet
        """
        response = self._send(self.nc_request(action="infoDnsRecords", parameters={"domainname": domainname}))

        # build records
        rset = DNSRecordSet(dnsrecords=[])
        for r in response["dnsrecords"]:
            dr = DNSRecord(id=int(r["id"]),
                           hostname=r["hostname"],
                           type=r["type"],
                           priority=int(r["priority"]),
                           destination=r["destination"],
                           deleterecord=r["deleterecord"],
                           state=r["state"])

            rset.dnsrecords.append(dr)

        return rset

    def updateDnsZone(self, zone: DNSZone):
        """
        Update/change the given dns zone.
        :param zone: dns zone dataclass
        :return:
        """
        self._send(self.nc_request(action="updateDnsZone",
                                   parameters={"domainname": zone.name, "dnszone": zone.json()}))

    def updateDnsRecords(self, zone: DNSZone, recordset: DNSRecordSet):
        """
        Update/change a given set of dns records.
        :param zone: the according dns zone has to be given to update the right domain
        :param recordset: dns record set
        :return:
        """
        self._send(self.nc_request(action="updateDnsRecords",
                                   parameters={"domainname": zone.name, "dnsrecordset": recordset.json()}))
