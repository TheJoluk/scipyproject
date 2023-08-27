import socket
import sys
import struct
import signal
import time
from select import select

running = True

IP = "localhost"
PORT = 55555

sock = None

#Hashmap of connections identifiable by the name
connections = {}
keep_alives = {}

class MSG:
    '''
    Small class to save message protocol
    '''
    CL_CON_REQ = 0x01
    SV_CON_REP = 0x02
    SV_CON_AMSG = 0x03
    SV_PING_REQ = 0x04
    CL_PING_REP = 0x05
    SV_DISC_REP = 0x06
    CL_DISC_REQ = 0x07
    SV_DISC_AMSG = 0x08
    CL_USER_REQ = 0x09
    SV_USER_REP = 0x0a
    CL_MSG = 0x0b
    SV_AMSG = 0x0c
    SV_STOP = 0x0d

class ccolor:
    '''
    Small class to save some console colors
    '''
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'



def handle_msg(data, user):
    '''
    Handles incoming messages

    Parameters
    ----------
    data : str
        data recived from client
    user : tupel
        ip an port of the user
    '''

    #If new connection request
    if data[0] == MSG.CL_CON_REQ:
        new_connection(data, user)
    
    #If data is answer to keep alive
    elif data[0] == MSG.CL_PING_REP:
        # Reset number of unanswered keep alives
        keep_alives[user] = 0

    #If user wants to disconnect
    elif data[0] == MSG.CL_DISC_REQ:
        disconnect(user)

    #If user wants to get a list of active users
    elif data[0] == MSG.CL_USER_REQ:
        send_user_list(user)

    #If the user send a message
    elif data[0] == MSG.CL_MSG:
        send_msg(data[1:], user)


def new_connection(data, user):
    '''
    Handles new incoming connection request. 

    Parameters
    ----------
    data : str
        The send data containing user length and user name
    user : tupel
        ip and port of the user
    '''

    #Unpack message
    user_length = struct.unpack("!H", data[1:3])[0]
    user_name = struct.unpack(f"!{user_length}s", data[3:])[0].decode("utf-8")

    if user_name not in connections.values():
        #Safe user in hashmap
        connections[user] = user_name
        keep_alives[user] = 0
        
        #Create answer for new user
        msg = struct.pack(f"!BB", MSG.SV_CON_REP, 0x01)
        sendto_user(msg, user)

        #Message every other user that new user connected
        msg = struct.pack(f"!BH{len(user_name)}s", MSG.SV_CON_AMSG, len(user_name), user_name.encode('utf-8'))
        sendto_others(msg, user)

        print("[STATUS]" + ccolor.BOLD + " User " + user_name + " connected." + ccolor.ENDC)
    else:
        #Reject new user
        msg = struct.pack(f"!BB", MSG.SV_CON_REP, 0x00)
        sock.sendto(msg, user)

        print("[STATUS]" + ccolor.WARNING + " Connection rejected: User " + user_name + " already exsits." + ccolor.ENDC)

def sendto_user(msg, user):
    '''
    Sends a message to the given user

    Parameters
    ----------
    msg : str
        message to send
    ip : str
        ip of the user
    port : int
        port of the user
    '''
    sock.sendto(msg, user)

def sendto_others(msg, user):
    '''
    Sends a message to all users except the given user

    Parameters
    ----------
    msg : str
        message to send
    user : str
        user that should no recvive the message
    '''

    for other in connections:
        if connections[other] != connections[user]:
            sock.sendto(msg, other)

def sendto_all(msg):
    '''
    Sends a message to all users

    Parameters
    ----------
    msg : str
        message to send
    '''
    for user in connections:
        sock.sendto(msg, user)

def ping_clients():
    for user in list(connections):
        #Increment number of send keep alives
        keep_alives[user] = keep_alives[user] + 1

        #If the client did not respond to three keep alives send disconnect
        if (keep_alives[user] >= 4): 
            print("[Status] " + ccolor.WARNING + connections[user] + " timed out." + ccolor.ENDC)
            disconnect(user)

        #Send keep alive to user
        msg = struct.pack(f"!B", MSG.SV_PING_REQ)
        sendto_user(msg, user)

def disconnect(user): 
    '''
    Disconnects a user from the server a notifies all other users
    '''

    # Send disconnect to user
    msg = struct.pack(f"!B", MSG.SV_DISC_REP)
    sendto_user(msg, user)

    #Message every other user that user disconnected
    username = connections[user]
    msg = struct.pack(f"!BH{len(username)}s", MSG.SV_DISC_AMSG, len(username), username.encode('utf-8'))
    sendto_others(msg, user)

    # Delete user from connections hash map
    del connections[user]
    del keep_alives[user]

    print("[Status] " + ccolor.BOLD + username + " left the server." + ccolor.ENDC)

def send_user_list(user):

    msg = struct.pack(f"!BH", MSG.SV_USER_REP, len(connections))
    for u in list(connections):
        username = connections[u]
        msg += struct.pack(f"!H{len(username)}s", len(username), username.encode("utf-8"))

    sendto_user(msg, user)

    print("[STATUS] " + ccolor.BOLD + connections[user] + " requested user list." + ccolor.ENDC)

def send_msg(data, user):
    recv_msg_len = struct.unpack("!I", data[0:4])[0]
    recv_msg = struct.unpack(f"!{recv_msg_len}s", data[4:4 + recv_msg_len])[0].decode("utf-8")

    username = connections[user]
    msg = struct.pack(f"!BH{len(username)}sI{recv_msg_len}s",
                      MSG.SV_AMSG,
                      len(username),
                      username.encode("utf-8"),
                      recv_msg_len,
                      recv_msg.encode("utf-8"))
    sendto_others(msg, user)
    store_info(recv_msg, user)

    print("[CHAT] " + username + ": " + recv_msg)


def store_info(message, user):
    ''' Add Message into Pandas'''

def printStats():
    '''Create Diagram to Pandas Table'''


def handle_input(data):
    if data == "help":
        print(ccolor.BOLD + " List of all commands:" + ccolor.ENDC)
        print(ccolor.BOLD + "  help        Prints all commands." + ccolor.ENDC)
        print(ccolor.BOLD + "  stop        Stops the server." + ccolor.ENDC)
        print(ccolor.BOLD + "  CTRL+C      Stops the server." + ccolor.ENDC)

    elif data == "stop":
        global running
        running = False
    elif data == "stats":
        printStats()
    else:
        print(ccolor.WARNING + "No such command: " + data + ccolor.ENDC)

def on_SIGINT(sig, frame):
    global running
    running = False

if __name__ == "__main__":

    #Create signal handler for SIGINT
    signal.signal(signal.SIGINT, on_SIGINT)

    #Create a new socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((IP, PORT))

    #While the server is running
    last_time = time.time()
    while(running):

        #If there is data from a client to read
        if (select([sock], [], [], 0)[0]):
            data, (ip, port) = sock.recvfrom(1024) # buffer size 1024 byte
            user = (ip, port)
            handle_msg(data, user)

        #If 3 seconds passed ping all clients
        current_time = time.time()
        if current_time - last_time > 3:
            last_time = current_time
            ping_clients()

        if (select([sys.stdin], [], [], 0)[0]):
            data = input()
            handle_input(data)
    
    #If the server stops notify all clients
    msg = struct.pack("!B", MSG.SV_STOP)
    sendto_all(msg)   

    #Cleanup
    sock.close()