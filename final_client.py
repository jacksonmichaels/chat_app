#!/usr/bin/env python3
# Foundations of Python Network Programming, Third Edition
# https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter07/srv_asyncio1.py
# Asynchronous I/O inside "asyncio" callback methods.

import asyncio, zen_utils, json, time
from struct import *

class ChatClient(asyncio.Protocol):
    def __init__(self, loop):
        self.loop = loop

    def connection_made(self, transport):
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        self.data = b''
        print('Accepted connection from {}'.format(self.address))

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
        self.data += data
        if (self.json_loaded == False):
            self.compile_server_data(data)
        elif(self.json_loaded):
            if (len(self.data) > 4 and self.next_length == -1):
                self.next_length = self.data[:4]
                self.next_length = unpack(b'!I', self.next_length)[0]
            elif (len(self.data) >= self.next_length):
                self.data = self.data[4:]
                print("MESSAGE: ", self.data)
                self.next_length = -1
                self.data = b''

    def compile_server_data(self, data):
        if (self.data.find(b'}') != -1):
            print(self.data)
            start_index = self.data.find(b'{')
            end_index = self.data.find(b'}')

            self.json_data = self.data[start_index:end_index + 1]
            self.data = self.data[end_index + 1:]

            self.json_data = self.json_data.decode('ascii')
            self.json_data = json.loads(self.json_data)
            self.json_loaded = True

            self.print_server_status()

    def send_message(self, message):
        if (message != ""):
            message = self.parse_message(message)
            message = '{"MESSAGES": ['+message+']}'
            message = message.encode('ascii')
            length = len(message)
            code_len = pack(b'!I', length)
            message = code_len + message

            self.transport.write(message)

    def parse_message(self, raw_message):
        raw_list = []
        raw_list.append(self.username.decode('ascii'))
        raw_list.append('ALL')
        raw_list.append(500000)
        raw_list.append(raw_message)

        if (raw_message.find('@') == 0):
            first_space = raw_message.find(' ')
            dest = raw_message[1:first_space]
            raw_message = raw_message[first_space:]
            raw_list[1] = dest
            raw_list[3] = raw_message

        json_message = json.dumps(raw_list)
        return json_message


    def print_server_status(self):
        print ("USERS:")
        for user in self.json_data["USER_LIST"]:
            print(user)
        print()
        print("MESSAGES:")
        for message in self.json_data["MESSAGES"][-10:]:
            print ("From: ", message[0], "     ", "To: ", message[1])
            print ("Message: ", message[3])
            print()

    def get_inital_data(self):
        pass

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
                loop.stop()
                return
            self.send_message(message)

if __name__ == '__main__':
    address = zen_utils.parse_command_line('asyncio server using callbacks')
    loop = asyncio.get_event_loop()
    client = ChatClient(loop)
    coro = loop.create_connection(lambda: client, *address)
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
