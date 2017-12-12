class Message:
    def __init__(self,sender,text,chatroom,receiver = None,**kwargs):
        self.time = time.time()  # integer timestamp
        self.sender = sender         # User object of sender
        self.text = text         # Text content of message
        self.chatroom = chatroom # Chatroom object where message is to be sent.
        self.__dict__.update(kwargs)
    def dict(self):
        return {"time":self.time,"sender":self.sender.name,"text":self.text}
    def __repr__(self):
        return "Message sent by {0} at {1} with text {2} to chatroom {3}".format(self.sender.name,self.time,self.text,self.chatroom)
class User:
    def __init__(self,ip,name=""): # TODO: Deactivate user after inactivity?
        self.ip = ip
        if name == "":
            name = get_random_name()
        self.name = name
        self.previous_messages = []# [timestamp,user,text,chatroom name]
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
            if message.chatroom == chatroom_name:
                relevant_messages.append(message)
                toremove.append(message)
        for message in toremove:
            self.read_queue.remove(message)
        return relevant_messages
    def enter_chatroom(self,chatroom):
        self.active_chatrooms.append(chatroom)
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name
class Chatroom:
    def __init__(self,name,creator=None):
        chatrooms[name] = self # Log existence for finding later
        if creator:
            self.users = [creator]
        else:
            self.users = []
        self.name = name
        self.chatlog = [] # chatlog: [timestamp,user,text,chatroom name] etc.
        self.wyr_exclude = [] # for "would you rather" questions.
    def write_message(self,orig_user,text):
        message = Message(orig_user,text,self.name)
        self.chatlog.append(message)
        for user in self.users:
#            if user != orig_user:
            user.send_message(message)
    def announce(self,text):
        msg = Message(server,text,self.name)
        for user in self.users:
            user.send_message(msg)
    def enter_chatroom(self,new_user):
        if not new_user in self.users:
            self.users.append(new_user)
            self.announce("User {0} has entered the chat".format(new_user.name))
            new_user.enter_chatroom(self)
            self.users.append(new_user)
            context = min(10,len(self.chatlog))
            for a in range(context): # give chatroom context to user
                new_user.send_message(self.chatlog[context-a])
        else:
            new_user.send_message(Message(server,"You are already in this chat",self.name))
    def leave_chatroom(self,leaving_user):
        print("User {0} has left chatroom {1}".format(leaving_user,self.name))
        try:
            self.users.remove(leaving_user)
        except ValueError: # user not in users
            raise UserException("User not in chatroom")
        self.announce("User {0} has left the chat".format(leaving_user.name))
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name
class UserException(BaseException):
    pass
server = User("0.0.0.0","server") # Server user - sends system messages etc.
user_number = 0
chatrooms = {} # {name:room}
user_number = 0
users = {} # {ip:[timestamp,user_obj]}
import time
def get_random_name():
    global user_number
    user_number += 1
    return "User {0}".format(user_number)