
from socket import * 
import sys
import _thread
import time
import random
import struct
import os
import time

def receive_message(serverSocket):
    try:
        message, address = serverSocket.recvfrom(2048)
        return message, address
    except BlockingIOError:
        return False, False
    except ConnectionResetError:
        return False, False
    except timeout:
        return False, False
    

def vehicleInFile(vehicle, fileName):
    with open(fileName) as f:
        vehicles = f.readlines()
    
    for v in vehicles:
        if v.rstrip().split(' ')[0] == vehicle:
            return True
    return False

def dateInFile(date, fileName):
    with open(fileName) as f:
        dates = f.readlines()
    
    for d in dates:
        if fileName == 'reservations.txt' and len(d.split()) > 1:
            d = d.rstrip().split(' ')[1]
        else:
            d = d.rstrip()
        if d == date:
            return True
    return False

def processRequest(message, address, serverSocket ):
    print("New thread has started")
    message = message.decode()
    message_args = message.split(" ")
    
    message = ""
    #cars: cars file returned
    if message_args[0] == "cars" and len(message_args) == 1:
        with open('cars.txt') as f:
            message = f.read()
    
    #dates: dates file returned
    elif message_args[0] == "dates" and len(message_args) == 1:
        with open('dates.txt') as f:
            message = f.read()
    elif message_args[0] == "reservations" and len(message_args) == 1:
        with open('reservations.txt') as f:
            message = f.read()
    #check: return reservations    
    elif message_args[0] == "check" and len(message_args) == 2:
        #check if vehicle type valid
        if not vehicleInFile(message_args[1], 'cars.txt'):
            message = "Vehicle type not found."
        else:
            #return reservations with no reservation found message
            with open('reservations.txt') as f:
                reservations = f.readlines()
            for reservation in reservations:
                if message_args[1] in reservation:
                    message = message + reservation
                    
            if message == "":
                message = "No reservations found for that vehicle type."
                
    #reserve: create reservation
    elif message_args[0] == "reserve" and len(message_args) == 3:
        valid = True
        #check if vehicle type valid
        if not vehicleInFile(message_args[1], 'cars.txt'):
            message = "Vehicle type not found."
            valid = False
        #check if date is valid
        elif not dateInFile(message_args[2], 'dates.txt'):
            message = "Date not found."
            valid = False
          
        #check if vehicle is taken 
        elif vehicleInFile(message_args[1], 'reservations.txt') and dateInFile(message_args[2], 'reservations.txt'):
            message = "Vehicle not available at that time."
            valid = False
           
        #save reservation and return confirmation message
        if valid:   
            with open('reservations.txt', "a") as f:
                f.write(message_args[1] +" "+ message_args[2]+"\n")
            message = "Reservation added"
        
    #delete: delete reservation
    elif message_args[0] == "delete" and len(message_args) == 3:
        #check reservation exists
        if vehicleInFile(message_args[1], 'reservations.txt') and dateInFile(message_args[2], 'reservations.txt'):
            #delete reservation
            with open('reservations.txt') as f:
                reservations = f.readlines()
            for i in range(len(reservations)):
                if message_args[1] +" "+ message_args[2] in reservations[i]:
                    del reservations[i]
                    with open('reservations.txt', "w") as f:
                        f.writelines(reservations) 
                    message = "Reservation deleted"
                    break
        else:
            message = "Reservation not found."
    #default for non-commands or non formatted commands  
    else:
        message = "Command not recognized"
    if not(message_args[0] == "reservations" and len(message_args) == 1):
        time.sleep(random.randrange(5,11))   
    
    serverSocket.sendto(message.encode(), address)
    print("New thread has ended")
    
def main():    
    #socket initialized
    serverSocket = socket(AF_INET, SOCK_DGRAM) 
    port  = int(sys.argv[2])
    ip  = sys.argv[1]
    serverSocket.bind(('', port)) 
    serverSocket.setblocking(False)
    leader = False
    pid = os.getpid()
    print("Server ", str(pid), " started")
    last_leader_hb = 0
    election_timeout = 3
    election_ongoing = False
    election_start = 0
    server_pids = []
    election_commands = ["e", "v", "hb"]
    election_init_pid = 0
    multicast_group = ip
    group = inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, INADDR_ANY)
    serverSocket.setsockopt(IPPROTO_IP, IP_ADD_MEMBERSHIP, mreq)
    
    serverSocket.sendto("reservations".encode(), (ip,port))
    message = b"reservations"
    time.sleep(1)
    message, address = receive_message(serverSocket)
    if message != b'reservations' and message != b"" and message != False:
        with open('reservations.txt', "w") as f:
            f.write(message.decode()) 
    
    while True:
        
        if leader and time.time() -last_leader_hb > 1:
            serverSocket.sendto(("hb "+str(pid)).encode(), (multicast_group, port))
        if not leader and time.time() - last_leader_hb > 3 and not election_ongoing:
            election_ongoing = True
            election_start = time.time()
            server_pids = []
            serverSocket.sendto(("e "+str(pid)).encode(), (multicast_group, port))
        if election_ongoing and time.time() - election_start >2:
            election_ongoing = False
            leader_pid = max(server_pids)
            if leader_pid == pid:
                leader = True
            print("Election completed. Group Leader: ", leader_pid)
        #message received and split into seperate arguments
        message, address = receive_message(serverSocket)
        if message != False:
            if len(message.decode().split(" ")) > 1:
                if message.decode().split(" ")[1].isdigit() and message.decode().split(" ")[0] in election_commands:
                    if message.decode().split(" ")[0] == "e":
                        election_init_pid =  int(message.decode().split(" ")[1])
                        server_pids.append(election_init_pid)
                        election_ongoing = True
                        server_pids = []
                        print(str(pid), " calling election initiated by ", str(election_init_pid))
                        serverSocket.sendto(("v "+str(pid)).encode(), (multicast_group, port))
                    elif message.decode().split(" ")[0] == "v":
                        if election_ongoing:
                            server_pids.append( int(message.decode().split(" ")[1]))
                    elif message.decode().split(" ")[0] == "hb":
                        last_leader_hb = time.time()
            else:
                if leader:
                    _thread.start_new_thread(processRequest, (message, address, serverSocket))
        
if __name__ == "__main__":    
    main()
        

  