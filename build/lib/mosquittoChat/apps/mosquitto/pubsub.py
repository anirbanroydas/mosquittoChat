"""
The pubsub module provides interface for the mosquitto client.

It provides classes to create mqtt clients vai paho-mqtt library to connect to mosquitto broker server, 
interact with and publish/subscribe to mosquitto via creating topics, methods to publish, subscribe/consume, 
stop consuming, start publishing, start connection, stop connection,  acknowledge delivery by publisher,
acknowledge receiving of messages by consumers and also add callbacks for various other events.

"""


import json
import logging
import base64
import os
import tornado.ioloop
import time
import paho.mqtt.client as mqtt



# EXCHANGE = 'chatexchange'
# EXCHANGE_TYPE = 'topic'
# BINDING_KEY_DEFAULT = 'public.*'
PORT = 5672

LOGGER = logging.getLogger(__name__)

# globacl tornado main ioloop object 
ioloop = tornado.ioloop.IOLoop.instance()



# defining IO events
WRITE = tornado.ioloop.IOLoop.WRITE 
READ = tornado.ioloop.IOLoop.READ 
ERROR = tornado.ioloop.IOLoop.ERROR

# no. of mqtt clinets active with mosquitto
mqttMosquittoParticipants = {'count': 0}
# list of mqtt client ever connected with msoquitto, {'clientid':'name'}
mqttClientSet = {}


# # utility temporary functions to check rather than using logging/LOGGER
# def pi(e): 
#     print '\n[MosquittoClient] Inside ' + e.upper() + '()\n'


# def pr(e):
#     print '\n[MosquittoClient] Returning from ' + e.upper() + '()\n'



