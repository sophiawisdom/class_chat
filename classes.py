user_number = 0
chatrooms = {} # {name:room}
user_number = 0
users = {} # {addr:[timestamp,user_obj]}

def get_random_name():
    global user_number
    user_number += 1
    return "User {0}".format(user_number)
class Message:
    def __init__(self,sender,text,chatroom,receiver = None,**kwargs):
        self.time = time.time()  # integer timestamp
        self.sender = sender         # User object of sender
        self.text = text         # Text content of message
        self.chatroom = chatroom # Chatroom object where message is to be sent.
        self.__dict__.update(kwargs)
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
            if message[3] == chatroom_name:
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
        chatrooms[name] = self # Log existence for finding later
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
class UserException(BaseException):
    pass