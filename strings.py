text_opener = """HTTP/1.1 200 OK
Content-Type: text
Connection: keep-alive
Content-Length: {0}\r\n\r\n"""
image_opener = """HTTP/1.1 200 OK
Content-Type: image/ico
Connection: keep-alive
Content-Length: {0}\r\n\r\n"""
help_message = """Available commands:
/help - display this help message
/username {newusername} - change name of user to newusername
/auth {password} - attempt to authorize user as administrator
/wyr - sends would you rather question to server
/leave - leaves chatroom

For Admins Only:
/ban user time - Ban user for specified number of seconds
"""
websocket_resp = """HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: {0}
"""