class MosquittoClient(object):
    """
    This is a Mosquitto Client class that will create an interface to connect to mosquitto
    by creating mqtt clients.

    It provides methods for connecting, diconnecting, publishing, subscribing, unsubscribing and 
    also callbacks related to many different events like on_connect, on_message, on_publish, on_subscribe,
    on_unsubcribe, on_disconnect.

    """


    def __init__(self, participants=1, name='user', clientid=None, clean_session=True, userdata=None, host='localhost', port=1883, keepalive=60, bind_address='', username='guest', password='guest'):
        """
        Create a new instance of the MosquittoClient class, passing in the client
        informaation, host, port, keepalive parameters.

        :param  participants:       number of participants available presently 
        :type   participants:       int 
        :param  name:               name of client trying to connect to msoquitto 
        :type   name:               string
        :param  clientid:           unique client id for a client-broker connection
        :type   clientid:           string
        :param  clean_session:      whether to keep persistant connecion or not
        :type   clean_session:      bool
        :param  userdata:           user defined data of any type that is passed as the userdata parameter to callbacks.
                                    It may be updated at a later point with the user_data_set() function.
        :type   userdata:           user defined data (can be int, string, or any object)
        :param  host:               the hostname or IP address of the remote broker
        :type   host:               string
        :param  port:               the network port of the server host to connect to. Defaults to 1883.
                                    Note that the default port for MQTT over SSL/TLS is 8883 so if you are using tls_set() the port may need providing manually
        :type   port:               int
        :param  keepalive:          maximum period in seconds allowed between communications with the broker. 
                                    If no other messages are being exchanged, this controls the rate at which the client will send ping messages to the broker
        :type   keepalive:          int 
        :param  bind_address:       the IP address of a local network interface to bind this client to, assuming multiple interfaces exist
        :type   bind_address:       string
        :param  username:           username for authentication
        :type   username:           string 
        :param  password:           password for authentication
        :type   password:           string 

        """

        # pi('__init__')

        self._participants = participants
        self._name = name
        self._clientid = clientid or self._genid() 
        self._clean_session = clean_session 
        self._userdata = userdata 
        self._host = host 
        self._port = port 
        self._keepalive = keepalive 
        self._bind_address = bind_address 
        self._username = username
        self._password = password

        
        self._connected = False
        self._connecting = False
        self._closing = False
        self._closed = False
        self._connection = None
        self._client = None
        self.websocket = None
        self._subNo = 0
        self._sock = None
        self._ioloopClosed = False
        self._schedular = None

        # pr('__init__')




    def _genid(self):
        """ 
        Method that generates unique clientids by calling base64.urlsafe_b64encode(os.urandom(32)).replace('=', 'e').
        
        :return:        Returns a unique urlsafe id 
        :rtype:         string 

        """ 

        # pi('_genid')

        return base64.urlsafe_b64encode(os.urandom(32)).replace('=', 'e')




    def start(self):
        """
        Method to start the mosquitto client by initiating a connection  to mosquitto broker
        by using the connect method and staring the network loop.

        """

        # pi('start')

        LOGGER.info('[MosquittoClient] starting the mosquitto connection')

        self.setup_connection()
        self.setup_callbacks()
        
        # self._connection is the return code of the connection, success, failure, error. Success = 0
        self._connection = self.connect()

        # print '[MosquittoClient] self._connection : ', self._connection

        if self._connection == 0: 
            # Start paho-mqtt mosquitto Event/IO Loop
            LOGGER.info('[MosquittoClient] Startig IOLoop for client : %s ' % self)
            
            self.start_ioloop()

            # Start schedular for keeping the mqtt connection opening by chekcing keepalive, and request/response with PINGREQ/PINGRESP
            self.start_schedular()

        else:
            self._connecting = False 

            LOGGER.warning('[MosquittoClient] Connection for client :  %s  with broker Not Established ' % self)


        # pr('start')




    
    def setup_connection(self):
        """
        Method to setup the extra options like username,password, will set, tls_set etc 
        before starting the connection.

        """ 

        # pi('setup_connection')

        self._client = self.create_client()

        # setting up client username and password
        self._client.username_pw_set(self._username, self._password)
        
        # setting up will message for private messaging
        # online/offline status can be used in private messaging
        will_topic = 'private/' + self._clientid + '/status'
        
        msg = {
                'msg_type': 'status',
                'status': 'offline',
                'msg': {
                            'name': self._name,
                            'clientid': self._clientid
                        }
              }
        
        self._client.will_set(will_topic, payload=json.dumps(msg), qos=2, retain=True)

        # setting up will message for public messaging
        # self._will_topic = 'public/msgs'
        # msg = {
        #         'msg_type': 'status',
        #         'msg': {
        #                     'status': 'offline',
        #                     'name': self._name,
        #                     'clientid': self._clientid
        #                 }
        #       }  
        #
        # self._client.will_set(self._will_topic, payload=json.dumps(msg), qos=2, retain=False)


        # pr('setup_connection')





    
    def create_client(self):
        """
        Method to create the paho-mqtt Client object which will be used to connect 
        to mosquitto. 
        
        :return:        Returns a mosquitto mqtt client object 
        :rtype:         paho.mqtt.client.Client 

        """ 

        # pi('create_client')

        return mqtt.Client(client_id=self._clientid, clean_session=self._clean_session, userdata=self._userdata)





    def setup_callbacks(self):
        """
        Method to setup all callbacks related to the connection, like on_connect,
        on_disconnect, on_publish, on_subscribe, on_unsubcribe etc. 

        """ 

        # pi('setup_callbacks')

        self._client.on_connect = self.on_connect 
        self._client.on_disconnect = self.on_disconnect 
        self._client.on_publish = self.on_publish 
        self._client.on_subscribe = self.on_subscribe 
        self._client.on_unsubcribe = self.on_unsubscribe
        self._client.message_callback_add('private/+/msgs', self.on_private_message)
        self._client.message_callback_add('private/+/status', self.on_private_status)
        self._client.message_callback_add('public/msgs', self.on_public_message)


        # pr('setup_callbacks')





    def connect(self):
        """
        This method connects to Mosquitto via returning the 
        connection return code.

        When the connection is established, the on_connect callback
        will be invoked by paho-mqtt.

        :return:        Returns a mosquitto mqtt connection return code, success, failure, error, etc 
        :rtype:         int

        """

        # pi('connect')

        if self._connecting:
            LOGGER.warning('[MosquittoClient] Already connecting to RabbitMQ')
            return

        self._connecting = True

        if self._connected: 
            LOGGER.warning('[MosquittoClient] Already connected to RabbitMQ')

        else:
            LOGGER.info('[MosquittoClient] Connecting to RabbitMQ on localhost:5672, Object: %s ' % self)

            # pr('connect')

            return self._client.connect(host=self._host, port=self._port, keepalive=self._keepalive, bind_address=self._bind_address)



    


    def on_connect(self, client, userdata, flags, rc): 
        """
        This is a Callback method and is called when the broker responds to our
        connection request. 

        :param      client:     the client instance for this callback 
        :param      userdata:   the private user data as set in Client() or userdata_set() 
        :param      flags:      response flags sent by the broker 
        :type       flags:      dict
        :param      rc:         the connection result 
        :type       rc:         int

        flags is a dict that contains response flags from the broker:

        flags['session present'] - this flag is useful for clients that are using clean session
        set to 0 only. If a client with clean session=0, that reconnects to a broker that it has
        previously connected to, this flag indicates whether the broker still has the session 
        information for the client. If 1, the session still exists. 

        The value of rc indicates success or not:

        0: Connection successful 1: Connection refused - incorrect protocol version 
        2: Connection refused - invalid client identifier 3: Connection refused - server unavailable 
        4: Connection refused - bad username or password 5: Connection refused - not authorised 
        6-255: Currently unused.

        """ 

        # pi('on_connect')

        if self._connection == 0:
            self._connected = True

            LOGGER.info('[MosquittoClient] Connection for client :  %s  with broker established, Return Code : %s ' % (client, str(rc)))

            # start subscribing to topics
            self.subscribe()

        else:
            self._connecting = False 

            LOGGER.warning('[MosquittoClient] Connection for client :  %s  with broker Not Established, Return Code : %s ' % (client, str(rc)))


        # pr('on_connect')







    def start_ioloop(self):
        """
        Method to start ioloop for paho-mqtt mosquitto clients so that it can 
        process read/write events for the sockets.

        Using tornado's ioloop, since if we use any of the loop*() function provided by
        phao-mqtt library, it will either block the entire tornado thread, or it will 
        keep on creating separate thread for each client if we use loop_start() fucntion. 

        We don't want to block thread or to create so many threads unnecessarily given 
        python GIL.

        Since the separate threads calls the loop() function indefinitely, and since its doing 
        network io, its possible it may release GIL, but I haven't checked that yet, if that 
        is the case, we can very well use loop_start().Pattern

        But for now we will add handlers to tornado's ioloop().

        """ 

        # pi('start_ioloop')

        # the socket conection of the present mqtt mosquitto client object 
        self._sock = self._client.socket()

        # adding tornado iooloop handler 
        events = READ | WRITE | ERROR

        # print '[MosquittoClient] adding tornado handler now'

        if self._sock:

            # print 'self._sock is present, hence adding handler'

            ioloop.add_handler(self._sock.fileno(), self._events_handler, events)

        else: 
            LOGGER.warning('[MosquittoClient] client socket is closed already')


        # pr('start_ioloop')






    def stop_ioloop(self):
        """
        Method to stop ioloop for paho-mqtt mosquitto clients so that it cannot 
        process any more read/write events for the sockets.

        Actually the paho-mqtt mosquitto socket has been closed, so bascially this
        method removed the tornaod ioloop handler for this socket.

        """ 

        # pi('stop_ioloop')

        self._sock = self._client.socket()
        
        # # removing tornado iooloop handler
        # print '[MosquittoClient] removing tornado handler now'

        if self._sock: 

            # print 'self._sock is present, hence removing handler'

            ioloop.remove_handler(self._sock.fileno()) 

            # updating close state of ioloop 
            self._ioloopClosed = True


        else: 
            LOGGER.warning('[MosquittoClient] client socket is closed already')


        # pr('stop_ioloop')




    def _events_handler(self, fd, events):
        """
        Handle IO/Event loop events, processing them.

        :param      fd:             The file descriptor for the events
        :type       fd:             int
        :param      events:         Events from the IO/Event loop
        :type       events:         int 

        """

        # pi('_events_handler')

        self._sock = self._client.socket() 

        # print '[MosquittoClient] self._sock : ', self._sock

        if not self._sock:
            LOGGER.error('Received events on closed socket: %r', fd)
            return

        if events & WRITE:
            # LOGGER.info('Received WRITE event')

            # handler write events by calling loop_read() method of paho-mqtt client
            self._client.loop_write()

        if events & READ:
            # LOGGER.info('Received READ event')
            
            # handler write events by calling loop_read() method of paho-mqtt client
            self._client.loop_read() 

        

        if events & ERROR:
            LOGGER.error('Error event for socket : %s and client : %s ' % (self._sock, self._client))


        # pr('_events_handler')






    def start_schedular(self):
        """
        This method calls Tornado's PeriodicCallback to schedule a callback every few seconds,
        which calls paho mqtt client's loop_misc() function which keeps the connection open by
        checking for keepalive value and by keep sending pingreq and pingresp to moqsuitto broker.

        """ 

        # pi('start_schedular')

        LOGGER.info('[MosquittoClient] Starting Scheduler for client : %s ' % self)

        # torndao ioloop shcedular 
        self._schedular = tornado.ioloop.PeriodicCallback(callback=self._client.loop_misc, callback_time=10000, io_loop=ioloop)

        # start the schedular
        self._schedular.start()

        # pr('start_schedular')



    def stop_schedular(self):
        """
        This method calls stops the tornado's periodicCallback Schedular loop.

        """ 

        # pi('stop_schedular')

        LOGGER.info('[MosquittoClient] Stoping Scheduler for client : %s ' % self)

        # stop the schedular
        self._schedular.stop()

        # pr('stop_schedular')






    def disconnect(self):   
        """
        Method to disconnect the mqqt connection with mosquitto broker.

        on_disconnect callback is called as a result of this method call. 

        """ 

        # pi('disconnect')

        if self._closing: 
            LOGGER.warning('[MosquittoClient] Connection for client :  %s  already disconnecting..' % self)

        else:
            self._closing = True 

            if self._closed:
                LOGGER.warning('[MosquittoClient] Connection for client :  %s  already disconnected ' % self)

            else:
                self._client.disconnect() 


        # pr('disconnect')



    



    def on_disconnect(self, client, userdata, rc):
        """
        This is a Callback method and is called when the client disconnects from
        the broker.

        """  

        # pi('on_disconnect')

        LOGGER.info('[MosquittoClient] Connection for client :  %s  with broker cleanly disconnected with return code : %s ' % (client, str(rc)))

        self._connecting = False 
        self._connected = False 
        self._closing = True
        self._closed = True

        
        # stopping ioloop - actually mqtt ioloop stopped, not the real torando ioloop, 
        # just removing handler from tornado ioloop
        self.stop_ioloop() 

        # stoppig shechular 
        self.stop_schedular()

        if self._ioloopClosed:
            self._sock = None


        # pr('on_disconnect')




    

    def subscribe(self, topic_list=None):
        """
        This method sets up the mqtt client to start subscribing to topics by accepting a list of tuples
        of topic and qos pairs.

        The on_subscribe method is called as a callback if subscribing is succesfull or if it unsuccessfull, the broker
        returng the suback frame. 

        :param      :topic_list:    a tuple of (topic, qos), or, a list of tuple of format (topic, qos). 
        :type       :topic_list:    list or tuple 


        """

        # pi('subscribe')

        LOGGER.info('[MosquittoClient] clinet : %s started Subscribing ' % self)
 
        # add clientid:name key-value pair in the global mqttClientSet
        if self._clientid not in mqttClientSet:

            # print '[MosquittoClient] inside self._clientid not in mqttClientSet'

            mqttClientSet[self._clientid] = self._name 

        if topic_list is None:

            # print '[MosquittoClient] insdie topic_list is None'

            topic_list = [] 
            topic = ("public/msgs", 2)
            topic_list.append(topic)

            if self._subNo == 0:

                # print '[MosquittoClient] inside self._subNo === 0'

                for cid in mqttClientSet.keys():
                    topics = ("private/" + cid + "/status", 2)
                    topic_list.append(topics)
        

        LOGGER.info('[MosquittoClient] Subscribing to topic_list : %s ' % str(topic_list))

        self._client.subscribe(topic_list)
       
        # pr('subscribe')


        





    def on_subscribe(self, client, userdata, mid, granted_qos): 
        """
        This is a Callback method and is called when the broker responds to a subscribe request.

        The mid variable matches the mid variable returned from the corresponding subscribe() call.
        The granted_qos variable is a list of integers that give the QoS level the broker has granted
        for each of the different subscription requests. 

        :param      client:         the client which subscribed which triggered this callback 
        :param      userdata:       the userdata associated with the client during its creation 
        :param      mid:            the message id value returned by the broker 
        :type       mid:            int 
        :param      granted_qos:    list of integers that give the QoS level the broker has granted 
                                    for each of the different subscription requests 
        :type       granted_qos:    list

        """

        # pi('on_subscribe')

        LOGGER.info('[MosquittoClient] client :  %s  subscribed to topic succesfully with message id : %s ' % (client, str(mid)))

        # first subscribtion or later
        self._subNo = self._subNo + 1

        if self._subNo == 1:
            # LOGGER.info('MosquittoClient] First subsrbition for client : %s ', client)
            
            # get current mqtt mosuitto clients subcribing on some topics by calling addnewmqttosquittoclietns
            self._participants = self.addNewMqttMosquittoClient()
            
            # creating first message to be sent to associated websocket
            firstMsg = {
                            'msg_type': 'public',
                            'stage': 'start',
                            'msg': {
                                        'clientid': self._clientid, 
                                        'name': self._name,
                                        'participants': self._participants,
                                    },
                            'clientlist': mqttClientSet
                        }
            
            # calling method to send message to associated websocket
            LOGGER.info('[MosquittoClient] mosquitto is now ready for publish/subscribe. \nSending first msg to websocket...')
            
            self.sendMsgToWebsocket(firstMsg)

            # publishing status to its own private status topic, so that whoever start
            # subcribing to its status, get the status info
            statusmsg = {
                            'msg_type': 'status',
                            'status': 'online',
                            'msg': {
                                        'name': self._name,
                                        'clientid': self._clientid
                                    }
                        }

            self.publish(topic='private/' + self._clientid + '/status', msg=statusmsg, qos=2, retain=True)

            # publishing the new mqqt client info to everybody else subscribed to public topic
            # and hence they can choose to subscribe to the new client too.
            
            # creating new msg to be sent to the subcribing clients
            newmsg = {
                        'msg_type': 'public',
                        'stage': 'new_participant',
                        'msg': {
                                    'clientid': self._clientid, 
                                    'name': self._name,
                                    'participants': self._participants
                                }
                    }

            self.publish(topic='public/msgs', msg=newmsg, qos=2, retain=False)



        # pr('on_subscribe')




    

    def addNewMqttMosquittoClient(self):
        """
        Method called after new mqtt connection is established and the client has started subsribing to 
        atleast some topics, called by on_subscribe callback. 

        """ 

        # pi('addNewMqttMosquittoClient')

        mqttMosquittoParticipants['count'] = mqttMosquittoParticipants['count'] + 1

        # print '[MosquittoClient] mqttMosquittoParticipants : ', mqttMosquittoParticipants['count']
        
        return mqttMosquittoParticipants['count']




    def sendMsgToWebsocket(self, msg): 
        """
        Method to send message to associated websocket. 

        :param      msg:        the message to be sent to the websocket 
        :type       msg:        string, unicode or json encoded string or a dict

        """ 

        # pi('sendMsgToWebsocket')

        # LOGGER.info('[MosquittoClient] mosquitto is sending msg to associated webscoket')

        if isinstance(msg, str) or isinstance(msg, unicode):
            payload = msg 
        else: 
            payload = json.dumps(msg)
        
        self.websocket.send(payload)   


        # pr('sendMsgToWebsocket')






    def unsubscribe(self, topic_list=None):
        """
        This method sets up the mqtt client to unsubscribe to topics by accepting topics as string or list.

        The on_unsubscribe method is called as a callback if unsubscribing is succesfull or if it unsuccessfull. 

        :param      topic_list:        The topics to be unsubscribed from 
        :type       topic_list:         list of strings(topics)

        """

        # pi('unsubscribe')

        LOGGER.info('[MosquittoClient] clinet : %s started Unsubscribing ' % self)

        if topic_list is None:
            topic_list = []
            topic = "public/msgs"
            topic_list.append(topic)
            for cid in mqttClientSet.keys():
                    topics = "private/" + cid + "/status"
                    topic_list.append(topics)
        
        self._client.unsubscribe(topic_list)
        

        # pr('unsubscribe')
    
    


    def on_unsubscribe(self, client, userdata, mid): 
        """
        This is a Callback method and is called when the broker responds to an 
        unsubscribe request. The mid variable matches the mid variable returned from t
        he corresponding unsubscribe() call. 

        :param      client:             the client which initiated unsubscribed
        :param      userdata:           the userdata associated with the client 
        :param      mid:                the message id value sent by the broker of the unsubscribe call. 
        :type       mid:                int 

        """

        # pi('on_unsubscribe')

        LOGGER.info('[MosquittoClient] client :  %s  unsubscribed to topic succesfully with message id : %s ' % (client, str(mid)))

        # pr('on_unsubscribe')

        




    def publish(self, topic, msg=None, qos=2, retain=False):
        """
        If the class is not stopping, publish a message to MosquittoClient.

        on_publish callback is called after broker confirms the published message.
        
        :param  topic:  The topic the message is to published to
        :type   topic:  string 
        :param  msg:    Message to be published to broker
        :type   msg:    string 
        :param  qos:    the qos of publishing message 
        :type   qos:    int (0, 1 or 2) 
        :param  retain: Should the message be retained or not 
        :type   retain: bool

        """

        # pi('publish')

        # LOGGER.info('[MosquittoClient] Publishing message')

        # converting message to json, to pass the message(dict) in acceptable format (string)
        if isinstance(msg, str) or isinstance(msg, unicode):
            payload = msg
        else:
            payload = json.dumps(msg, ensure_ascii=False)

        self._client.publish(topic=topic, payload=payload, qos=qos, retain=retain)


        # pr('publish')







    def on_publish(self, client, userdata, mid): 
        """
        This is a Callback method and is called when a message that was to be sent
        using the publish() call has completed transmission to the broker. For messages
        with QoS levels 1 and 2, this means that the appropriate handshakes have completed.

        For QoS 0, this simply means that the message has left the client. 
        The mid variable matches the mid variable returned from the corresponding publish()
        call, to allow outgoing messages to be tracked.

        This callback is important because even if the publish() call returns success,
        it does not always mean that the message has been sent.

        :param      client:         the client who initiated the publish method 
        :param      userdata:       the userdata associated with the client during its creation 
        :param      mid:            the message id sent by the broker 
        :type       mid:            int 

        """

        # pi('on_publish')

        # LOGGER.info('[MosquittoClient] client :  %s  published message succesfully with message id : %s ' % (client, str(mid)))

        pass

        # pr('on_publish')


   


    

    def on_private_message(self, client, userdata, msg): 
        """
        This is a Callback method and is called  when a message has been received on a topic
        [private/cientid/msgs] that the client subscribes to. 

        :param      client:         the client who initiated the publish method 
        :param      userdata:       the userdata associated with the client during its creation 
        :param      msg:            the message sent by the broker 
        :type       mid:            string or json encoded string 

        """

        # // Todo
        pass


    
    

    def on_private_status(self, client, userdata, msg): 
        """
        This is a Callback method and is called  when a message has been received on a topic
        [private/cientid/status] that the client subscribes to.

        :param      client:         the client who initiated the publish method 
        :param      userdata:       the userdata associated with the client during its creation 
        :param      msg:            the message sent by the broker 
        :type       mid:            string or json encoded string 

        """

        # pi('on_private_status')

        # LOGGER.info('[MosquittoClient] Received message with mid : %s from topic : %s with qos :  %s and retain = %s ' % (str(msg.mid), msg.topic, str(msg.qos), str(msg.retain)))
        
        json_decoded_body = json.loads(msg.payload)

        if json_decoded_body['status'] == 'offline':

            # print '[MosquittoClient] received status === offline'

            if json_decoded_body['msg']['clientid'] == self._clientid:

                # print 'received offline status on self._clientid, hence stopping mqtt client'

                # since status message has been sent, its safe to close the mqtt mosquitto connection now
                self.stop() 

                # return from this function so as to avoid send the status message to the correspongin 
                # websocket since its already closed.
                

                # pr('on_private_status')

                return
            
            last_seen = time.localtime()
            json_decoded_body['last_seen'] = {
                                                'date': last_seen.tm_mday,
                                                'month': last_seen.tm_mon,
                                                'year': last_seen.tm_year,
                                                'hour': last_seen.tm_hour,
                                                'min': last_seen.tm_min
                                            } 
        
        # LOGGER.info('[MosquittoClient] sending the message to corresponsding websoket: %s ' % self.websocket)

        # print '[MosquittoClient] msg to be sent : ', json_decoded_body

        self.sendMsgToWebsocket(json_decoded_body)


        # pr('on_private_status')




    
    
    def on_public_message(self, client, userdata, msg): 
        """
        This is a Callback method and is called  when a message has been received on a topic
        [public/msgs] that the client subscribes to.

        :param      client:         the client who initiated the publish method 
        :param      userdata:       the userdata associated with the client during its creation 
        :param      msg:            the message sent by the broker 
        :type       mid:            string or json encoded string 

        """

        # pi('on_public_message')

        # LOGGER.info('[MosquittoClient] Received message with mid : %s from topic : %s with qos :  %s and retain = %s ' % (str(msg.mid), msg.topic, str(msg.qos), str(msg.retain)))

        json_decoded_body = json.loads(msg.payload)
        stage = json_decoded_body['stage']

        if stage == 'new_participant':
            
            # print '[MosquittoClient] Received stage == new_participant'

            if json_decoded_body['msg']['clientid'] != self._clientid: 

                # print '[MosquittoClient] received stage == new_participant with != self._clientid, thus subscribing to its private status'
                
                topic_list = ('private/' + str(json_decoded_body['msg']['clientid']) + '/status', 2)
                
                # print 'MosquittoClient] topic_list to be sent : ', topic_list
                
                # subscribe the new participant's status topic
                self.subscribe(topic_list=topic_list)
            
            else:


                # pr('on_public_message')

                return



        if stage == 'stop' and self._clientid == json_decoded_body['msg']['clientid']:

            # print '[MosquittoClient] received stage == stop with == self._clientid, thus sending offline status to subscribers'
                
            # LOGGER.info('[MosquittoClient] skipping sending message to websocket since webscoket is closed.')
            # LOGGER.info('[MosquittoClient] initating closing of rabbitmq Client Connection...')

            # avoid sending the message to the corresponding websocket, since its already cloesed. 
            # rather sending the offline status message to the subscribers of its private/status topic
            self.send_offline_status()

        else:
            # print '[MosquittoClient] received stage != new_participant and != self._clientid, thus sendimg msg to corresponding websocket'
                
            # LOGGER.info('[MosquittoClient] sending the message to corresponsding websoket: %s ' % self.websocket)

            self.sendMsgToWebsocket(json_decoded_body)


        # pr('on_public_message')




    

    def send_offline_status(self): 
        """
        Method is called when the mqtt client's corresponding websocket is closed.
        This method will send the subcribing clients to its private status an offline status
        message.

        """ 

        # pi('send_offline_status')

        # removing the subscribed but now unsubscribed and disconected mqtt mosqitto client 
        self._participants = self.delMqttMosquittoClient()

        # publishing status message to private/clientid/status topic
        statusmsg = {
                            'msg_type': 'status',
                            'status': 'offline',
                            'msg': {
                                        'name': self._name,
                                        'clientid': self._clientid
                                    }
                        }

        self.publish(topic='private/' + self._clientid + '/status', msg=statusmsg, qos=2, retain=True)


        # pr('send_offline_status')






    def delMqttMosquittoClient(self):
        """ Method called after an mqtt clinet unsubsribes to 
        atleast some topics, called by on_subscribe callback. 

        :return:    Returns update mqqt clients active 
        :rtype:     dict with update count 

        """ 

        # pi('delMqttMosquittoClient')

        mqttMosquittoParticipants['count'] = mqttMosquittoParticipants['count'] - 1

        # print '[MosquittoClient] mqttMosquittoParticipants : ', mqttMosquittoParticipants['count']
        
        return mqttMosquittoParticipants['count']




    

    def stop(self):
        """
        Cleanly shutdown the connection to Mosquitto by disconnecting the mqtt client.

        When mosquitto confirms disconection, on_disconnect callback will be called.

        """

        # pi('stop')

        LOGGER.info('[MosquittoClient] Stopping MosquittoClient object... : %s ' % self)

        self.disconnect()

        # pr('stop')


    






