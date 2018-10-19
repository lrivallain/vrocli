#!/usr/bin/env python

import requests
import os
from utils import confirm_action, logger
import getpass

# disable ssl warnings
requests.packages.urllib3.disable_warnings()


class VroServer():
    def __init__(self, name, config):
        self.hostname = name
        server_conf = self.is_configured(config)
        self.username = server_conf.get('user', None)
        if not self.username:
            self.username = input('vRO API username: ')
        self.password = server_conf.get('pwd', None)
        if not self.password:
            self.password = getpass.getpass("vRO API password: ")
        self.verify_ssl = server_conf.get('verify_ssl', True)


    def is_configured(self, config):
        try:
            return config['vro_servers'][self.hostname]
        except KeyError:
            logger.error("vRO Server %s is not configured. Ensure to add it to your local configuration before to use it."
                % self.hostname)
            exit(-1)


    def pull(self, package_name, destination):
        headers = {'accept': 'application/zip'}
        r = requests.get("https://%s/vco/api/packages/%s" % (self.hostname, package_name),
                auth = (self.username, self.password),
                headers = headers,
                verify = self.verify_ssl
            )
        #r.raise_for_status()
        if not r.status_code == requests.codes.ok:
            logger.error("Bad HTTP response code: %d" % r.status_code)
            exit(-1)
        logger.info("Downloading package data from %s to %s " %
                    (self.hostname, destination))
        open(destination, 'wb').write(r.content)


    def push(self, package_name, file_location):
        #headers = {'accept': 'application/zip'}
        files = {'file': ('%s.package' % package_name,
                            open(file_location, 'rb'),
                            'application/zip',
                            {'Expires': '0'})
                }
        r = requests.post("https://%s/vco/api/packages/?overwrite=true" % self.hostname,
                auth = (self.username, self.password),
                verify = self.verify_ssl,
                files = files
            )
        #r.raise_for_status()
        if not r.status_code == requests.codes.accepted:
            logger.error("Bad HTTP response code: %d" % r.status_code)
            exit(-1)
        logger.info("Pushed %s package content to %s" % 
                    (package_name, self.hostname))
