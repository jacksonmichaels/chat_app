"""
Author: Jackson Michaels
Class:  CSI-235-02
Assignment:  Lab 4
Date Assigned: 3/30/2018
Due Date:  4/6/2018   

Description: 
    Simple magic eight ball client for asking questions to a server and
    getting answers
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

    run this command "python magic_eight_client "[server name]" -p [port]

Champlain College CSI-235, Spring 2018
This code builds off skeleton code written by
Prof. Joshua Auerbach (jauerbach@champlain.edu)
"""



import socket
import argparse
import time
from threading import Thread


TEST_QUESTIONS = [b'Am I awesome?', b'Will I pass this class?',
                  b'Will a single threaded server suffice?']

class EightBallClient:
    """
        a client for asking questions to a magic_eight_server
    """
    def __init__(self, host, port):
        info_list = socket.getaddrinfo(host, port)
        info = info_list[0]
        self.sock = socket.socket(*info[0:3])
        self.sock.connect(info[4])
        self.buff = b''
        print('Client has been assigned socket name', self.sock.getsockname()[1])

    def recv_until_delimiters(self, delimiters, buffer_size=1024) :
        '''
            recieves data from stream until one of the delimiters is found, once
            one is found it parses up to the delimiter and prints results
            finally passes buffer data back into system to be parsed over
        '''
        data = self.buff
        while True:
            if (len(self.buff) == 0):
                more = self.sock.recv(buffer_size)
            else:
                more = self.buff
                self.buff = b''
            if not more:
                raise EOFError('socket was closed before delimiter was sent')
            delim_loc = self.get_first_delim(more, delimiters)
            if (delim_loc[0]):
                data = (more[:delim_loc[1]])
                self.buff = more[delim_loc[1] + 1:]
                #data += delim
                return data

            data += more
        return data

    def get_first_delim(self, message, delims):
        """
            returns a tuple (delimiter found, index of delimiter) for list of
            delimiters of any length
        """
        places = [message.find(i) for i in delims if message.find(i) != -1]
        return_val = (False, len(message) + 1)
        if (places):
            for index in places:
                if (index < return_val[1]):
                    return_val = (True, index)
        return return_val

    def ask_question(self, question):
        """
            formats question from user and sends to server
        """
        if isinstance(question, str):
            question = question.encode()
        self.sock.sendall(question)

    def recv_next_response(self):
        """
            gets reply from stream and prints it
        """
        reply = self.recv_until_delimiters((b'.', b'!'))
        return reply

    def close(self):
        self.sock.close()


def run_interactive_client(host, port):
    """
        interactive magic eightball client, allows user to ask questions
        forcing them to end with '?'
    """
    question = ""
    client = EightBallClient(host, port)
    while (question != "exit"):
        question = input("Please enter your question (with exactly 1'?') or exit to quit: ")

        if (question == "exit"):
            continue
        if (question.endswith('?') != True or question.count('?') != 1):
            print ("ERROR: please enter a question with no more or less than 1 (one) '?' as the last character")
            continue
        client.ask_question(question)
        reply = client.recv_next_response()
        print (reply)
        print('')
    client.close()


def run_single_test_client(host, port):
    """
        simple automatic test of client and server, asks 3 questions and prints
        3 replies
    """
    replies = 0
    client = EightBallClient(host, port)
    for question in TEST_QUESTIONS:
        client.ask_question(question)
    for i in range(len(TEST_QUESTIONS)):
        reply = client.recv_next_response()
        print ('[' + str(client.sock.getsockname()[1]) + '] ' + reply.decode())
        print('')
    client.close()

def test(host, port, workers):
    """
        runs three threaded testing clients at the same time
    """
    for i in range(workers):
        thread = Thread(target = run_single_test_client, args = (host, port))
        thread.start()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Example client')
    parser.add_argument('host', help='IP or hostname')
    parser.add_argument('-p', metavar='port', type=int, default=7000,
                        help='TCP port (default 7000)')
    parser.add_argument('-t', action='store_true', help='test mode')
    parser.add_argument('-n', metavar='num threads', type=int, default=4,
                        help='Num threads for test mode')
    args = parser.parse_args()
    if args.t:
        test(args.host, args.p, args.n)
    else:
        run_interactive_client(args.host, args.p)
