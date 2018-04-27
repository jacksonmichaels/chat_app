"""
Author: Jackson Michaels
Class:  CSI-235-02
Assignment:  Final Project
Date Assigned: 4/6/2018
Due Date:  4/26/2018   

Description: 
    simple chat server

Certification of Authenticity:  
I certify that this is entirely my own work, except where I have given                            
fully­documented references to the work of others. I understand the definition and
consequences of plagiarism and acknowledge that the assessor of this assignment
may, for the purpose of assessing this assignment:  ­ 
Reproduce this assignment and provide a copy to another member of academic  ­ 
staff; and/or Communicate a copy of this assignment to a plagiarism checking  ­ 
service (which may then retain a copy of this assignment on its database for the  ­ 
purpose of future plagiarism checking) 

final_server.py

    run this command "python final_server "[host name]" -p [port]

Champlain College CSI-235, Spring 2018
This code builds off skeleton code gotten from
https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter07/srv_asyncio1.py
"""


import asyncio, random, argparse, time, json
from struct import *

def parse_command_line(description):
    """gotten from https://github.com/brandon-rhodes/fopnp/tree/m/py3/chapter07
    Parse command line and return a socket address.
    Creates parser for network connections
    """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('host', help='IP or hostname')
    parser.add_argument('-p', metavar='port', type=int, default=1060,
                        help='TCP port (default 1060)')
    args = parser.parse_args()
    address = (args.host, args.p)
    return address

class Server(asyncio.Protocol):
    """
        Class for the chat server, recieves connection for clients and sends/
        recieves messages from clients
    """
    def __init__(self):
        """
            initializes client
        """
        self.users = {}
        self.messages = []
        self.next_length = -1
        self.transport = None
        self.user = ""

    def new_connection(self, user, transport):
        """
            handles when a client initially connects to the server
        """
        json_dict = {}
        allowed = self.check_login(user, transport)
        json_dict['USERNAME_ACCEPTED'] = allowed
        if (allowed):
            json_dict['INFO'] = 'Welcome to Jacksons Server'
            json_dict['USER_LIST'] = list(self.users.keys())
            json_dict['MESSAGES'] = self.messages
            self.user = user
            print(user, " joined")
        out_string = self.dict_to_proto(json_dict)
        transport.write(out_string)
        new_user_message = {}
        new_user_message['USERS_JOINED'] = [user]
        new_user_message = self.dict_to_proto(new_user_message)
        self.send_data("ALL", new_user_message)


    def dict_to_proto(self, dict_in):
        """
            takes a dictionary and turns it into a byte string matching
            the format we are using
        """
        json_string = json.dumps(dict_in)
        json_string = json_string.encode('ascii')

        str_len = len(json_string)
        str_len = pack(b'!I', str_len)

        final_string = str_len + json_string

        return final_string

    def check_login(self, user, transport):
        """
            checks if username is taken
        """
        new = not user in self.users
        if (new):
            self.users[user] = transport
        return new

    def connection_made(self, transport):
        """
            automatically called wehn user connects
        """
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        self.data = b''
        print('Accepted connection from {}'.format(self.address[1]))

    def send_data(self, target, message):
        """
            helper function to send data over network, messaage must be formated
            before calling
        """
        if (target == "ALL"):
            for user in self.users:
                self.users[user].write(message)
        else:
            valid_user = target in self.users
            if (valid_user):
                self.users[target].write(message)
            else:
                self.send_error('invalid destination')

    def send_error(self, error):
        """
            helper for sending error messages
        """
        error_message = {}
        error_message['ERROR'] = error
        error_message = self.dict_to_proto(error_message)
        print("Error: ", error)
        self.transport.write(error_message)


    def handle_message(self, message, transport):
        try:
            in_list = json.loads(message)
        except:
            self.send_error('Unable to read message')
            return
        if ('USERNAME' in in_list):
            self.new_connection(in_list['USERNAME'], transport)

        if ('MESSAGES' in in_list):
            for sub_list in in_list['MESSAGES']:
                target = sub_list[1]
                self.messages.append(sub_list)
                out_message = {}
                out_message['MESSAGES'] = [sub_list]
                final_message = self.dict_to_proto(out_message)
                self.send_data(target, final_message)

    def data_received(self, data):
        """ recievese data from stream, parses the data
            and and sends a response to each message
        """
        self.data += data
        if (len(self.data) >= 4 and self.next_length == -1):
            self.next_length = self.data[:4]
            self.next_length = unpack(b'!I', self.next_length)[0]
            self.data = self.data[4:]

        if (len(self.data) >= self.next_length and self.next_length != -1):
            message = self.data[:self.next_length]
            self.data = self.data[self.next_length:]
            self.handle_message(message, self.transport)
            self.next_length = -1


    def connection_lost(self, exc):
        if exc:
            print('Client {} error: {}'.format(self.address[1], exc))
        elif self.data:
            print('Client {} sent {} but then closed'
                  .format(self.address, self.data))
        else:
            print('Client {} closed socket'.format(self.address[1]))
            new_user_message = {}
            new_user_message['USERS_LEFT'] = [self.user]
            new_user_message = self.dict_to_proto(new_user_message)
            self.send_data("ALL", new_user_message)
            print(self.user, " left")

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
