"Netcup API implementation"

from requests import Session
import logging

from .dns import DNSRecord, DNS


class APIException(Exception):
    pass


class NcAPI:
    """
    Manage the netcup dns api via requests in a session.
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
        Construct a valid api request according to https://ccp.netcup.net/run/webservice/servers/endpoint.php.
        :param action: action name
        :param parameters: additional parameters
        :return: payload dictionary
        """
        assert action is not None, "action has to be provided!"
        # attach api session id bc it is a default parameter
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
        Post api request and raise if an error occured.
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
        Login to access api.
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

    def infoDnsZone(self, domainname: str):
        """
        Returns information in the dns zone of given domain.
        :param domainname: domain name like netcup.de
        :return: dictionary
        """
        return self._send(self.nc_request(action="infoDnsZone", parameters={"domainname": domainname}))

    def infoDnsRecords(self, domainname: str):
        """
        Returns information in the dns records (aka host entries) of given domain.
        :param domainname: domain name like netcup.de
        :return: dictionary
        """
        return self._send(self.nc_request(action="infoDnsRecords", parameters={"domainname": domainname}))

    def get_info(self, domainname: str) -> DNS:
        """
        Return information on zone and records regarding a single domain.
        :param domainname:
        :return: custom dataclass (see dns.py for)
        """
        # first get zone and record information
        zone = self.infoDnsZone(domainname)
        records = self.infoDnsRecords(domainname)

        # build records
        records_parsed = []
        for r in records["dnsrecords"]:
            dr = DNSRecord(id=int(r["id"]),
                           hostname=r["hostname"],
                           type=r["type"],
                           priority=int(r["priority"]),
                           destination=r["destination"],
                           deleterecord=r["deleterecord"],
                           state=r["state"])

            records_parsed.append(dr)

        # build dataclass
        dns = DNS(name=domainname,
                  ttl=int(zone["ttl"]),
                  serial=zone["serial"],
                  refresh=int(zone["refresh"]),
                  retry=int(zone["retry"]),
                  expire=int(zone["expire"]),
                  dnssecstatus=zone["dnssecstatus"],
                  records=records_parsed)

        return dns
