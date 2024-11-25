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

        self.routing_table = {} #{dest: (next hop, cost)}
        self.neighbors = {} #{neighbor: (port, cost)}
        self.received_ctrl_packets = []
    
    def broadcast_control_packets(self):

        for neighbor, (port, _) in self.neighbors.items():
            if port is not None and neighbor.isdigit():
                update = Packet(Packet.CONTROL, self.addr, neighbor, dumps(self.routing_table))
                self.send(port, update)

    
    def handlePacket(self, port, packet):
        """process incoming packet.
        This method is called whenever router receives a packet (CONTROL or DATA)"""

        """parameters:
        port : the router port on which the packet was received
        packet : the received packet"""

        # default implementation sends packet back out the port it arrived
        # you should replace it with your implementation
        #self.send(port, packet)

        if packet.isData():

            dest = packet.dstAddr
            if dest in self.routing_table:
                hop, _ = self.routing_table[dest]
                for neighbor, (port, _) in self.neighbors.items():
                    if hop != neighbor:
                        continue
                    elif hop == neighbor:
                        self.send(port, packet)
                        return
            #
            #print(f"Packet dropped: no route to {dest}")

        elif packet.isControl():

            update = 0
            for dest, link_data in loads(packet.content).items():
                if dest == self.addr or link_data[0] is None or (dest in self.routing_table and self.routing_table[dest][0] == self.addr):# or link_data[0] == self.addr:
                    continue
               
                new_cost = self.neighbors[packet.srcAddr][1] + link_data[1]
                if new_cost >= self.infinity:
                    self.routing_table[dest] = (None, self.infinity)
                    update = 1
                    continue
                if (dest not in self.routing_table or packet.srcAddr == self.routing_table[dest][0] or self.routing_table[dest][0] is None) or ((packet.srcAddr != self.routing_table[dest][0]) and (new_cost < self.routing_table[dest][1] or (new_cost == self.routing_table[dest][1] and ord(packet.srcAddr) > ord(self.routing_table[dest][0])))):
                    self.routing_table[dest] = (packet.srcAddr, new_cost)
                    update = 1
            if update == 1:
                self.broadcast_control_packets()
    


    def addRoute(self, port, endpoint, cost):
        self.neighbors[endpoint] = (port, cost)
        self.routing_table[endpoint] = (endpoint, cost)

    def handleNewLink(self, port, endpoint, cost):
        """This method is called whenever a new link (including each of the initial links in the json file)
        is added to a router port, or an existing link cost is updated.
        The "links" data structure in router.py has already been updated with this change.
        Implement any routing/forwarding action that you might want to take under such a scenario"""

        """parameters:
        port : router port of the new link / the existing link whose cost has been updated
        endpoint : the node at the other end of the new link / the exisitng link whose cost has been updated
        cost : cost of the new link / updated cost of the exisitng link"""
        #pass
        '''and cost < self.routing_table[endpoint][1]'''
        #print("coutner\n")

        if (endpoint not in self.routing_table) or (endpoint in self.routing_table and self.routing_table[endpoint][0] != endpoint and cost < self.routing_table[endpoint][1]):
            self.addRoute(port, endpoint, cost)
            
        for dest in self.routing_table:
            #print(f"here {self.addr} {endpoint}\n")
            if self.routing_table[dest][0] == endpoint and dest != endpoint:
                if dest != endpoint:
                    new_cost = self.routing_table[dest][1] + cost
                    #print(f"how - {self.addr} {self.routing_table[dest][0]} {cost} {new_cost} {dest}\n")
                    self.routing_table[dest] = (endpoint, new_cost)
        self.broadcast_control_packets()


    def unReachable(self, endpoint):
        for dest in self.routing_table:
            if self.routing_table[dest][0] == endpoint:
                self.routing_table[dest] = (None, self.infinity)
            
    def handleRemoveLink(self, port, endpoint):
        """This method is called whenever an existing link is removed from the router port.
        The "links" data structure in router.py has already been updated with this change.
        Implement any routing/forwarding action that you might want to take under such a scenario"""

        self.neighbors[endpoint] = (port, self.infinity)
        self.unReachable(endpoint)
        self.broadcast_control_packets()
    
    
    
    def handlePeriodicOps(self):
        """Periodic update of routing table to neighbors."""
        self.broadcast_control_packets()

