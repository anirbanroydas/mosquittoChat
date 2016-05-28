Overview
=========

mosquittochat is an MQTT protocol based simple Chat Server which can be set up locally to chat in your LAN. It supports both **Public Chat** among all participants connected simultaneously at a particular time and also **Private Chat** betweent those individual participants.

It uses the `MQTT <https://www.mqtt.org/>`_  protocol to implement the real time message passing system. **MQTT** is implemented in many languages and in many softwares, one of such is `Mosquitto <https://www.mosquitto.org/>`_ , which is a message broker implementing the `MQTT <https://www.mqtt.org/>`_ protocol.

The connection is created using the `sockjs <https://github.com/sockjs/sockjs-client>`_ protocol. **SockJS** is implemented in many languages, primarily in Javascript to talk to the servers in real time, which tries to create a duplex bi-directional connection between the **Client(browser)** and the **Server**. Ther server should also implement the **sockjs** protocol. Thus using the  `sockjs-tornado <https://github.com/MrJoes/sockjs-tornado>`_ library which exposes the **sockjs** protocol in `Tornado <http://www.tornadoweb.org/>`_ server.

It first tries to create a `Websocket <https://en.wikipedia.org/wiki/WebSocket>`_ connection, and if it fails then it fallbacks to other transport mechanisms, such as **Ajax**, **long polling**, etc. After the connection is established, the tornado server**(sockjs-tornado)** connects to **Mosquitto** via MQTT protocol using the **MQTT Python Client Library**, `paho-mqtt <https://pypi.python.org/pypi/paho-mqtt/>`_. 

Thus the connection is *web-browser* to *tornado* to *mosquitto* and vice versa.

