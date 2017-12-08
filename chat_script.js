var chatroomname = "test_chatroom"; // Do not hardcode in future
var global_form;
var input_box = document.getElementById("text_input");
var unread_messages = 0;
var body = document.getElementById("body");
input_box.addEventListener('keydown', function(event) {
    if (event.key === "Enter") {
        submit_textbox();
    }
});
document.title = chatroomname;
function submit_textbox(){
    var val = input_box.value;
    if (val == ""){
        console.log("Submit textbox called w/o message");
        return;
    }
    var url = "/postmessage/" + chatroomname;
    console.log("Url is " + url + "text box value is " + val);
    jQuery.post(url,val);
    input_box.value = "";
    input_box.focus();
}
function write_message(message){
    console.log("write_message was called with message " + message);
    element = document.getElementById("chatbox");
    text = `<tr class="message"> <td> ${message[1]} </td> <td> ${message[2]} </td> </tr>`;
    element.innerHTML += text;
}
function write_messages(messages){
    unread_messages += messages.length;
    
    messages.forEach(write_message);
}
function poll_server(){
    jQuery.get("/getmessages/" + chatroomname,write_messages,datatype="json");
}
function update_notifications(){
    if (document.hidden && unread_messages){
        document.title = chatroomname + "(" + unread_messages + ")";
    }
    else {
        document.title = chatroomname;
        unread_messages = 0;
    }
}
setInterval(poll_server,500); // poll server every 1/2 second. Can be tuned.
setInterval(update_notifications,200);
