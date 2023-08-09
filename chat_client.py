import sys
import socket
#import ipaddress
import struct
from select import select

sock = None
connected = False

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

def cleanup():
    '''
    Closes the socket and ends the programm
    '''
    sock.close()
    sys.exit(0)

def handle_msg(data, serv, port) -> bool:
    '''
    Handles all incoming messages from the server and prints/ 
    sends back messages accordingly

    Parameters
    ----------
    data : str
        The data that was reveived
    serv : str
        The server ip
    port : str
        The port

    Returns
    -------
    True
        if the connection should continue
    False
        if the programm should end
    '''

    #If another client connects to the server
    if data[0] == MSG.SV_CON_AMSG:
        user_length = struct.unpack("!H", data[1:3])[0]
        user = struct.unpack(f"!{user_length}s", data[3:])[0].decode("utf-8")
        print("[STATUS] " + ccolor.BOLD + f"User {user} joined the chat." + ccolor.ENDC)
        return True

    #If data is a keepalive send response
    elif data[0] == MSG.SV_PING_REQ:
        msg = struct.pack(f"!B", MSG.CL_PING_REP)
        sock.sendto(msg, (serv, port))
        return True

    #If client times out
    elif data[0] == MSG.SV_DISC_REP:
        print("[Status] " + ccolor.FAIL + f"Lost connection to the server. Timeout." + ccolor.ENDC)
        return False
    
    #If a user left the chat
    elif data[0] == MSG.SV_DISC_AMSG:
        user_length = struct.unpack("!H", data[1:3])[0]
        user = struct.unpack(f"!{user_length}s", data[3:])[0].decode("utf-8")
        print("[CHAT] " + ccolor.BOLD + f"{user} left the chat." + ccolor.ENDC)
        return True
    
    #If the client searched for a user, handle answer
    elif data[0] == MSG.SV_USER_REP:
        read_user_list(data[1:])
        return True
    
    #If a user send a message
    elif data[0] == MSG.SV_AMSG:
        user_length = struct.unpack("!H", data[1:3])[0]
        user = struct.unpack(f"!{user_length}s", data[3:3 + user_length])[0].decode("utf-8")
        msg_length = struct.unpack("!I", data[3 + user_length:7 + user_length])[0]
        msg = struct.unpack(f"{msg_length}s", data[7 + user_length:])[0].decode("utf-8")
       
        print(f"[CHAT] {user}: {msg}")
        return True
    
    #If the server stops
    elif data[0] == MSG.SV_STOP:
        print("[SERVER]" + ccolor.FAIL + " Server closed." + ccolor.ENDC)
        return False

    #If a message was received that has an unknown id, return false.
    #This should never happen
    return False

def disconnect(serv, port):
    '''
    Disconnects the client from the server safetly.
    Tries three times before timeout. Ends the programm.

    Parameters
    ----------
    serv : str
        The server ip
    port : str
        The port
    '''

    connected = False
    msg = struct.pack("!B", MSG.CL_DISC_REQ)
    data = None
    i = 0

    print("[Status] " + ccolor.BOLD + f"Disconnecting from {socket.gethostbyaddr(serv)[0]} ({serv})." + ccolor.ENDC)

    while i < 3:
        #Send disconnect request
        sock.sendto(msg, (serv, port))

        #If the socket is ready to read within 5 seconds
        if select([sock], [], [], 5)[0]:
            data = sock.recv(1024)
            #If the server answers the disconnect request
            if data[0] == MSG.SV_DISC_REP:
                print("[Status] " + ccolor.BOLD + f"Connection was terminated successfully." + ccolor.ENDC)
                cleanup()
            #If another message arrives
            else:
                handle_msg(data, serv, port)
                #Decrement i so the received message does not interfere with the disconnect function
                i -= 1
                data = None
        i += 1
    print("[Status] " + ccolor.FAIL + f"Could not tear down the connection. Timeout." + ccolor.ENDC)
    cleanup()

def read_user_list(data):
    
    #Get the number of currently online users
    num_users = struct.unpack("!H", data[0:2])[0]
    
    print("[STATUS]" + ccolor.BOLD + " List of currently connected users:" + ccolor.ENDC)
    p = 2
    for i in range(num_users):
        user_len = struct.unpack("!H", data[p:p+2])[0]
        p += 2
        username = struct.unpack(f"!{user_len}s", data[p:p+user_len])[0].decode("utf-8")
        p += user_len
        print(ccolor.BOLD + "  " + username + ccolor.ENDC)
        
