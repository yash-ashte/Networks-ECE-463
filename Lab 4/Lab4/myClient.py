# The code is subject to Purdue University copyright policies.
# Do not share, distribute, or post online.

import time
import sys
import queue
from client import Client
from packet import Packet

class MyClient(Client):
    """Implement a reliable transport"""

    def __init__(self, addr, sendFile, recvFile, MSS):
        """Client A is sending bytes from file 'sendFile' to client B.
           Client B stores the received bytes from A in file 'recvFile'.
        """
        Client.__init__(self, addr, sendFile, recvFile, MSS)  # initialize superclass
        self.connSetup = 0
        self.connEstablished = 0
        self.connTerminate = 0
        self.sendFile = sendFile
        self.recvFile = recvFile
        """add your own class fields and initialization code here"""
        self.currentPacket = None  # Packet being transmitted
        self.timerStart = None  # Timer for retransmissions
        #self.timeout = 5  # Timeout period (in seconds)
        self.waitingForAck = False  # Whether waiting for an ACK
        self.seqNum = 2
        self.ackNum = 2
        self.lastWrite = 1
        self.window = queue.Queue(maxsize=10)  # Queue for unacknowledged packets
        self.timers = {}  # Dictionary to track timers for packets
        self.timeout = 30
        self.dupAckCount = 0  # Track duplicate ACKs for the last acknowledged sequence number
        self.lastAckNum = -1  # Track the most recently acknowledged sequence number
        self.kDupAcks = 5 # Threshold for triggering retransmission on duplicate ACKs
        self.lastCont = 0




    def handleRecvdPackets(self):
        """Handle packets recvd from the network.
           This method is called every 0.1 seconds.
        """
        if self.link:
            packet = self.link.recv(self.addr) # receive a packet from the link
            if packet:
                # log recvd packet
                self.f.write("Packet - srcAddr: " + packet.srcAddr + " dstAddr: " + packet.dstAddr + " seqNum: " + str(packet.seqNum) + " ackNum: " + str(packet.ackNum) + " SYNFLag: " + str(packet.synFlag) + " ACKFlag: " + str(packet.ackFlag) + " FINFlag: " + str(packet.finFlag) + " Payload: " + str(packet.payload))
                self.f.write("\n")
                #print("Packet - srcAddr: " + packet.srcAddr + " dstAddr: " + packet.dstAddr + " seqNum: " + str(packet.seqNum) + " ackNum: " + str(packet.ackNum) + " SYNFLag: " + str(packet.synFlag) + " ACKFlag: " + str(packet.ackFlag) + " FINFlag: " + str(packet.finFlag) + " Payload: " + str(packet.payload))
                #print("\n")
                # handle recvd packets for client A (sender of the file)
                if self.addr == "A":

                    if packet.synFlag == 1 and packet.ackFlag == 1: # received a SYN-ACK packet
                        packet = Packet("A", "B", 1, 1, 0, 1, 0, None) # create an ACK packet
                        if self.link:
                            self.link.send(packet, self.addr) # send ACK packet out into the network
                        self.connEstablished = 1

                    elif packet.finFlag == 1 and packet.ackFlag == 1: # received a FIN-ACK packet
                        packet = Packet("A", "B", 0, 0, 0, 1, 0, None) # create an ACK packet
                        if self.link:
                            self.link.send(packet, self.addr) # send ACK packet out into the network

                    elif packet.ackFlag: # and packet.ackNum == self.seqNum + 1:
                        # Correct ACK received, move to the next packet
                        #self.seqNum += 1  # Increment the sequence number
                        ackNum = packet.ackNum
                        #print(ackNum)

                        if ackNum == self.lastAckNum:
                            self.dupAckCount += 1
                            if self.dupAckCount >= self.kDupAcks:
                                for packet in list(self.window.queue):
                                    if packet.seqNum >= ackNum:
                                        self.link.send(packet, self.addr)
                                        self.timers[packet.seqNum] = time.time()
                                self.dupAckCount = 0  # Reset duplicate ACK counter
                        else:
                            self.dupAckCount = 0  # Reset duplicate ACK counter for a new ACK
                            self.lastAckNum = ackNum


                        while not self.window.empty():
                            
                            frontPacket = self.window.queue[0]
                            if frontPacket.seqNum <= ackNum:
                                self.window.get()  # Remove the packet from the queue
                                #print(toDel)
                                del self.timers[frontPacket.seqNum]
                            else:
                                
                                break
                        #self.waitingForAck = False  # Ready to send the next packet
                        #self.timerStart = None  # Reset the timer

                # handle recvd packets for client B (receiver of the file)
                if self.addr == "B":
                    if packet.synFlag == 1: # received a SYN packet
                        packet = Packet("B", "A", 0, 1, 1, 1, 0, None) # create a SYN-ACK packet
                        if self.link:
                            self.link.send(packet, self.addr) # send SYN-ACK packet out into the network
                        self.connSetup = 1

                    elif packet.finFlag == 1: # received a FIN packet
                        packet = Packet("B", "A", 0, 0, 0, 1, 1, None) # create a FIN-ACK packet
                        if self.link:
                            self.link.send(packet, self.addr) # send FIN-ACK packet out into the network
                        self.connTerminate = 1

                    elif self.connSetup == 1 and packet.ackFlag == 1: # received an ACK packet for SYN-ACK
                        self.connSetup = 0

                    elif self.connTerminate == 1 and packet.ackFlag == 1: # received an ACK packet for FIN-ACK
                        self.connTerminate = 0

                    elif packet.ackFlag == 1 and self.connSetup == 0 and self.connTerminate == 0: # received a data packet
                        #if self.lastWrite == 0:
                         #   self.lastWrite = packet.seqNum - 1
                        #self.lastCont = packet.seqNum
                        if packet.seqNum == self.lastWrite + 1:
                            self.lastCont = packet.seqNum
                            self.recvFile.write(packet.payload) # write the contents of the packet to recvFile
                            self.lastWrite = packet.seqNum
                            ack = Packet("B", "A", 0, self.lastCont, 0, 1, 0, None)
                            self.link.send(ack, self.addr)
                        else:
                            ack = Packet("B", "A", 0, self.lastCont, 0, 1, 0, None)
                            self.link.send(ack, self.addr)


    def sendPackets(self):
        """Send packets into the network.
           This method is called every 0.1 seconds.
        """
        # send packets from client A (sender of the file)
        if self.addr == "A":
            if self.connSetup == 0:
                packet = Packet("A", "B", 0, 0, 1, 0, 0, None) # create a SYN packet
                if self.link:
                    self.link.send(packet, self.addr) # send SYN packet out into the network
                self.connSetup = 1

            if self.connEstablished == 1 and self.connTerminate == 0:
                while not self.window.full():
                    #if not self.waitingForAck:
                        content = self.sendFile.read(self.MSS) # read MSS bytes from sendFile
                        if content:
                            packet = Packet("A", "B", self.seqNum, 0, 0, 1, 0, content) # create a packet
                            #self.currentPacket = packet

                            if self.link:
                                self.link.send(packet, self.addr) # send packet out into the network
                                self.window.put(packet)
                                self.timers[self.seqNum] = time.time()  # Start the timer
                                self.seqNum += 1
                                #self.waitingForAck = True  # Expecting an ACK for this packet
                        else:
                            #print(self.window.empty())
                            if self.window.empty():
                                # start connection termination
                                packet = Packet("A", "B", 0, 0, 0, 1, 1, None) # create a FIN packet
                                if self.link:
                                    self.link.send(packet, self.addr) # send FIN packet out into the network
                                self.connTerminate = 1
                                break
                            else:
                                break
                
                current_time = time.time()
                for packet in list(self.window.queue):
                    seqNum = packet.seqNum
                    if current_time - self.timers[seqNum] > self.timeout:
                        self.link.send(packet, self.addr)  # Resend the packet
                        self.timers[seqNum] = time.time()  # Restart the timer

        # send packets from client B (receiver of the file)
        if self.addr == "B":
            pass
        


