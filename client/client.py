from socket import *
import sys
import struct
import time
from os.path import exists

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

def cache(command, message):
    command_args = command.split(" ")
    if command == "cars":
        with open('cars.txt', "w") as f:
            f.writelines(message) 
    #dates: dates file returned
    elif command == "dates":
        with open('dates.txt', "w") as f:
            f.writelines(message) 
    elif command == "reservations":
        with open('reservations.txt', 'w') as f:
            f.writelines(message)
    #check: return reservations    
    elif command_args[0] == "check" and len(command_args) == 2:
        #check if vehicle type valid
        if exists("reservations.txt"):
            with open('reservations.txt', 'w') as f:
                f.writelines(message)
        else:
            with open('reservations.txt') as f:
                reservations = f.readlines()
                
            for i in range(len(reservations)):
                if command_args[1] in reservations[i]:
                    del reservations[i]
                    with open('reservations.txt', "w") as f:
                        f.writelines(reservations)
            with open('reservations.txt', "ab") as f:
                f.write(message)
                
    #reserve: create reservation
    elif command_args[0] == "reserve" and len(command_args) == 3:
        valid = True
        #check if vehicle type valid
        if not vehicleInFile(command_args[1], 'cars.txt'):
            message = "Vehicle type not found."
            valid = False
        #check if date is valid
        elif not dateInFile(command_args[2], 'dates.txt'):
            message = "Date not found."
            valid = False
          
        #check if vehicle is taken 
        elif vehicleInFile(command_args[1], 'reservations.txt') and dateInFile(command_args[2], 'reservations.txt'):
            message = "Vehicle not available at that time."
            valid = False
           
        #save reservation and return confirmation message
        if valid:   
            with open('reservations.txt', "a") as f:
                f.write(command_args[1] +" "+ command_args[2]+"\n")
            message = "Reservation added"
        
    #delete: delete reservation
    elif command_args[0] == "delete" and len(command_args) == 3:
        #check reservation exists
        if vehicleInFile(command_args[1], 'reservations.txt') and dateInFile(command_args[2], 'reservations.txt'):
            #delete reservation
            with open('reservations.txt') as f:
                reservations = f.readlines()
            for i in range(len(reservations)):
                if command_args[1] +" "+ command_args[2] in reservations[i]:
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

def get_cache(message):
    message_args = message.split(" ")
    
    message = ""
    #cars: cars file returned
    if message_args[0] == "cars" and len(message_args) == 1:
        if not exists("cars.txt"):
            return False
        with open('cars.txt') as f:
            message = f.read()
    
    #dates: dates file returned
    elif message_args[0] == "dates" and len(message_args) == 1:
        if not exists("dates.txt"):
            return False
        with open('dates.txt') as f:
            message = f.read()
    elif message_args[0] == "reservations" and len(message_args) == 1:
        if not exists("reservations.txt"):
            return False
        with open('reservations.txt') as f:
            message = f.read()
    #check: return reservations    
    elif message_args[0] == "check" and len(message_args) == 2:
        if not exists("cars.txt"):
            return False
        if not exists("reservations.txt"):
            return False
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
        if not exists("cars.txt"):
            return False
        if not exists("dates.txt"):
            return False
        if not exists("reservations.txt"):
            return False
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
        if not exists("reservations.txt"):
            return False
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
        
    return message
#command line arguments assigned

serverPort  = int(sys.argv[2])
ip = sys.argv[1]
multicast_group = (ip, serverPort)
# Socket initialized
clientSocket = socket(AF_INET,SOCK_DGRAM)
clientSocket.settimeout(.2)

ttl = struct.pack('b', 127)
clientSocket.setsockopt(IPPROTO_IP, IP_MULTICAST_TTL, ttl)

user_input = ""
print("Enter 'quit' to exit the program.")
#command loop
previous_commands = 0
previous_responses = []
while True:
    #command entered and sent to server without processing until quit entered
    user_input = input("Enter command: ")
    previous_commands +=1
    if user_input == "quit":
        clientSocket.close()
        print("Socket closed")
        exit(0)
    cache_response = get_cache(user_input)
    if cache_response == False:
        clientSocket.sendto(user_input.encode(),multicast_group)
        send_time = time.time()
        while (time.time()-send_time < 12):
            try:
                modifiedMessage, serverAddress = clientSocket.recvfrom(2048)
                #logic for detecting duplicates
                duplicate_found = False
                for response in previous_responses:
                    #packet is duplicate is exact same response w/ different IP or
                    #all commands already satisfied
                    if (modifiedMessage == response[0] and serverAddress != response[1]) or previous_commands == len(previous_responses):
                        duplicate_found = True
                        print("ERROR: Duplicate received")
                if not duplicate_found:
                    previous_responses.append((modifiedMessage, serverAddress))
                    cache(user_input, modifiedMessage.decode())
                    print ("(Server): ",modifiedMessage.decode())
            except timeout:
                pass
        if previous_commands != len(previous_responses):
            previous_commands -=1
            print("Request timed out.")
    else:
        previous_commands -=1
        print("(Cache): ", cache_response)
    

