"""
Author: Jackson Michaels
Class:  CSI-235-02
Assignment:  Lab 4
Date Assigned: 3/30/2018
Due Date:  4/6/2018   

Description: 
    Simple magic eight ball server for answering questions from a client and

Certification of Authenticity:  
I certify that this is entirely my own work, except where I have given                            
fully­documented references to the work of others. I understand the definition and
consequences of plagiarism and acknowledge that the assessor of this assignment
may, for the purpose of assessing this assignment:  ­ 
Reproduce this assignment and provide a copy to another member of academic  ­ 
staff; and/or Communicate a copy of this assignment to a plagiarism checking  ­ 
service (which may then retain a copy of this assignment on its database for the  ­ 
purpose of future plagiarism checking) 

magic_eight_client.py

    run this command "python magic_eight_server "[server name]" -p [port]

Champlain College CSI-235, Spring 2018
This code builds off skeleton code gotten from
https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter07/srv_asyncio1.py
"""



import asyncio, random, argparse

def parse_command_line(description):
    """gotten from https://github.com/brandon-rhodes/fopnp/tree/m/py3/chapter07
    Parse command line and return a socket address."""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('host', help='IP or hostname')
    parser.add_argument('-p', metavar='port', type=int, default=1060,
                        help='TCP port (default 1060)')
    args = parser.parse_args()
    address = (args.host, args.p)
    return address

class Server(asyncio.Protocol):
    def __init__(self):
        self.users = {}
        self.messages = []

    def new_connection(self, user):
        json_dict = {}
        allowed = self.check_login(user)
        json_dict['USERNAME_ACCEPTED'] = allowed
        if (allowed):
            json_dict['INFO'] = b'Welcome to Jacksons Server'
            json_dict['USER_LIST'] = list(self.users.keys())
            json_dict['MESSAGES'] = self.messages

        out_string = self.dict_to_proto(json_dict)
        print(out_string)


    def dict_to_proto(self, dict_in):
        json_string = json.loads(dict_in)
        json_string = json_string.encode('ascii')

        str_len = len(json_string)
        str_len = pack(b'!I', str_len)

        final_string = str_len + json_string

        return final_string

    def check_login(self, user, transport):
        new = not user in self.users
        if (new):
            self.users[user] = transport
        return new

    """gotten from https://github.com/brandon-rhodes/fopnp/tree/m/py3/chapter07"""
    def connection_made(self, transport):
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        self.data = b''
        print('Accepted connection from {}'.format(self.address[1]))

    def data_received(self, data):
        """ recievese data from stream, parses the data
            and and sends a response to each message
        """
        self.data += data
        print(self.data)

    def connection_lost(self, exc):
        if exc:
            print('Client {} error: {}'.format(self.address[1], exc))
        elif self.data:
            print('Client {} sent {} but then closed'
                  .format(self.address, self.data))
        else:
            print('Client {} closed socket'.format(self.address[1]))

if __name__ == '__main__':
    address = parse_command_line('asyncio server using callbacks')
    loop = asyncio.get_event_loop()
    server_obj = Server()
    coro = loop.create_server(lambda: server_obj, *address)
    server = loop.run_until_complete(coro)
    print('Listening at {}'.format(address))
    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
