import socket
import time
import json
import random
import threading
import os
import select
import subprocess
import atexit
import sys
from classes import *
from strings import *
"""with open("saved_users") as file:
    data = file.read().split("\n")
saved_users = dict([a.split(chr(2500)) for a in data])
res = subprocess.getoutput("arp -an").split("\n")
ip_mac_table = {a.split(" ")[1][1:-1]:a.split(" ")[3] for a in res}"""
def clean_up():
    with open("current_port",'w') as file:
        file.write("0")
def read_file(filename,options='r'):
    try:
        with open(filename,options) as file:
            return file.read()
    except FileNotFoundError as e:
        print("FileNotFoundError when looking for file {0}".format(filename))
        return ""
def handle_command(command,user,chatroom,*args):
    if command == "username":
        oldusername = user.name
        newusername = args[0]
        for ip in users:
            if users[ip][1].name == newusername:
                user.write_message(Message(server,'Username cannot be changed to {0} because there is already a user with that username'.
                    format(newusername),chatroom))
        chatroom.write_message(server,'User "{0}" is now known as "{1}"'.\
                               format(oldusername,newusername))
        user.name = newusername

    elif command == "auth":
        with open("password") as file:
            passwords = [a.replace(" ","") for a in file.read().split("\n")]
        if args[0] in passwords:
            user.admin = True
            message = Message(server,"Authenticated as admin",chatroom)
            user.send_message(message)
            user.bad_login_attempts = 0
        else:
            user.bad_login_attempts += 1 # Just to keep track for the moment
            user.send_message(Message(server,"Bad password.",chatroom))

    elif command == "ban": # A semi-vulnerability involved in this is that users
        if not user.admin:
            user.send_message(Message(server,"Command not allowed for non-admins. Login as admin using /auth",chatroom))
            return
        username_to_ban = args[0]
        user_to_ban = None
        for ip in users:
            user = users[ip][1]
            if username_to_ban == user.name:
                user_to_ban = user

        if user_to_ban:
            user_to_ban.time_to_unban = time.time() + int(args[1])
            banned_ips[user_to_ban.ip] = time.time() + int(args[1])
        else: # unable to find username
            user.send_message(Message(server,"Unable to find user {0}".format(username_to_ban),chatroom))
    elif command == "get_mac": # implement this later
        pass
    elif command == "help":
        user.send_message([time.time(),server,help_message,"server"])

def get_resource(resource,user,postdata=""):
    resource = resource[1:] # Starts with /
    resource = resource if resource != "" else "index.html" # Static file
    if resource.split(".")[-1] in ['css','html','js']: # What's a more elegant way to say after the last dot?
        try:
            return read_file(resource)
        except FileNotFoundError:
            return read_file("404.html")

    if postdata:
        print("{0} requested {1} with post data {2}".format(user.ip,\
                                                            resource,postdata))
    else:
        print("{0} requested {1}".format(user.ip,resource))

    if resource == "chatroom_listing":
        chatroom_listing = [chatrooms[a] for a in chatrooms]
        chatroom_listing = [[a.name,len(a.users)] for a in chatroom_listing]
        return json.dumps(chatroom_listing)

    elif resource == "create_chatroom":
        chatroom_name = postdata.split("=")[1]
        print("New chatroom named {0} created by {1}".format(chatroom_name,user))
        newchatroom = Chatroom(chatroom_name,user)
        print(chatrooms)
        return read_file("chatroom.html").format(newchatroom.name) # Somehow redirect them to new chatroom?
    resource = resource[1:].split("/")
    chatroom = chatrooms[resource[1]] # Either postmessage or getmessage

    if resource[0] == "message" and postdata: # trying to do some action on a chatroom

        if postdata.startswith("/"): # attempt at command
            command = postdata[1:].split(" ")
            return handle_command(command[0],user,chatroom,*command[1:])

        print('User wrote message "{0}" to chatroom "{1}"'.format(\
            postdata,chatroom.name))
        chatroom.write_message(user,postdata)
        for ip, user in users.items():
            print("User {0} has readqueue {1}".format(ip,user[0].read_queue))
        return ''

    elif resource[0] == "message":
        chatroom_name = resource[1]
        print('User "{0}" is polling chatroom "{1}"'.format(user.ip,\
                                                            chatroom_name))
        data = user.get_readqueue(chatroom_name)
        print('User "{0}" has a readqueue "{1}"'.format(user.ip,data))
        for a in data:
            if type(a[1]) != str:
                a[1] = a[1].name # Turn user objects into names
        return json.dumps(data)
    else:
        return read_file("404.html")

