import socket
import io
import datetime
import logging
import sys
import argparse


class ClientStream:
    '''
    Class for client data representation
    '''
    def __init__(self, client_name: tuple):
        self.client_name = client_name      # Address
        self.stream = io.BytesIO()          # Stream bytes for storing datagrams
        self.datagrams = 0                  # Datagrams count
        self.last_datagram_date = None      # Last datagram date

    def add_datagram(self, datagram: bytes):
        '''
        Write datagram to stream and increase datagrams count/last date
        :param datagram:
        :return:
        '''
        self.stream.write(datagram)
        self.last_datagram_date = datetime.datetime.now()
        self.datagrams += 1

    def get_bytes(self):
        '''
        Return bytes representation and close stream
        :return: bytes
        '''
        self.stream.seek(0)
        content = self.stream.read()
        self.stream.close()
        return content

    def get_last_datagram_date(self):
        '''
        Return last datagram date
        :return: datetime
        '''
        return self.last_datagram_date

    def __len__(self):
        '''
        Len = datagrams count
        :return:
        '''
        return self.datagrams

    def __str__(self):
        '''
        String representation
        :return:
        '''
        return f'Address: {self.client_name} |' \
               f' Datagrams: {self.datagrams} |' \
               f' Last datagram date: {self.last_datagram_date} |' \
               f' Stream status: {"open" if not self.stream.closed else "closed"}'


class UDPServer:
    """
    UDP socket server
    """
    def __init__(self):
        self.clients = {}       # Clients dict
        self.server = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    def start(self, host: str, port: int):
        """
        Bind socket and start listening
        :param host: server host
        :param port: server port
        :return:
        """
        self.server.bind((host, port))
        logger.info(f"Start at {(host, port)}")

        chunk = 4096
        logger.info('Wait for datagrams...')
        while True:
            datagram, address = self.server.recvfrom(chunk)
            self.handle_datagram(address=address, datagram=datagram)    # Datagram handling
            #Thread(target=self.handle_datagram, args=(address, datagram, )).start()

    def handle_datagram(self, address: tuple, datagram: bytes):
        """
        If client is new then send PONG and create ClientStream instance in clients dict for new client
        If client is known then store datagram into ClientStream of this client
        :param address: tuple(host, port)
        :param datagram: bytes
        :return:
        """
        if address not in self.clients:
            logger.info(f"New client {address} with message: {datagram.decode()}!")
            self.clients[address] = ClientStream(client_name=address)
            self.server.sendto(b'PONG', address)    # Optional(udp is fire and forget)
            self.print_clients()                    # Printing all clients every new client(optional)
        else:
            client_data = self.clients.get(address)
            client_data.add_datagram(datagram)
            logger.info(f"Receive new datagram from {address}. Total: {len(client_data)}")

    def print_clients(self):
        """
        Printing all clients
        :return:
        """
        logger.info("*" * 40)
        logger.info(f"Total clients: {len(self.clients)}")
        for client in self.clients.values():
            logger.info(client)
        logger.info("*" * 40)


if __name__ == '__main__':
    # Simple logger
    logger = logging.getLogger('server')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('[%(asctime)s] - %(name)-10s - %(module)-10s - [%(levelname)-8s] - %(threadName)-10s - %(message)s')
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Parse arguments
    parser = argparse.ArgumentParser(description="audio/wav streaming server")
    parser.add_argument('-uh', '--host', type=str, action='store', help='udp server host', default='localhost')
    parser.add_argument('-up', '--port', type=int, action='store', help='udp server port', default=5001)
    args = parser.parse_args()

    x = 5

    udp_server = UDPServer()
    udp_server.start(host=args.host, port=args.port)

