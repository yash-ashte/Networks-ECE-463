# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
from collections import defaultdict
from router import Router
from packet import Packet
from json import dumps, loads

class DVrouter(Router):
    """Distance vector routing and forwarding implementation"""

    def __init__(self, addr, heartbeatTime, infinity):
        Router.__init__(self, addr, heartbeatTime)  # initialize superclass
        self.infinity = infinity
        """add your own class fields and initialization code here"""


    def handlePacket(self, port, packet):
        """process incoming packet.
        This method is called whenever router receives a packet (CONTROL or DATA)"""

        """parameters:
        port : the router port on which the packet was received
        packet : the received packet"""

        # default implementation sends packet back out the port it arrived
        # you should replace it with your implementation
        self.send(port, packet)


    def handleNewLink(self, port, endpoint, cost):
        """This method is called whenever a new link (including each of the initial links in the json file)
        is added to a router port, or an existing link cost is updated.
        The "links" data structure in router.py has already been updated with this change.
        Implement any routing/forwarding action that you might want to take under such a scenario"""

        """parameters:
        port : router port of the new link / the existing link whose cost has been updated
        endpoint : the node at the other end of the new link / the exisitng link whose cost has been updated
        cost : cost of the new link / updated cost of the exisitng link"""
        pass


    def handleRemoveLink(self, port, endpoint):
        """This method is called whenever an existing link is removed from the router port.
        The "links" data structure in router.py has already been updated with this change.
        Implement any routing/forwarding action that you might want to take under such a scenario"""

        """parameters:
        port : router port from which the link has been removed
        endpoint : the node at the other end of the removed link"""
        pass


    def handlePeriodicOps(self):
        """handle periodic operations. This method is called every heartbeatTime.
        The value of heartbeatTime is specified in the json file"""
        pass