def send_msg(msg, serv, port):
    '''
    Evaluades the type of message the user tries to send.
    Calls the appropriate function or sends the message

    Parameters
    ----------
    msg : str
        The message
    serv : str
        The server ip
    port : int
        The port
    '''
    
    #Messages should be at least 1 char long
    if len(msg) < 1:
        return
    
    if msg == "/help":
        print("[HELP]" + ccolor.BOLD + "List of all commands:" + ccolor.ENDC)
        print(ccolor.BOLD + "  /help        Prints all commands." + ccolor.ENDC)
        print(ccolor.BOLD + "  /disconnect  Disconnects the user from the server." + ccolor.ENDC)
        print(ccolor.BOLD + "  /listusers   Lists all connected users." + ccolor.ENDC)
        return

    #If the user wants to disconnect
    if msg == "/disconnect":
        disconnect(serv, port)
        return

    #If the user wants to get a list of active users
    if msg == "/listusers":
        msg = struct.pack(f"!B", MSG.CL_USER_REQ)
        sock.sendto(msg, (serv, port))    
        return

    #If the msg starts with a '/' but is none of the above commands print error
    if msg[0] == "/":
        print("[STATUS]" + ccolor.WARNING + " No such command: " + msg[1:] + ccolor.ENDC)
        return
    
    #Get the length of the message in bytes
    msg_length = len(msg.encode("utf-8"))

    #If the message is not too long
    if msg_length <= 1400:
        msg = struct.pack(f"!BI{msg_length}s", MSG.CL_MSG, msg_length, msg.encode("utf-8"))
        sock.sendto(msg, (serv, port))

def connection_setup(user, serv, port):
    '''
    Sets up the connection to the given server and port
    Tries three times befor timeout.

    Parameters
    ----------
    user : str
        The user name
    serv : str
        The server ip
    port : int
        The port

    Returns
    -------
    True if the connection was successful, False otherwise
    '''

    #Create msg CL_CON_REQ with length of user name and the username
    msg = struct.pack(f"!BH{len(user)}s", MSG.CL_CON_REQ, len(user), user.encode('utf-8'))

    print("[STATUS] " + ccolor.BOLD + f"Connecting as {user}." + ccolor.ENDC)

    #Recieve reply. Try three times
    data = None
    i = 0
    while i < 3:
        #Send connection request
        sock.sendto(msg, (serv, port))

        #If the socket is ready to read within 3 seconds
        if select([sock], [], [], 3)[0]:
            data = sock.recv(1024)
            #If the server answers the connection request
            if data[0] == MSG.SV_CON_REP:
                break
            #If an error occurs
            else:
                handle_msg(data, serv, port)
                #Decrement i so the received message does not interfere with the connect function
                i -= 1
                data = None
        i += 1

    #If after three atempts nothing is recieved
    if not data:
        print("[STATUS] " + ccolor.FAIL + "Connection rejected. Server does not answer." + ccolor.ENDC)
        return False

    #If reply is 0, exit
    if data[1] == 0x00:
        print("[SERVER] " + ccolor.FAIL + "Connection rejected by server." + ccolor.ENDC)
        return False
    
    #if reply is 1, connection successful
    elif data[1] == 0x01:
        print("[STATUS] " + ccolor.BOLD + f"Connection accepted." + ccolor.ENDC)
        return True
    
    #Should not be reached
    print("[STATUS] " + ccolor.FAIL + "Unexpected error." + ccolor.ENDC)
    return False

def read_arguments():
    '''
    Returns the username

    Returns
    -------
    user : str
        The user name
    serv : str
        The server
    port : int
        The port
    '''

    # Read in a valid username
    invalid = True
    while invalid:
        user = input(ccolor.BOLD + "Select a user name (max 20 characters): " + ccolor.ENDC)
        if len(user) < 20 and len(user) > 0:
            invalid = False

    # There is the potential to host the server somewhere else then the localhost. Not implemented further.
    '''
    invalid = True
    while invalid:
        serv = input(ccolor.BOLD + "Enter the ip of the server: " + ccolor.ENDC)
        try:
            ipaddress.ip_address(serv)
        except BaseException:
            if serv == "localhost":
                invalid = False
            continue
        invalid = False

    invalid = True
    while invalid:
        try:
            port = int(input(ccolor.BOLD + "Enter the port of the server: " + ccolor.ENDC))
            if port < 1 or port > 65535:
                raise ValueError
        except BaseException:
            continue
        invalid = False
    '''
    serv = "localhost"
    port = 55555
    return user, serv, port

if __name__ == "__main__":
    #Read in the arguments to get the user, server and port values
    user, serv, port = read_arguments()

    #Create a new socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    #Set up connection to given server
    connected = connection_setup(user, serv, port)

    #While the client is connected
    while(connected):
        #If there is data from the server to read
        if (select([sock], [], [], 0)[0]):
            data = sock.recv(2048)
            connected = handle_msg(data, serv, port)

        #If there is data in stdin to send
        if (select([sys.stdin], [], [], 0)[0]):
            msg = input()
            send_msg(msg, serv, port)
    
    #Clean up at the end of the program
    cleanup()
    


