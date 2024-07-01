"""
This module implements simple helper functions for managing service instance objects

"""

# VMware vSphere Python SDK Community Samples Addons
# Copyright (c) 2014-2021 VMware, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See LICENSE-VMWARE

__author__ = "VMware, Inc."

import atexit
import json
import logging
import os
import ssl
import time
from pyVim.connect import SmartConnect, Disconnect, vim
from pyVmomi.SoapAdapter import SoapStubAdapter
from .. import VsphereConnectException


def write_session(service_instance, sessionfile):
    cache_dict = {}
    cache_dict.update(
        {
            "host": service_instance._stub.host,
            "cookie": service_instance._stub.cookie,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": service_instance._stub.version,
        }
    )
    with open(sessionfile, "w") as json_file:
        logging.debug(f'saving session to {sessionfile}')
        json.dump(cache_dict, json_file)


def read_sessionfile(sessionfile):
    with open(sessionfile, "r") as json_file:
        loaded_dict = json.load(json_file)
    return loaded_dict


def open_session_from_sessionfile(sessionfile, host, nossl: bool):
    if nossl:
        sslcontext = ssl._create_unverified_context()
    else:
        sslcontext = ssl._create_default_https_context()
    logging.debug(f'restoring session from {sessionfile}')
    session_cookie = None
    service_instance = None

    if os.path.exists(sessionfile):
        logging.debug(f'{sessionfile} exists')
        cached_session = read_sessionfile(sessionfile)
        session_cookie = cached_session["cookie"]
        version = cached_session["version"]
    else:
        logging.debug(f'{sessionfile} missing')

    if session_cookie:
        soapStub = SoapStubAdapter(host=host, version=version, sslContext=sslcontext)
        service_instance = vim.ServiceInstance("ServiceInstance",soapStub)
        service_instance._stub.cookie = session_cookie
        content = service_instance.RetrieveContent()
        # If the session is inactive we delete the old session file
        if content.sessionManager.currentSession == None:
            logging.debug(f'session in {sessionfile} was invalid. Trying with username/password and deleting invalid sessionfile')
            os.remove(sessionfile)
            service_instance = None
        else:
            logging.debug(f'sucessfully restored session for {content.sessionManager.currentSession.userName}')
    return service_instance


def connect(args):
    """
    Determine the most preferred API version supported by the specified server,
    then connect to the specified server using that API version, login and return
    the service instance object.
    """
    sessionfile = args.sessionfile
    service_instance = None
    if sessionfile:
        service_instance = open_session_from_sessionfile(sessionfile, args.host, args.disable_ssl_verification)
        if service_instance:
            return service_instance

    # Form session otherwise
    try:
        logging.debug(f'initiating session with username/password')
        if args.disable_ssl_verification:
            service_instance = SmartConnect(
                host=args.host,
                user=args.user,
                pwd=args.password,
                port=args.port,
                disableSslCertValidation=True,
            )
        else:
            service_instance = SmartConnect(
                host=args.host,
                user=args.user,
                pwd=args.password,
                port=args.port,
            )
    except Exception as e:
        if os.environ.get("CONNECT_NOFAIL", None):
            raise VsphereConnectException("cannot connect") from e
        else:
            raise e

    if sessionfile:
        write_session(service_instance, args.sessionfile)
    else:
        logging.debug(f'disconnect session')
        # doing this means you don't need to remember to disconnect your script/objects
        atexit.register(Disconnect, service_instance)

    return service_instance
