#! /usr/bin/python3.6
import socket
import threading
import time
import random
import interpret
import sys
import atexit
run_server = 1
text_opener = b"""HTTP/1.1 200 OK
Content-Type: text
Connection: keep-alive\r\n\r\n""" # tell other side we're A-Ok (200)
image_opener = b"""HTTP/1.1 200 OK
Content-Type: image
Connection: keep-alive\r\n\r\n""" # necessary?
spl_char = chr(5000)
file = open("responses.txt")
responses = file.read()
file.close()
# responses.txt format:
# questionᎈchoice_1:choice_2\n
# ...
responses = responses.split("\n")
responses = [a.split(spl_char) for a in responses]
while 1:
    try:
        responses.remove([''])
    except BaseException:
        break
for place, value in enumerate(responses):
    s = value[1].split(":")
    s = [int(s[0]),int(s[1])]
    responses[place][1] = s
responses = {a[0]:a[1] for a in responses} # {q:[choice_1,choice_2],...}
sock = socket.socket()
r = random.randint(2000,7000)
if len(sys.argv)==2:
    r = int(sys.argv[1]) # for specifically requesting to run @ 80
sock.bind(('',r))
print("Now listening for incoming connections on port {0}".format(r))
sock.listen(10)
spec_char = "썐"
all_questions = []
all_questions.extend(interpret.database['Friends'])
all_questions.extend(interpret.database['Family'])
all_questions.extend(interpret.database['Discussion'])
hashmap = {hash(a):a for a in all_questions}
excl = {} # exclude questions dict. For making sure same questions don't get
# asked
def save_responses(): # saves response data in responses.txt For some reason blanks.
    file = open("responses.txt",'w')
    m = list(responses.keys())
    for i in m:
        r = responses[i]
        file.write(chr(5000).join([i,":".join([str(r[0]),str(r[1])])]) + "\n")
    file.close()
def html_to_question(html):
    # turns html header and turns it into raw
    html = html.replace("+"," ")
    html = html.replace("%3F","?")
    return html
#atexit.register(save_responses) # save_responses appears to blank responses
def read_page(page):
    with open(page,'rb') as file:
        return file.read()
def get_question(loc):
    prefs = [0,0,0]
    loc = loc.split('?')[1].split("&")
    if loc == ['']: # no preferences checked
        return text_opener + read_page("page.html")
    for i in loc:
        s = i.split("=")
        if s[0].startswith("response"): # response_q=rating
           s[0] = s[0].split("_")[1]
           s[1] = int(s[1])
           s[1] -= 1
           s[0] = hashmap[int(s[0])]
           responses[s[0]][s[1]] += 1 # hopefully works.
           continue
        prefs[int(s[0])] = int(s[1])
    try:
        t_recv, exclude = excl[addr[0]]
        if time.time()-t_recv> (60*60): # 1 hour
            raise KeyError # Reset timer
    except KeyError: # current IP not on record
        excl[addr[0]] = [time.time(),[]] # add to record
        exclude = []
    question = interpret.get_question(prefs,exclude) # Get q from database
    excl[addr[0]][1].append(question) # add to exclude for this ip
    questions = question.replace("’","'") # can cause weird looking letters
    res = str(read_page("page_renew.html"),'utf-8')
    prefs = ["checked" if a else "" for a in prefs]
    return bytes(res.format(question,hash(question),*prefs),'utf-8')
#static = {"/":text_opener + read_page("page.html"),"/favicon.ico",
def handle_conn(clientsocket, addr):
    t = time.time()
    res = clientsocket.recv(10000)
    res = res.split(b"\r\n")
    r = res[0].split(b' ')
    try:
        loc = str(r[1],'utf-8') # what section is desired
    except IndexError:
        print("Incoming connection from {0}:{1} gave no information. Aborting."\
              .format(addr[0],addr[1]))
        clientsocket.close()
        return
    print("Incoming conn from {0}:{1}. Wants page {2}".format(addr[0],addr[1],loc))
    if loc == "/": # main page
        clientsocket.send(text_opener + read_page("page.html"))
    elif loc == "/favicon.ico":
        clientsocket.send(text_opener + read_page("favicon.ico"))
    elif loc.startswith("/get_question"):
        clientsocket.send(text_opener + get_question(loc))
    elif loc.startswith("/dump_questions"):
        clientsocket.send(text_opener + read_page("questions.txt"))
    else:
        clientsocket.send(text_opener + b"I'm sorry, but that page does not appear to be on this website. Please try again.")
    clientsocket.close() # Tells server we won't talk anymore
    # if you remove this, page will be weird. Maybe it's trying websockets?
    return
while run_server:
    clientsocket, addr = sock.accept()
    threading.Thread(target=handle_conn,args=(clientsocket,addr)).start()
