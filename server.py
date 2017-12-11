import socket
import time
import json
import random
import threading
import os
import select
import subprocess
import atexit
text_opener = """HTTP/1.1 200 OK
Content-Type: text
Connection: keep-alive
Content-Length: {0}\r\n\r\n"""
image_opener = """HTTP/1.1 200 OK
Content-Type: image/ico
Connection: keep-alive
Content-Length: {0}\r\n\r\n"""
"""with open("saved_users") as file:
    data = file.read().split("\n")
saved_users = dict([a.split(chr(2500)) for a in data])
res = subprocess.getoutput("arp -an").split("\n")
ip_mac_table = {a.split(" ")[1][1:-1]:a.split(" ")[3] for a in res}"""
help_message = """Available commands:
/help - display this help message
/username newusername - change name of user to newusername
/auth password - attempt to authorize user as administrator

For Admins Only:
/ban user time - Ban user for specified number of seconds

"""
users = {} # {addr:[timestamp,user_obj]}
banned_ips = {}
chatrooms = []
user_number = 0
def get_random_name():
    global user_number
    user_number += 1
    return "User {0}".format(user_number)
def clean_up():
    with open("current_port",'w') as file:
        file.write("0")
class User:
    def __init__(self,ip,name=""): # TODO: Deactivate user after inactivity?
        self.ip = ip
        if name == "":
            name = get_random_name()
        self.name = name
        self.previous_messages = []
        self.read_queue = []
        self.active_chatrooms = []
        self.admin = False
        self.unban_time = 0
    def send_message(self,message):
        self.read_queue.append(message)
    def get_readqueue(self,chatroom_name):
        relevant_messages = []
        toremove = []
        for message in self.read_queue:
            if message[3] == chatroom_name or message[3] == "server":
                relevant_messages.append(message)
                toremove.append(message)
        for message in toremove:
            self.read_queue.remove(message)
        return relevant_messages
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name
class Chatroom:
    def __init__(self,name,creator=None):
        chatrooms.append(self)
        if creator:
            self.users = [creator]
        else:
            self.users = []
        self.name = name
        self.chatlog = [] # chatlog: [timestamp,user,text,chatroom name] etc.
    def write_message(self,orig_user,text):
        message = [int(time.time()),orig_user,text,self.name]
        self.chatlog.append(message)
        for user in self.users:
#            if user != orig_user:
            user.send_message(message)
    def enter_chatroom(self,user):
        if not user in self.users:
            self.users.append(user)
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
        chatroom.write_message(server,'User "{0}" is now known as "{1}"'.\
                               format(oldusername,newusername))
        user.name = newusername
    elif command == "auth":
        with open("password") as file:
            passwords = [a.replace(" ","") for a in file.read().split("\n")]
        if args[0] in passwords:
            user.admin = True
            user.send_message([time.time(),server,"Authenticated as admin",\
                               "server"])
        else:
            user.send_messages([time.time(),server,"Bad Password","server"])
    elif command == "ban":
        if not user.admin:
            user.send_message([time.time(),server,"Not admin","server"])
            return
        username_to_ban = args[0]
        user_to_ban = None
        for ip in users:
            user = users[ip][1]
            if username_to_ban == user:
                user_to_ban = user
        if user_to_ban == None: # unable to find user
            user.send_message([time.time(),server,"User {0} not found".\
                                format(username_to_ban),"server"])
            return
        
        user_to_ban.time_to_unban = time.time() + int(args[1])
        banned_ips[user_to_ban.ip] = time.time() + int(args[1])
    elif command == "help":
        user.send_message([time.time(),server,help_message,"server"])
def get_resource(resource,user,postdata=""):
    if postdata:        
        print("{0} requested {1} with post data {2}".format(user.ip,\
                                                            resource,postdata))
    else:
        print("{0} requested {1}".format(user.ip,resource))
    static_files = os.listdir()
    resource = resource[1:]
    if resource == "":
        resource = "index.html"
    if resource in static_files and not resource.endswith(".py"):
        return read_file(resource)
    resource = resource.split("/")
    chatroom_names = [a.name for a in chatrooms]
    chatroom = chatrooms[chatroom_names.index(resource[1])]
    if resource[0] == "postmessage": # trying to do some action on a chatroom
        if postdata.startswith("/"): # attempt at command
            command = postdata[1:].split(" ")
            handle_command(command[0],user,chatroom,*command[1:])
            return ""
        print('User wrote message "{0}" to chatroom "{1}"'.format(\
            postdata,chatroom.name))
        chatroom.write_message(user,postdata)
        for ip, user in users.items():
            print("User {0} has readqueue {1}".format(ip,user[0].read_queue))
        return ''
    if resource[0] == "getmessages":
        chatroom_name = resource[1]
        print('User "{0}" is polling chatroom "{1}"'.format(user.ip,\
                                                            chatroom_name))
        data = user.get_readqueue(chatroom_name)
        print('User "{0}" has a readqueue "{1}"'.format(user.ip,data))
        for a in data:
            if type(a[1]) != str:
                a[1] = a[1].name # Turn user objects into names
        return json.dumps(data)
def handle_connection(clientsocket,addr):
    global users
    ip = addr[0]
    if ip in users:
        user = users[ip][0]
        print("Returning user: IP {0} and name {1}".format(ip,user.name))
        users[ip][1] = time.time() # timestamp last user appearance
        if user.unban_time > time.time():
            with open("banned.html") as file:
                clientsocket.send(bytes(file.read().format(user.unban_time),\
                                        'utf-8'))
            return
    else:
        if ip in banned_ips and banned_ips[ip] > time.time():
            clientsocket.send(bytes(read_file("banned.html").format(banned_ips\
                                                                    ),'utf-8'))
        user = User(ip)
        print("New user with IP {0} and name {1}".format(ip,user.name))
        try:
            mac = ip_mac_table[ip]
            user = saved_users[mac]
        except BaseException:
            pass
        users[ip] = [user,time.time()]
    test_chatroom.enter_chatroom(user)     # FOR THE MOMENT
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
                break
            last_error = time.time()
            continue
        if resource == "/favicon.ico":
            with open("favicon.ico",'rb') as file:
                favicon = file.read()
            opener = bytes(image_opener.format(len(favicon)),'utf-8')
            clientsocket.send(opener + favicon)
            continue
        if request[0].split(" ")[0] == "POST": # post request
            content_length = int(request[3][16:]) # past content-length: 
            while len(request[-1]) < content_length:
                request[-1] += str(clientsocket.recv(content_length-\
                                                     len(request[-1])),'utf-8')
            response = get_resource(resource,user,request[-1])
        else: # get request
            response = get_resource(resource,user)
        opener = bytes(text_opener.format(len(response)),'utf-8')
        clientsocket.send(opener + bytes(response,'utf-8'))
sock = socket.socket()
try:
    sock.bind(('',80))
    n = 80
except BaseException:
    while 1:
        try:
            n = random.randint(3000,8000)
            sock.bind(('',n))
            break
        except BaseException:
            print("failed to bind to port {0}".format(n))
print("Bound to port {0}".format(n))
sock.listen(10)
server = User("0.0.0.0","server")
test_chatroom = Chatroom("test_chatroom")
subprocess.getoutput('open -a "Google Chrome" http://localhost:{0}'.format(n))
while 1:
    clientsocket, addr = sock.accept()
    threading.Thread(target=handle_connection,args=(clientsocket,addr)).start()
