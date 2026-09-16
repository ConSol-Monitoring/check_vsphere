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
import logging
import os
import ssl
from pyVim.connect import SmartConnect, Disconnect
from checkvsphere import VsphereConnectException


def write_session_id(service_instance, sessionfile):
    with open(sessionfile, "w") as s:
        logging.debug(f'saving session to {sessionfile}')
        s.write(service_instance._GetStub().GetSessionId())


def read_session_id(sessionfile):
    try:
        logging.debug(f'read session from {sessionfile}')
        return open(sessionfile).read()
    except FileNotFoundError:
        return None
    except:
        logging.exception("Error restoring session")
        return None


def get_ssl_context(args):
    ssl_context = None

    ca_file = os.environ.get("SSL_CA_FILE")
    ca_path = os.environ.get("SSL_CA_PATH")

    if ca_file or ca_path:
        ssl_context = ssl.create_default_context()
        try:
            ssl_context.load_verify_locations(cafile=ca_file, capath=ca_path)
        except Exception as e:
            logging.warning(
                f"SSL_CA_FILE or SSL_CA_PATH could not be loaded: {e}. "
                "Falling back to default system truststore."
            )
            ssl_context = None

    if args.disable_ssl_verification:
        ssl_context = ssl._create_unverified_context()

    return ssl_context

def connect(args):
    """
    Determine the most preferred API version supported by the specified server,
    then connect to the specified server using that API version, login and return
    the service instance object.
    """
    sessionfile = args.sessionfile
    sessionId = None
    service_instance = None
    if sessionfile:
        sessionId = read_session_id(args.sessionfile)


    params = {
        "host": args.host,
        "port": args.port,
        "pwd": args.password,
        "user": args.user,
        "sessionId": sessionId,
    }

    ssl_context = get_ssl_context(args)
    if ssl_context:
        params["sslContext"] = ssl_context
    else:
        params["disableSslCertValidation"] = bool(args.disable_ssl_verification)

    try:
        try:
            service_instance = SmartConnect(**params)
        except Exception:
            if sessionId:
                logging.debug("retry without sessionId")
                del params["sessionId"]
                service_instance = SmartConnect(**params)
            else:
                raise
    except Exception as e:
        if os.environ.get("CONNECT_NOFAIL", None):
            raise VsphereConnectException("cannot connect") from e
        else:
            raise e

    if sessionfile:
        write_session_id(service_instance, args.sessionfile)
    else:
        logging.debug('add disconnect handler')
        # doing this means you don't need to remember to disconnect your script/objects
        atexit.register(Disconnect, service_instance)

    return service_instance
