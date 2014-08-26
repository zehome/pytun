""" pytun

pytun is a tiny piece of code which gives you the ability to create and
manage tun/tap tunnels on Linux (for now).

"""

__author__ = "Gawen Arab"
__copyright__ = "Copyright 2012, Gawen Arab"
__credits__ = ["Gawen Arab"]
__license__ = "MIT"
__version__ = "1.0.1"
__maintainer__ = "Gawen Arab"
__email__ = "g@wenarab.com"
__status__ = "Beta"

import os
import fcntl
import struct
import logging
import functools

TUN_KO_PATH = "/dev/net/tun"

logger = logging.getLogger("pytun")

class Tunnel(object):
    """ tun/tap handler class """

    class AlreadyOpened(Exception):
        """ Raised when the user try to open a already-opened
            tunnel.
        """
        pass

    class PermissionDenied(Exception):
        """ Raised when pytun try to setup a new tunnel without
            the good permissions.
        """
        pass
 
    MODES = {
        "tun": 0x0001,
        "tap": 0x0002,
    }

    # ioctl call
    TUNSETIFF = 0x400454ca

    def __init__(self, mode=None, pattern=None):
        """ Create a new tun/tap tunnel. Its type is defined by the
            argument 'mode', whose value can be either a string or
            the system value.

            The argument 'pattern set the string format used to
            generate the name of the future tunnel. By default, for
            Linux, it is "tun%d" or "tap%d" depending on the mode.

            If the argument 'auto_open' is true, this constructor
            will automatically create the tunnel.

        """
        mode = mode if mode is not None else "tun"
        pattern = pattern if pattern is not None else ""
        auto_open = auto_open if auto_open is not None else True
        super(Tunnel, self).__init__()
        self.pattern = pattern
        self.mode = mode
        self.name = None
        self.fd = None

        if isinstance(self.mode, str):
            self.mode = self.MODES.get(self.mode, None)
            assert self.mode is not None, "%r is not a valid tunnel type." % (self.mode, )

    def __del__(self):
        self.close()

    @property
    def mode_name(self):
        """ Returns the tunnel mode's name, for printing purpose. """
        for name, id in self.MODES.items():
            if id == self.mode:
                return name

    def fileno(self):
        return self.fd

    def open(self):
        """ Create the tunnel.
            If the tunnel is already opened, the function will
            raised an AlreadyOpened exception.
        """
        if self.fd is not None:
            raise self.AlreadyOpened()
        logger.debug("Opening %s..." % (TUN_KO_PATH, ))
        self.fd = os.open(TUN_KO_PATH, os.O_RDWR)
        logger.debug("Opening %s tunnel '%s'..." % (self.mode_name.upper(), self.pattern, ))
        try:
            ret = fcntl.ioctl(self.fd, self.TUNSETIFF, struct.pack("16sH", self.pattern.encode(), self.mode))
        except IOError as e:
            if e.errno == 1:
                logger.error("Cannot open a %s tunnel because the operation is not permitted." % (self.mode_name.upper(), ))
                raise self.PermissionDenied()

            raise
        self.name = str(ret[:16].strip(b"\x00"))
        logger.info("Tunnel '%s' opened." % (self.name, ))

    def close(self):
        if self.fd:
            os.close(self.fd)
            self.fd = None
            logger.info("Tunnel '%s' closed." % (self.name or "", ))

    def send(self, buf):
        os.write(self.fd, buf)

    def recv(self, size=1500):
        return os.read(self.fd, size)

    def __repr__(self):
        return "<%s tunnel '%s'>" % (self.mode_name.capitalize(), self.name, )

