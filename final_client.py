#!/usr/bin/env python3
# Foundations of Python Network Programming, Third Edition
# https://github.com/brandon-rhodes/fopnp/blob/m/py3/chapter07/srv_asyncio1.py
# Asynchronous I/O inside "asyncio" callback methods.

import asyncio, zen_utils, json
from struct import *

class ZenServer(asyncio.Protocol):

    def connection_made(self, transport):
        self.transport = transport
        self.address = transport.get_extra_info('peername')
        self.data = b''
        print('Accepted connection from {}'.format(self.address))

        self.username = b'{"USERNAME": "jacksonm"}'
        length = len(self.username)
        code_len = pack(b'!I', length)
        message = code_len + self.username
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
                print("LENGTH: ", self.next_length)

            elif (len(self.data) >= self.next_length):
                self.data = self.data[4:]
                print("MESSAGE: ", self.data)
                self.next_length = -1

    def compile_server_data(self, data):
        if (self.data.find(b'}') != -1):
            start_index = self.data.find(b'{')
            end_index = self.data.find(b'}')

            self.json_data = self.data[start_index:end_index + 1]
            self.data = self.data[end_index + 1:]

            self.json_data = self.json_data.decode('ascii')
            self.json_data = json.loads(self.json_data)
            self.json_loaded = True

            self.print_server_status()

    def print_server_status(self):
        print ("USERS:")
        for user in self.json_data["USER_LIST"]:
            print(user)
        print('')
        print("MESSAGES:")
        for message in self.json_data["MESSAGES"][-10:]:
            print ("From: ", message[0])
            print ("To: ", message[1])
            print ("Message: ", message[3])

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

if __name__ == '__main__':
    print("DATA: ", unpack('!I', b'\x00\x00\x00<')[0])
    address = zen_utils.parse_command_line('asyncio server using callbacks')
    loop = asyncio.get_event_loop()
    coro = loop.create_connection(ZenServer, *address)
    server = loop.run_until_complete(coro)
    print('Listening at {}'.format(address))
    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
