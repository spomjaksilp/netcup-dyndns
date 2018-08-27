if __name__ == "__main__":
    from dyndns.nc_api import NcAPI
    from dyndns.external_ip import ExternalIpify

    import json
    import logging

    # get external ip
    ip = ExternalIpify().ip
    print(f"external ip {ip}")

    with open("settings.json") as fp:
        settings = json.load(fp)

    with NcAPI(api_url=settings["API_URL"],
               api_key=settings["API_KEY"],
               api_password=settings["API_PASSWORD"],
               customer_id=settings["CUSTOMER_ID"]) as api:
        dns = api.get_info(domainname="laz0r.de")
        print(dns)