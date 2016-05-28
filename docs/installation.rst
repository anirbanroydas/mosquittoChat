Installation
=============

Prerequisites
--------------

1. python 2.7+
2. tornado
3. sockjs-tornado
4. sockjs-client
5. paho-mqtt
6. mosquitto

   
Install
-------
::

        $ pip install mosquittoChat

If above dependencies do not get installed by the above command, then use the below steps to install them one by one.

 **Step 1 - Install pip**

 Follow the below methods for installing pip. One of them may help you to install pip in your system.

 * **Method 1 -**  https://pip.pypa.io/en/stable/installing/

 * **Method 2 -** http://ask.xmodulo.com/install-pip-linux.html

 * **Method 3 -** If you installed python on MAC OS X via ``brew install python``, then **pip** is already installed along with python.


 **Step 2 - Install tornado**
 ::

         $ pip install tornado

 **Step 3 - Install sockjs-tornado**
 ::

         $ pip install sockjs-tornado


 **Step 4 - Install paho-mqtt**
 ::

         $ pip install paho-mqtt

 **Step 5 - Install Mosquitto**
 
 * *For* ``Mac`` *Users*
 
   1. Brew Install Mosquitto
   ::

         $ brew install mosquitto

   2. Configure mosquitto, by modifying the file at ``/usr/local/etc/mosquitto/mosquitto.conf``.

 * *For* ``Ubuntu/Linux`` *Users*

   1. Enable mosquitto repository (optional)

      First Try directly, if it doesn't work, then follow this step and continue after this.::

      $ sudo apt-add-repository ppa:mosquitto-dev/mosquitto-ppa

   

   2. Update the sources with our new addition from above
   ::

        $ apt-get update

  
   3. And finally, download and install Mosquitto
   ::

         $ sudo apt-get install mosquitto

 

   4. Configure mosquitto, by modifying the file at ``/usr/local/etc/mosquitto/mosquitto.conf``.




