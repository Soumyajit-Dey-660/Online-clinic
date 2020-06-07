document.addEventListener('DOMContentLoaded', () => {

    // Connect to websocket
    var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

    // Retrieve username
    const username = document.querySelector('#get-username').innerHTML;

    // Set default room
    let room = "Lounge"
    joinRoom("Lounge");


    // Send messages
    document.querySelector('#send_message').onclick = () => {
        socket.emit('incoming-msg', {'msg': document.querySelector('#user_message').value,
            'username': username, 'room': room});

        document.querySelector('#user_message').value = '';
    };

    // Display all incoming messages
    socket.on('message', data => {

        // Display current message
        if (data.msg) {
            const p = document.createElement('p');
            const span_username = document.createElement('span');
            const span_timestamp = document.createElement('span');
            const br = document.createElement('br');
            // Display user's own message
            if (data.username == username) {
                    p.setAttribute("class", "my-msg");

                    // Username
                    span_username.setAttribute("class", "my-username");
                    span_username.innerText = data.username;

                    // Timestamp
                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = data.time_stamp;

                    // HTML to append
                    p.innerHTML += span_username.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML

                    //Append
                    document.querySelector('#display-message-section').append(p);
            }
            // Display other users' messages
            else if (typeof data.username !== 'undefined') {
                p.setAttribute("class", "others-msg");

                // Username
                span_username.setAttribute("class", "other-username");
                span_username.innerText = data.username;

                // Timestamp
                span_timestamp.setAttribute("class", "timestamp");
                span_timestamp.innerText = data.time_stamp;

                // HTML to append
                p.innerHTML += span_username.outerHTML + br.outerHTML + data.msg + br.outerHTML + span_timestamp.outerHTML;

                //Append
                document.querySelector('#display-message-section').append(p);
                
            }
            // Display system message
            else {
                printSysMsg(data.msg);
            }


        }
        scrollDownChatWindow();
    });


    socket.on('chat-history', data => {
        //Show previous messages in message area
        if(data.messages){
            for (var i = 0; i < data.messages.length; i++){
            const p = document.createElement('p');
            const span_username = document.createElement('span');
            const span_timestamp = document.createElement('span');
            const br = document.createElement('br');
                var counter = data.messages[i];
                // Display user's own message
                if (counter.username == username) {
                        p.setAttribute("class", "my-msg");
                        p.setAttribute("style", "margin-left:7em;margin-right:1em;padding: 0.5em 0.5em 0.5em 1em;border-radius: 5px;border-color: #206ED2;border-width: 1px;border-style: solid;")
                        // Username
                        span_username.setAttribute("class", "my-username");
                        span_username.innerText = counter.username;

                        // Timestamp
                        span_timestamp.setAttribute("class", "timestamp");
                        span_timestamp.innerText = counter.time;

                        // HTML to append
                        p.innerHTML += span_username.outerHTML + br.outerHTML + counter.text + br.outerHTML + span_timestamp.outerHTML + br.outerHTML;

                        //Append
                        document.querySelector('#display-message-section').append(p);
                }
                // Display other users' messages
                else if (typeof counter.username !== 'undefined') {
                    p.setAttribute("class", "others-msg");
                    p.setAttribute("style", "margin-right:7em;margin-left: 1em;padding: 0.5em 0.5em 0.5em 1em;border-radius: 5px;border-color: grey;border-width: 0.5px;border-style: solid;background-color: #C2DBFB;");
                    // Username
                    span_username.setAttribute("class", "other-username");
                    span_username.innerText = counter.username;

                    // Timestamp
                    span_timestamp.setAttribute("class", "timestamp");
                    span_timestamp.innerText = counter.time;

                    // HTML to append
                    p.innerHTML += span_username.outerHTML + br.outerHTML + counter.text + br.outerHTML + span_timestamp.outerHTML +br.outerHTML;

                    //Append
                    document.querySelector('#display-message-section').append(p);
                }
            }
    
        }
        scrollDownChatWindow();
    });



    // Select a room
    document.querySelectorAll('.select-room').forEach(p => {
        p.onclick = () => {
            let newRoom = p.innerHTML;
            // Check if user already in the room
            if (newRoom === room) {
                msg = `You are already in ${room} room.`;
                printSysMsg(msg);
            } else {
                leaveRoom(room);
                joinRoom(newRoom);
                room = newRoom;
                
            }
        };
    });

    // Logout from chat
    document.querySelector("#logout-btn").onclick = () => {
        leaveRoom(room);
    };

    // Trigger 'leave' event if user was previously on a room
    function leaveRoom(room) {
        socket.emit('leave', {'username': username, 'room': room});

        document.querySelectorAll('.select-room').forEach(p => {
            p.style.color = "black";
        });
    }

    // Trigger 'join' event
    function joinRoom(room) {

        // Join room
        socket.emit('join', {'username': username, 'room': room});
        // Highlight selected room
        document.querySelector('#' + CSS.escape(room)).style.color = "#ffc107";
        document.querySelector('#' + CSS.escape(room)).style.backgroundColor = "white";

        
        document.querySelector('#display-message-section').innerHTML = '';
        // Autofocus on text box
        document.querySelector("#user_message").focus();
        socket.emit('chat', {'username': username ,'room': room});
    }

    // Scroll chat window down
    function scrollDownChatWindow() {
        const chatWindow = document.querySelector("#display-message-section");
        chatWindow.scrollTop = chatWindow.scrollHeight;
    }

    // Print system messages
    function printSysMsg(msg) {
        const p = document.createElement('p');
        p.setAttribute("class", "system-msg");
        p.innerHTML = msg;
        document.querySelector('#display-message-section').append(p);
        scrollDownChatWindow()

        // Autofocus on text box
        document.querySelector("#user_message").focus();
    }
});