def get_or_create_user(ip):
    global users
    if ip in users: # Already seen user before
        user = users[ip][0]
        print("Returning user: IP {0} and name {1}".format(ip,user.name))
        users[ip][1] = time.time() # timestamp last user appearance
        if user.unban_time > time.time():
            raise UserException("User banned")
    else: # New user
        if ip in banned_ips and (banned_ips[ip] > time.time()):
            raise UserException("User banned")
        user = User(ip)
        print("New user with IP {0} and name {1}".format(ip,user.name))
        users[ip] = [user,time.time()] # update users table
    return user

def handle_connection(clientsocket,addr): # Handles a connection from start to end. Most work is passed off to get_resource
    try:
        user = get_or_create_user(addr[0])
    except UserException: # Only happens when user is banned
        clientsocket.send(read_file('banned.html','rb'))
    last_error = 0
    while 1: # To handle keep-alive connections
        request = str(clientsocket.recv(10000),'utf-8')
        request = request.split("\r\n")
        try:
            resource = request[0].split(" ")[1]
        except IndexError:
            print("Failed to get resource from request \n{0}".\
                  format("\n".join(request)))
            if (time.time() - last_error) < 1:
                print("Time since last error with connection from {0} is {1} so breaking".format(addr[0],time.time()-last_error))
                clientsocket.close()
                break
            last_error = time.time()
            continue

        if resource == "/favicon.ico":
            with open("favicon.ico",'rb') as file:
                favicon = file.read()
            opener = bytes(image_opener.format(len(favicon)),'utf-8')
            clientsocket.send(opener + favicon)
            continue

        request_type = request[0].split(" ")[0]

        if request_type == "POST": # post request
            # Sometimes when a post request is sent for whatever reason the rest of the data will wait behind, leading to malformed requests
            # Fortunately, we can tell how long the data that was left behind was, because of the content-length header. This waits until
            # the length of the content is equal to the content-length header and then sends the post request off to be handled. This appears
            # to solve all the problems that previously existed with post requests.
            content_length = int(request[3][16:])
            postdata = request[-1]
            while len(postdata) < content_length:
                newdata = clientsocket.recv(content_length-len(postdata))
                postdata += str(newdata,'utf-8')
            print("Postdata for request of {0} by {1} was {2}".format(resource,user,postdata))
            response = get_resource(resource,user,postdata)

        elif request_type == "GET": # Standard get equest
            response = get_resource(resource,user)

        else: # not POST or GET
            response = read_file("404.html")

        opener = bytes(text_opener.format(len(response)),'utf-8')
        clientsocket.send(opener + bytes(response,'utf-8'))

banned_ips = {}
server = User("0.0.0.0","server") # Server user - sends system messages etc.

sock = socket.socket()
try:
    sock.bind(('',80))
    port = 80
except BaseException:
    while 1:
        try:
            port = random.randint(1024,2000)
            sock.bind(('',port))
            break
        except BaseException:
            print("failed to bind to port {0}".format(port))
print("Bound to port {0}".format(port))
sock.listen(10)

if sys.platform == "darwin": # We're running on a mac, so we're probably doing interactive editing and want to see the website
    subprocess.getoutput('open -a "Google Chrome" http://localhost:{0}'.format(port))

while 1: # Main event loop
    clientsocket, addr = sock.accept()
    threading.Thread(target=handle_connection,args=(clientsocket,addr)).start()