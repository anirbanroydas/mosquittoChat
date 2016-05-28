
$(document).ready(function() {
    
    // Global name of person
    var person = '';

    // Function to take the name of person until he selects a qualified name.
    // Calls repeatedly until name is selected.
    function myFunction() {
        person = prompt("What's your nickname?", "nick");
        if (person === null) {
            myFunction();
        } else if (person === '') {
            myFunction();
        } else if (person !== null) {
            $('.welcome .welcomeLine').append($('<h2>').text('Welcome, '));
            $('.welcome .welcomeLine').append($('<h3>').text(person + '.'));
            $('.welcome').append($('<code>'));
        }
    }


    // Call the myFunction just as the window loads
    $(window).bind("load", function() {
        myFunction();
    });






    // Default variables
    
    var conn = null;                            // global connection object
    var disconn = 0;                            // checks if connection was closed by server or user
    var errorconn = 0;                          // checks if connection is havving error
    var origin_clientid = null;                 // clientid if the main user sent by server
    var typing = false;                         // If person is typing presently or not
    var lastTypingTime;                         // last time the typing event was called
    var TYPING_TIMER_LENGTH = 1000;             // in ms
    var msgcount = 0;                           // currently of no use. can used in your own way.
    var colorcount = 0;                         // No of usernames ( keeps on adding even if user leaves chat)
    var personcolor = {};                       // Color set array for different usernames picked from colorset
      

    var $messages = $('.messages');             // Messages area
    var $userlist = $('.privateUserList');      // Private User list area


    // The color set for usernames
    var colorset = ['#4876FF', '#CD00CD', '#32CD32', '#FFC125',
                    '#DC143C', '#8a2be2', '#00ff7f', '#00ced1',
                    '#FF34B3', '#8B8989', '#00CD66', '#EE1289',
                    '#1E90FF', '#FFD700', '#C67171', '#33A1C9',
                    '#CD8500', '#2E8B57', '#68228B', '#00C5CD'];
    





    // Function to be called when a person clicks the Connect/Dicsonnect button
    // basically to start the connection to chat
    $('#connect').click(function() {
        console.log('insdie #connect.clic()');

        if (conn === null) {
            console.log('insdie conn === null');
        
            connect();
        } 
        else {
            console.log('insdie conn !== null');
        
            disconnect();
        }

        console.log('returning from #connect.clic()');

        return false;
    });


    // Funciton to update the UI from present status - online/offline, connect/disconnect
    function update_ui() {
        console.log('insdie update_ui()');

        var msg = '';
        if (conn === null || conn.readyState != SockJS.OPEN) {
            console.log('insdie (conn === null || conn.readyState != SockJS.OPEN)');
        
            $('#status').text('Offline').removeClass('active').addClass('inactive');
            $('#connect').text('Connect');
        } 
        else {
            console.log('insdie not (conn === null || conn.readyState != SockJS.OPEN)');
        
            $('#status').text('Online - ' + conn.protocol).removeClass('inactive').addClass('active');
            $('#connect').text('Disconnect');

        }

        console.log('returning from update_ui()');
        
    }


    // Funciton called when user disconnects using Disconnect button
    function disconnect() {
        console.log('insdie diconnect()');
        
        if (conn !== null) {
            console.log('insdieconn !== null');
        
            disconn = 1;
            conn.close();
        }

        console.log('returning from diconnect()');
        
    }


    // function called when user clicks on connect button, initated by click event
    function connect() {
        console.log('insdie connect()');
        
        // first call disconnect() to be clean any stale previous connections
        disconnect();

        // To add any other transport layers to be used if websocket is not possible
        var transports = $('#protocols input:checked').map(function() {
            return $(this).attr('id');
        }).get();

        // sockjs connection object created
        conn = new SockJS('http://' + window.location.host + '/chat', transports);

        $('.welcome code').text('Connecting...');

        // Sockjs onOpen event triggered when connection is opened and readystate is OPEN
        conn.onopen = function() {
            console.log('insdie conn.onopen()');
        
            $('.welcome code').text('Connected');
            update_ui();

            // send first msg to websocket
            sendmsg(topic=null, msg_type=null, stage='start', msg=null, clientid=null);


        };

        // sockjs onMessage event triggered whenever there is a message sent on the connection
        conn.onmessage = function(e) {
            console.log('insdie conn.onmessage()');
        
            var m = JSON.parse(e.data);

            console.log('Message received : ',m);

            var msg_type = m.msg_type; 

            if (msg_type === 'public') {
                console.log('insdie msg_type === public');
        
                handlePublicMsg(m);
            } else if (msg_type === 'status') {
                console.log('insdie msg_type === status');
        
                handleStatusMsg(m);
            }
            else if (msg_type === 'private'){
                console.log('insdie msg_type === private');
        
                handlePrivateMsg(m);
            }
        };

        // sockjs on Close event triggered whenever there is a close event either triggered by
        // server or by user itself via disconnect button -> disconnect()
        conn.onclose = function() {
            console.log('insdie conn.onclose()');
        
            if (errorconn !== 1) {
                console.log('insdie errorconn !== 1');
        
                if (disconn === 0) {
                    console.log('insdie disconn === 0');

                    serverUnavailable();
                } else {
                    console.log('insdie disconn !== 0');

                    disconn = 0;
                    closeConn();
                }
            } else if (errorconn === 1) {
                console.log('insdie errorconn === 1');

                serverError();
                errorconn = 0;
            }
            $('.welcome code').text('');
            conn = null;
            update_ui();
        };

        // sockjs Error event triggered whenver there is an error connecting to the connection or
        // error info sent by server
        conn.onerror = function() {
            console.log('insdie conn.onerror');

            errorconn = 1;
        };

        console.log('returning from connect()');
        
    }


    // Funciton to print the message received by connection,
    // this funciton doesn't print directly, rather it processes the messages and
    // calls other utility funcitons to print the final message
    function handlePublicMsg(p) {
        console.log('insdie handlePublicMsg()');

        msgcount = msgcount + 1;
        var msg_type = p['msg_type'];
        chatbox = $('.' + msg_type + ' .chatbox');
        var name = p['msg']['name'];
        var stage = p['stage'];
        var clientid = p['msg']['clientid'];
        var participants = p['msg']['participants'];
        var m = '';
        var m1 = '';
        var m2 = '';


        // Process what is the Stage of the message -> start, stop, msg, error,
        // start_typing,stop_typing, sevrver is unavailable...
        if (stage === 'start') {
            console.log('insdie stage === start');

            setUsernameColor(clientid);
            origin_clientid = clientid;
            m1 = "You joined";
            log(m1);
            updateParticipants(participants);
        } 
        else if (stage === 'new_participant'){
            console.log('insdie stage === new_participant');

            setUsernameColor(clientid);
            m1 = name + ' joned';
            log(m1);
            updateParticipants(participants);
        }
        else if (stage === 'msg') {
            console.log('insdie stage === msg');

            if (personcolor[clientid] === undefined) {
                console.log('insdie personcolor[clientid] === undefined');

                setUsernameColor(clientid);
            }
            addmsg(p);
        }
        else if (stage === 'stop') {
            console.log('insdie stage === stop');

            if (clientid === origin_clientid) {
                console.log('insdie clientid ==== origin_clientid');

                m1 = "You left";
                clearPrivateUserList();
            } 
            else {
                console.log('insdie clientid != origin_clientid');

                m1 = name + ' left';
            }
            log(m1);
            updateParticipants(participants);
        } 
        else if (stage === 'error') {
            console.log('insdie stage === error');

            m1 = 'Aw! Snap. Server no do';
            log(m1);
            updateParticipants(participants);
            clearPrivateUserList();
        } 
        else if (stage === 'unavailable') {
            console.log('insdie stage === unavailable');

            m1 = 'Oops! server unavailable';
            log(m1);
            updateParticipants(participants);
            clearPrivateUserList();
        } 
        else if (stage === 'start_typing') {
            console.log('insdie stage === start_typing');

            if (personcolor[clientid] === undefined) {
                console.log('insdie personcolor[clientid] === undefined');

                setUsernameColor(clientid);
            }
            if (clientid !== origin_clientid) {
                console.log('insdie clientid !== origin_clientid');

                addChatTyping(p);
            }
        } 
        else if (stage === 'stop_typing') {
            console.log('insdie stage === stop_typing');

            if (personcolor[clientid] === undefined) {
                console.log('insdie personcolor[clientid] === undefined');

                setUsernameColor(clientid);
            }
            if (clientid !== origin_clientid) {
                console.log('insdie clientid !== origin_clientid');

                removeChatTyping(clientid);
            }
        }
        chatbox.scrollTop(chatbox.scrollTop() + 10000);
        $('.public .groupchatTB #groupcount').text(participants);

        console.log('returning from handlePublicMsg()');
        
    }


    // function logs the start, stop, unavailable message in the center of chat screen
    function log(msg) {
        console.log('insdie log()');

        var $el = $('<li>').addClass('log').text(msg);
        var options = {};
        echomsg($el, options);

        console.log('returning from log()');
        
    }

    
    // funciton updates the present number of participants after start,stop, unavaible events
    function updateParticipants(participants) {
        console.log('insdie updateParticipants()');

        var msg = '';
        if (participants === 0) {
            console.log('insdie participants === 0');

            msg += "nobody is online";
        } 
        else if (participants === 1) {
            console.log('insdie participants === 1');

            msg += "there is 1 person online";
        } 
        else {
            console.log('insdie participants > 1');

            msg += "there are " + participants + "people online";
        }
        log(msg);

        console.log('returning from updateParticipants()');
        
    }



    // Adds a message element to the messages and scrolls to the bottom
    // elem - The element to add as a message
    // options.fade - If the element should fade-in (default = true)
    // options.prepend - If the element should prepend
    //   all other messages (default = false)
    function echomsg(elem, options) {
        console.log('insdie echomsg()');

        var $el = $(elem);
        // Setup default options
        if (!options) {
            options = {};
        }
        if (typeof options.fade === 'undefined') {
            options.fade = true;
        }
        if (typeof options.prepend === 'undefined') {
            options.prepend = false;
        }
        // Apply options
        if (options.fade) {
            $el.hide().fadeIn(100);
        }
        if (options.prepend) {
            $messages.prepend($el);
        } else {
            $messages.append($el);
        }

        // $messages[0].scrollTop = $messages[0].scrollHeight;
        
        console.log('returning from echomsg()');
        
    }


    // Adds the visual chat message to the message list
    function addmsg(data, options) {
        console.log('insdie addmsg()');

        // Don't fade the message in if there is an 'X was typing'
        var $typingMessages = getTypingMessages(data['msg']['clientid']);
        options = options || {};
        if ($typingMessages.length !== 0) {
            console.log('insdie $typingMessages.length !== 0');

            options.fade = false;
            $typingMessages.remove();
        }
        var tm = new Date().toString("hh:mm tt");
        var typingClass = data.typing ? 'typing' : '';
        var timeTypingClass = data.typing ? 'timeTyping' : '';
        var $timeinfoDiv = $('<p class="timeinfo2" />').addClass(timeTypingClass).text(tm).css('color', '#C2C2C2');
        var $usernameDiv = $('<p class="username"/>').text(data['msg']['name']).css('color', personcolor[data['msg']['clientid']]);
        var $messageBodyDiv = $('<span class="messageBody">').text(data['msg']['msg']);
        var $messageDiv = $usernameDiv.append($messageBodyDiv);
        var $messageDivFinal = $('<li class="message"/>').attr('clientid', data['msg']['clientid']).addClass(typingClass).append($timeinfoDiv, $messageDiv);
        echomsg($messageDivFinal, options);

        console.log('returning from addmsg()');
        
    }


    // Decide color of user
    function setUsernameColor(clientid) {
        console.log('insdie setUsernameColor()');

        colorcount = colorcount + 1;
        personcolor[clientid] = colorset[colorcount % 20 - 1];

        console.log('returning from setUsernameColor()');
        
    }


    // Adds the visual chat typing message
    function addChatTyping(data) {
        console.log('insdie addChatTyping()');

        data['typing'] = true;
        data['msg']['msg'] = 'is typing...';
        addmsg(data);

        console.log('returning from addChatTyping()');
        
    }


    // Removes the visual chat typing message
    function removeChatTyping(clientid) {
        console.log('insdie removeChatTyping()');

        getTypingMessages(clientid).fadeOut(function() {
            $(this).remove();
        });

        console.log('returning from removeChatTyping()');
        
    }


    // Gets the 'X is typing' messages of a user
    function getTypingMessages(clientid) {
        console.log('insdie getTypingMessages()');

        return $('.typing').filter(function(index) {
            console.log('insdie filter(function(index)) : index : ', index );

            var res = $(this).attr('clientid') === clientid;

            console.log('returning from filter(function(index))');
        
            return res;
        });


    }


    // preares msg to be sent to handlePublicMsg() when close connection initated by user
    function closeConn() {
        console.log('insdie closeConn()');

        var m = {
            'stage': 'stop',
            'msg_type' : 'public,',
             'msg':  { 
                        'name' : person,
                        'clientid' : origin_clientid,
                        'participants': 0
                    }
            };
        handlePublicMsg(m);

        console.log('returning from closeConn()');
        
    }


    // preares msg to be sent to handlePublicMsg() when close connection initated by server or server is unavailbel
    function serverUnavailable() {
        console.log('insdie serverUnavailable()');

        var m = {
            'stage': 'unavailable',
            'msg_type': 'public',
            'msg':  { 
                        'name' : person,
                        'clientid' : origin_clientid,
                        'participants': 0,
                    }
        };
        handlePublicMsg(m);

        console.log('returning from serverUnavailable()');
        
    }


    // preares msg to be sent to handlePublicMsg() when close connection initated by some error in connection
    function serverError() {
        console.log('insdie serverError()');

        var m = {
            'stage': 'error',
            'msg_type': 'public',
            'msg':  { 
                        'name' : person,
                        'clientid' : origin_clientid,
                        'participants': 0,
                    }
        };
        handlePublicMsg(m);

        console.log('returning from serverError()');
       
    }



    // triggered when msg is sent by send button
    $('#publicsendbtn').click(function() {
        console.log('insdie #publicsendbtn.click()');

        formsubmit(topic='public/msgs', msg_type='public');
        return false;
    });


    // triggered when msg is sent by send button
    $('#privatesendbtn').click(function() {
        console.log('insdie #privatesendbtn.click()');

        formsubmit(topic='private/'+origin_clientid+'/msgs', msg_type='private');
        return false;
    });


    // triggered when msg is sent by hitting Enter
    $('.publicsend').submit(function() {
        console.log('insdie #publicsend.submit()');

        formsubmit(topic='public/msgs', msg_type='public');
        return false;
    });


    // triggered when msg is sent by hitting Enter
    $('.privatesend').submit(function() {
        console.log('insdie #privatesend.submit()');

        formsubmit(topic='private/'+origin_clientid+'/msgs', msg_type='private');
        return false;
    });


    //  sends the message content to sendmsg -> which actually sends msg to the connection
    function formsubmit(topic, msg_type) {
        console.log('insdie formsubmit()');

        sendmsg(topic=topic, msg_type=msg_type, stage='stop_typing', msg=null, clientid=origin_clientid);
        typing = false;
        var v = $('#' + msg_typ + 'text').val();
        sendmsg(topic=topic, msg_type=msg_type, stage='msg', msg=v, clientid=origin_clientid);
        $('#' + msg_typ + 'text').val('');
        return false;
    }


    // triggers whenever user is Typing...
    $('.box .inpbox').on('keypress', function() {
        console.log('insdie input.on(keypress)()');

        var typ = $(this).attr('data');
        if (typ === 'public'){
            console.log('insdie typ === public');

            updateTyping(topic=typ+'/msgs', msg_typ=typ);
        }
        else
        {
            console.log('insdie type === private');

            updateTyping(topic=typ+'/'+origin_clientid+'/msgs', msg_typ=typ);
        }
        
    });


    // called to update typing status whenever user is typing event is triggered
    function updateTyping(topic, msg_typ) {
        console.log('insdie updateTyping()');

        if (conn !== null) {
            console.log('insdie conn !== null');

            if (typing === false) {
                console.log('insdie typing === false');

                typing = true;

                sendmsg(topic=topic, msg_type=msg_typ, stage='start_typing', msg=null, clientid=origin_clientid);
            }
            lastTypingTime = (new Date()).getTime();
            setTimeout(function() {
                console.log('insdie setTimeout(fuction(){})');

                var typingTimer = (new Date()).getTime();
                var timeDiff = typingTimer - lastTypingTime;
                if (timeDiff >= TYPING_TIMER_LENGTH && typing) {
                    console.log('insdie timeDiff >= TYPING_TIMER_LENGTH && typing');

                    sendmsg(topic=topic, msg_type=msg_typ, stage='stop_typing', msg=null, clientid=origin_clientid);
                    typing = false;
                }
            }, TYPING_TIMER_LENGTH);
        }

        console.log('returning from supdateTyping()');
   
    }


    // sends the actual msg after JSONifying it to the connection via conn.send()
    function sendmsg(topic, msg_type, stage, msg, clientid) {
        console.log('insdie sendmsg()');

        var newmsg = {
            'msg': { 
                'name' : person
            }
        };
        
        if (stage !== null){
            newmsg['stage'] = stage;
        }
        if (topic !== null){
            newmsg['topic'] = topic;
        }
        if (msg_type !== null){
            newmsg['msg_type'] = msg_type;
        }
        if (msg !== null){
            newmsg['msg']['msg'] = msg;
        }
        if (clientid !== null){
            newmsg['msg']['clientid'] = origin_clientid;
        }
        
        var res = JSON.stringify(newmsg);

        console.log('senign msg to websesocke conn.send : ', res);
        
        conn.send(res);

        console.log('returning from sendmsg()');
   
    }



    // function to handler status msgs
    function handleStatusMsg(m) {      
        console.log('insdie handleStatusMsg()');
        console.log('status message received : ', m);    
        
        status = m['status'];
        msg = m['msg'];

        if (status === 'online') {
            console.log('insdie status === online');

            updatePrivateUserList(m,last_seen=null);
        } 
        else {
            console.log('insdie status === offline');

            $last_seen_el = logLastSeenMsg(m['last_seen']);
            updatePrivateUserList(m, last_seen=$last_seen_el);
        }

        console.log('returning from handleStatusMsg()');
   
    }




    // function to process the status msgs and add element on html
    function updatePrivateUserList(data, last_seen) {
        console.log('insdie updatePrivateUserList()');

        var clientid = data['msg']['clientid'];
        var status = data['status'];
        var status_symbol = (status === 'online') ?  ' &#9749;' : ' &#9731;' ;

        // Remove userlist element if already present so as to create a new element and prepend at the top
        var $status_elem = getStatusElem(clientid);

        if ($status_elem.length !== 0) {
            console.log('insdie $statu_elem.length !== 0');

            $status_elem.remove();
        }

        var $span_status_symbol = $('<span class=' + '"' + status + '-symbol" >').html(status_symbol);

        var $span_status = $('<span class=' + '"' + status + '" >' ).text(status).append($span_status_symbol);
        
        var $p_elem = $('<p>').text(data['msg']['name']).append($span_status);

        var $li_elem = null;

        if (last_seen === null) {
                console.log('insdie last_seen === null');
                
                $li_elem = $('<li class="privateUser" id=' + '"' + clientid + '" >').append($p_elem) ;
        }
        else {
                console.log('insdie last_seen !== null');
                
                $li_elem = $('<li class="privateUser" id=' + '"' + clientid + '" >').append($p_elem, $(last_seen)) ;
        }


        // call printStatusMsg to actually print the created li element
        printStatusMsg($li_elem);

        console.log('returning from updatePrivateUserList()');
   
    }



    // function to return if there is an status eleme already present
    function getStatusElem(clientid) {
        console.log('insdie getStatusElem()');
                
        return $('.privateUser').filter(function(index) {
                                        console.log('inside privateUser(filter(function(index){}))');
            
                                        var res = $(this).attr('id') === clientid;

                                        console.log('returning from .privateUser(filter(function(index){}))');
   
                                        return res;
                                    });


    }





    // function to print the userlist elem on private chat box
    function printStatusMsg(elem) { 
        console.log('insdie printStatusMsg()');
                
        var $el = $(elem);

        $userlist.prepend($el);

        console.log('returning from printStatusMsg()');
   
    }





    // function to process last seen details and log it
    function logLastSeenMsg(lastseen) {
            console.log('insdie logLastSeenMsg()');
            console.log('lastseen : ', lastseen);

            var d = lastseen.date + '/' + lastseen.month + '/' + lastseen.year;
            var t = lastseen.hour + ':' + lastseen.min;
            var m = '';

            if (Date.equals( Date.parse('today'), Date.parse(d) )){
                console.log('insdie Date equals today');
            
                m = 'last seen today at '+Date.parse(t).toString('hh:mm tt');
            }
            else if (Date.equals( Date.parse('yesterday'), Date.parse(d1) )){
                console.log('insdie Date equals yesterday');
            
                m = 'last seen yesterday at '+Date.parse(t).toString('hh:mm tt');
            }
            else{
                console.log('insdie Date not equals today or yesterday');
            
                m = 'last seen on ' + Date.parse(d).toString('on ddd  dd/MM/yy') + ' at ' + Date.parse(t).toString('hh:mm tt');
            }

            // create the lastseen element
            $last_seen_el = $('<h6 class="lastseen" >').text(m);

            console.log('returning from logLastSeenMsg()');
   
            return $last_seen_el;
    }



    // clear the private user list
    function clearPrivateUserList() {
        console.log('inside clearPrivateUserList()');

        $('.privateUser').remove();

        console.log('returning from clearPrivateUserList()')
    }


    // function handle private msgs
    function handlePrivateMsg(m) {
        // Todo 
    }

});