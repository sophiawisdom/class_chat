function update_chat(data){
	data.forEach(function j(chatroom){
		start = `<a href = "/chatroom/${chatroom[0]}" id="button">`
		content = `${chatroom[0]} <br>${chatroom[1]} user${chatroom[1]>1 ? 's' : ''}`
		chatroom_listing.innerHTML += (start + content + "</a>")
		console.log(chatroom);
	})
	chatroom_listing.innerHTML += '<a href="/new_chatroom.html" id="button"> Create a new chatroom </a>';
}
chatroom_listing = document.getElementById("chatroom_listing")
jQuery.get("/chatroom_listing",update_chat,datatype='json') // [[name,len(users)]...]