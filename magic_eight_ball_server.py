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

answers = [
	b"As I see it, yes.",
	b"It is certain.",
	b"It is decidedly so.",
	b"Most likely.",
	b"Outlook good.",
	b"Signs point to yes.",
	b"Without a doubt.",
	b"Yes!",
	b"Yes - definitely.",
	b"You may rely on it.",
	b"Reply hazy, try again.",
	b"Ask again later.",
	b"Better not tell you now.",
	b"Cannot predict now.",
	b"Concentrate and ask again.",
	b"Don't count on it.",
	b"My reply is no.",
	b"My sources say no.",
	b"Outlook not so good.",
	b"Very doubtful.",
]

def rand_answer():
    """ Retrieves a random answer from answers list """
    choice = random.choice(answers)
    return choice

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

def parse_until_delim(data, delim):
    """ takes a byte string and finds theh delimiter in it
        if found it splits the string and returns a tuple
        if not found it leaves it intact and returnsa failed
        status
    """
    result = b''
    found = False
    if not data:
        raise EOFError('socket was closed before delimiter was sent')
    if (delim in data):
        found = True
        result += (data[:data.find(delim)])
        buff = data[data.find(delim) + len(delim):]

    return (found, result, buff)

class ZenServer(asyncio.Protocol):
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
        results = parse_until_delim(self.data, b'?')
        if (results[0]):
            print(self.address[1], "Asked: " , results[1])
            answer = rand_answer()
            self.transport.write(answer)
            self.data = results[2]
            while (self.data != b''):
                results = parse_until_delim(self.data, b'?')
                print(self.address[1], "Asked: " , results[1])
                answer = rand_answer()
                self.transport.write(answer)
                self.data = results[2]

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
    coro = loop.create_server(ZenServer, *address)
    server = loop.run_until_complete(coro)
    print('Listening at {}'.format(address))
    try:
        loop.run_forever()
    finally:
        server.close()
        loop.close()
