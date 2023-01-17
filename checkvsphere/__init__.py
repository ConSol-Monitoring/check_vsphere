__version__ = "0.1"

class CheckVsphereException(Exception):
    pass

class CheckVsphereTimeout(BaseException):
    pass

class VsphereConnectException(Exception):
    pass
