# -*- coding:utf-8 -*-

from io import BytesIO
from fabric import *
from scp import SCPClient

class ConnectionWithSCP(Connection):

    @property
    def scp(self):
        return SCPClient(self.client.get_transport())

    def put(self, src, dest):
        """Patch to addres a case where parameko fails to use an sftp socket

        The reason to use scp over the fabric.put method is that fabric uses the
        parameko sftp implementation which was found to be closing sockets all
        over the place.
        """
        if isinstance(src, BytesIO):
            self.scp.putfo(src, dest)
        else:
            self.scp.put(src, dest)
