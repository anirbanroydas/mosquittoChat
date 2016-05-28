"""
This is the main view module which manages main tornado connections. This module
provides request handlers for managing simple HTTP requests as well as Websocket requests.

Although the websocket requests are actually sockJs requests which follows the sockjs protcol, thus it
provide interface to sockjs connection handlers behind the scene.
"""




import tornado.web
import tornado.escape
import logging



from sockjs.tornado import SockJSConnection
from mosquittoChat.apps.mosquitto.pubsub import MosquittoClient


LOGGER = logging.getLogger(__name__)



# Handles the general HTTP connections
class IndexHandler(tornado.web.RequestHandler):
    """This handler is a basic regular HTTP handler to serve the chatroom page.

    """

    def get(self):
        """
        This method is called when a client does a simple GET request,
        all other HTTP requests like POST, PUT, DELETE, etc are ignored.

        :return: Returns the rendered main requested page, in this case its the chat page, index.html

        """

        LOGGER.info('[IndexHandler] HTTP connection opened')

        self.render('index.html')

        LOGGER.info('[IndexHandler] index.html served')



# set of websocket connections
websocketParticipants = set()
# no. of mqtt clients
mqttClients = set()



# Handler for Websocket Connections or Sockjs Connections
class ChatWebsocketHandler(SockJSConnection):
    """ Websocket Handler implementing the sockjs Connection Class which will
    handle the websocket/sockjs connections.
    """

    def on_open(self, info):
        """
        This method is called when a websocket/sockjs connection is opened for the first time.
        
        :param      self:  The object
        :param      info:  The information
        
        :return:    It returns the websocket object

        """

        LOGGER.info('[ChatWebsocketHandler] Websocket connecition opened: %s ' % self)

        # adding new websocket connection to global websocketParcticipants set
        websocketParticipants.add(self)




    def on_message(self, message):
        """
        This method is called when a message is received via the websocket/sockjs connection
        created initially.
        
        :param      self:     The object
        :param      message:  The message received via the connection.
        :type       message: json string

        """

        # LOGGER.info('[ChatWebsocketHandler] message received on Websocket: %s ' % self)

        res = tornado.escape.json_decode(message)

        # print '[ChatWebsocketHandler] received msg : ', res

        stage = res['stage']
        
        if stage == 'start':
            LOGGER.info('[ChatWebsocketHandler] Message Stage : START')

            # get first-msg contents
            name = res['msg']['name']

            # Initialize new mqtt mosquitto client object for this websocket.
            # call with default values, clean_session=True if using for public messaging,
            # for private msgs feature, clean_session=False has to be initiated by 
            # self._mqtt_client = MosquittoClient(clean_session=False)
            self.mqtt_client = MosquittoClient(name=name, clean_session=False)
            
            # Assign websocket object to a Pika client object attribute.
            self.mqtt_client.websocket = self
            
            # connect to Mosquitto
            self.mqtt_client.start()


        else: 
            msg_type = res['msg_type']
            topic = res['topic']

            # LOGGER.info('[ChatWebsocketHandler] Publishing the received message to Mosquitto')

            if msg_type == 'public':
                self.mqtt_client.publish(topic=topic, msg=res, qos=2, retain=False)
            elif msg_type == 'private': 
                self.mqtt_client.publish(topic=topic, msg=res, qos=2, retain=True)



    
    def on_close(self):
        """
        This method is called when a websocket/sockjs connection is closed.
        
        :param      self:  The object
        
        :return:     Doesn't return anything, except a confirmation of closed connection back to web app.
        
        """

        LOGGER.info('[ChatWebsocketHandler] Websocket conneciton close event %s ' % self)

        stopmsg = {
                'msg_type': 'public',
                'stage': 'stop',
                'msg': {
                            'clientid': self.mqtt_client._clientid, 
                            'name': self.mqtt_client._name,
                            'participants': len(websocketParticipants) - 1
                        }
        }

        topic = 'public/msgs'

        # publishing the close connection info to rest of the rabbitmq subscribers/clients
        self.mqtt_client.publish(topic=topic, msg=stopmsg, qos=2, retain=False)

        # removing the connection of global list
        websocketParticipants.remove(self)

        LOGGER.info('[ChatWebsocketHandler] Websocket connection closed')







