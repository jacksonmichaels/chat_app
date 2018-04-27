"""
Author: Jackson Michaels
Class:  CSI-235-02
Assignment:  Final Project
Date Assigned: 4/6/2018
Due Date:  4/26/2018   

Description: 
    simple chat client

Certification of Authenticity:  
I certify that this is entirely my own work, except where I have given                            
fully­documented references to the work of others. I understand the definition and
consequences of plagiarism and acknowledge that the assessor of this assignment
may, for the purpose of assessing this assignment:  ­ 
Reproduce this assignment and provide a copy to another member of academic  ­ 
staff; and/or Communicate a copy of this assignment to a plagiarism checking  ­ 
service (which may then retain a copy of this assignment on its database for the  ­ 
purpose of future plagiarism checking) 

final_client.py

    run this command "python final_client "[host name]" -p [port]

Champlain College CSI-235, Spring 2018
This code builds off skeleton code gotten from
https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter07/srv_asyncio1.py
"""

#!/usr/bin/env python3
# Foundations of Python Network Programming, Third Edition
# https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter07/srv_asyncio1.py
# Asynchronous I/O inside "asyncio" callback methods.

import asyncio, zen_utils, json, time, calendar, ssl
from struct import *

class ChatClient(asyncio.Protocol):
    """
        Class for the chat client, establishes connection and Asynchronously
        handles input from user and from server
    """
    def __init__(self, loop):
        """
            initializes client
        """

        self.loop = loop

    def connection_made(self, transport):
        """
            handles initial connection to the server
        """
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        self.data = b''
        print('Accepted connection from {}'.format(self.address))
        self.establish_username()


    def establish_username(self):
        self.username = input("Please enter username: ")
        self.username = self.username.encode('ascii')
        json_name = b'{"USERNAME": "'+self.username+b'"}'
        length = len(json_name)
        code_len = pack(b'!I', length)
        message = code_len + json_name
        self.json_loaded = False
        self.next_length = -1
        self.transport.write(message)

    def data_received(self, data):
        """
            called when data is recieved over network, handles all incoming data
        """
        self.data += data
        if (self.json_loaded == False):
            accepted = self.compile_server_data(data)
            if (not accepted):
                print("USERNAME REJECTED")
                self.establish_username()
        elif(self.json_loaded):
            if (len(self.data) >= 4 and self.next_length == -1):
                self.next_length = self.data[:4]
                self.next_length = unpack(b'!I', self.next_length)[0]
                self.data = self.data[4:]

            if (len(self.data) >= self.next_length and self.next_length != -1):
                message = self.data[:self.next_length]
                self.data = self.data[self.next_length:]
                self.output_incoming_message(message)
                self.next_length = -1

    def output_incoming_message(self, message):
        """
            takes a messaages and decides what to do with it
        """
        if (message != b''):
            in_list = json.loads(message)
            if ('MESSAGES' in in_list):
                for message in in_list['MESSAGES']:
                    self.print_message(message)

            if ('ERROR' in in_list):
                print ("ERROR: ", in_list['ERROR'])

            if ('USERS_JOINED' in in_list):
                for user in in_list['USERS_JOINED']:
                    print (user)
                print ("joined the server.")

            if ('USERS_LEFT' in in_list):
                for user in in_list['USERS_LEFT']:
                    print (user)
                print ("left the server.")


    def compile_server_data(self, data):
        """
            takes initial server data and parses it out output_incoming_message
        """
        if (self.data.find(b'}') != -1):
            start_index = self.data.find(b'{')
            end_index = self.data.find(b'}')

            self.json_data = self.data[start_index:end_index + 1]
            self.data = self.data[end_index + 1:]

            self.json_data = self.json_data.decode('ascii')
            self.json_data = json.loads(self.json_data)

            accepted = self.json_data['USERNAME_ACCEPTED']

            if (accepted):
                self.json_loaded = True

                self.print_server_status()

            return accepted

    def send_message(self, message):
        """"
            helper, is given a string and packs it up to be sent over connection
        """
        if (message != ""):
            message = self.parse_message(message)
            message = '{"MESSAGES": ['+message+']}'
            message = message.encode('ascii')
            length = len(message)
            code_len = pack(b'!I', length)
            message = code_len + message

            self.transport.write(message)

    def parse_message(self, raw_message):
        """
            takes the raw user input and converts it to a useable message
        """
        raw_list = []
        raw_list.append(self.username.decode('ascii'))
        raw_list.append('ALL')
        raw_list.append(calendar.timegm(time.gmtime()))
        raw_list.append(raw_message)

        if (raw_message.find('@') == 0):
            first_space = raw_message.find(' ')
            dest = raw_message[1:first_space]
            raw_message = raw_message[first_space:]
            raw_list[1] = dest
            raw_list[3] = raw_message

        json_message = json.dumps(raw_list)
        return json_message

    def print_message(self, message):
        """
            takes a message in list form and formats it
        """
        print ("From: ", message[0], "     ", "To: ", message[1])
        print ("Message: ", message[3])
        print()

    def print_server_status(self):
        """
            gets initial server data and desplays it nicely
        """
        print ("USERS:")
        for user in self.json_data["USER_LIST"]:
            print(user)
        print()
        print("MESSAGES:")
        for message in self.json_data["MESSAGES"][-10:]:
            self.print_message(message)

    def connection_lost(self, exc):
        if exc:
            print('Client {} error: {}'.format(self.address, exc))
        elif self.data:
            print('Client {} sent {} but then closed'
                  .format(self.address, self.data))
        else:
            print('Client {} closed socket'.format(self.address))


    async def handle_user_input(self, loop):
        """reads from stdin in separate thread

        if user inputs 'quit' stops the event loop
        otherwise just echos user input
        """
        while True:
            print("Please Enter Message, to send pm format like @[target] [message]")
            message = await loop.run_in_executor(None, input, "> ")
            if message == "quit":
                self.transport.close()
                return
            self.send_message(message)

if __name__ == '__main__':
    purpose = ssl.Purpose.SERVER_AUTH
    context = ssl.create_default_context(purpose, cafile="ca.crt")

    address = zen_utils.parse_command_line('asyncio server using callbacks')
    loop = asyncio.get_event_loop()
    client = ChatClient(loop)
    coro = loop.create_connection(lambda: client, *address, ssl = context)
    server = loop.run_until_complete(coro)


    # Start a task which reads from standard input
    asyncio.async(client.handle_user_input(loop))

    print(input)

    print('Listening at {}'.format(address))
    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
