# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import sys
from collections import defaultdict
from router import Router
from packet import Packet
from json import dumps, loads

class PQEntry:

    def __init__(self, addr, cost, next_hop):
        self.addr = addr
        self.cost = cost
        self.next_hop = next_hop

    def __lt__(self, other):
         return (self.cost < other.cost)

    def __eq__(self, other):
         return (self.cost == other.cost)


class LSrouter(Router):
    """Link state routing and forwarding implementation"""

    def __init__(self, addr, heartbeatTime):
        Router.__init__(self, addr, heartbeatTime)  # initialize superclass
        self.graph = {} # A dictionary with KEY = router
                        # VALUE = a list of lists of all its neighbor routers/clients and the cost to each neighbor
                        # {router: [[neighbor_router_or_client, cost]]}
        self.graph[self.addr] = []
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
        for neighbor in self.graph[self.addr]:
            if neighbor[0] == endpoint:
                self.graph[self.addr].remove(neighbor)
        self.graph[self.addr].append([endpoint,cost])


    def handleRemoveLink(self, port, endpoint):
        """This method is called whenever an existing link is removed from the router port.
        The "links" data structure in router.py has already been updated with this change.
        Implement any routing/forwarding action that you might want to take under such a scenario"""

        """parameters:
        port : router port from which the link has been removed
        endpoint : the node at the other end of the removed link"""      
        for neighbor in self.graph[self.addr]:
            if neighbor[0] == endpoint:
                self.graph[self.addr].remove(neighbor)


    def handlePeriodicOps(self):
        """handle periodic operations. This method is called every heartbeatTime.
        The value of heartbeatTime is specified in the json file"""
        pass


    def dijkstra(self):
        """An implementation of Dijkstra's shortest path algorithm.
        Operates on self.graph datastructure and returns the cost and next hop to
        each destination node in the graph as a List (finishedQ) of type PQEntry"""
        priorityQ = []
        finishedQ = [PQEntry(self.addr, 0, self.addr)]
        for neighbor in self.graph[self.addr]:
            priorityQ.append(PQEntry(neighbor[0], neighbor[1], neighbor[0]))
        priorityQ.sort(key=lambda x: x.cost)

        while len(priorityQ) > 0:
            dst = priorityQ.pop(0)
            finishedQ.append(dst)
            if not(dst.addr in self.graph.keys()):
                continue
            for neighbor in self.graph[dst.addr]:
                #neighbor already exists in finishedQ
                found = False
                for e in finishedQ:
                    if e.addr == neighbor[0]:
                        found = True
                        break
                if found:
                    continue
                newCost = dst.cost + neighbor[1]
                #neighbor already exists in priorityQ
                found = False
                for e in priorityQ:
                    if e.addr == neighbor[0]:
                        found = True
                        if newCost < e.cost:
                            e.cost = newCost
                            e.next_hop = dst.next_hop
                        break
                if not found:
                    priorityQ.append(PQEntry(neighbor[0], newCost, dst.next_hop))

                priorityQ.sort(key=lambda x: x.cost)

        return finishedQ

