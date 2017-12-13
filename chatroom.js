var global_form;
var input_box = document.getElementById("text_input");
var unread_messages = 0;
var body = document.getElementById("body");
input_box.addEventListener('keydown', function(event) {
    if (event.key === "Enter") {
        submit_textbox();
    }
});
document.title = chatroom_name;
function handle_close(){
    // Tell server to exit us from chatroom
    jQuery.get("/leave_chatroom/" + chatroom_name)
}
function submit_textbox(){
    var message = input_box.value;
    if (message == ""){
        console.log("Submit textbox called w/o message");
        return;
    }
    var url = "/message/" + chatroom_name;
    console.log("Url is " + url + "text box value is " + message);
    jQuery.post(url,message,handle_post_response,"json");
    input_box.value = "";
    input_box.focus();
}
function handle_post_response(data){
    console.log("handle_post_response called with data" + data)
    console.log(data)
    if (data['command'] == "redirect"){
        console.log("Redirected to " + data['location']);
        window.location.replace(data['location']);
        return;
    }
}
function write_message(message){
    console.log(`wrote message ${message['text']} by ${message['sender']}`)
    element = document.getElementById("chatbox");
    text = `<span class="message"> ${message["sender"]}: ${message["text"]} </span> <br>`
    element.innerHTML += text;
}
function write_messages(messages){
    unread_messages += messages.length;
    
    messages.forEach(write_message);
}
function poll_server(){
    jQuery.get("/message/" + chatroom_name,write_messages,datatype="json");
}
function update_notifications(){
    if (document.hidden && unread_messages){
        document.title = chatroom_name + "(" + unread_messages + ")";
    }
    else {
        document.title = chatroom_name;
        unread_messages = 0;
    }
}
console.log("chatroom.js loaded")
setInterval(poll_server,200); // poll server every 1/5 second. Can be tuned.
setInterval(update_notifications,200);
