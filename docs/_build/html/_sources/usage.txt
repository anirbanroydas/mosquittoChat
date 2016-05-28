Usage
=====

After having installed mosquittoChat, just run the following commands to use it:

Mosquitto Server
-----------------

1. *For* ``Mac`` *Users*
   ::
           
          # start normally
          $ mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf
           
          # If you want to run in background
          $ mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf -d 

          # start using brew services (doesn't work with tmux, athough there is a fix, mentioned in one of the pull requests and issues)
          $ brew services start mosquitto
           

2. *For* ``Ubuntu/LInux`` *Users*
   ::
           
          # start normally
          $ mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf

          # If you want to run in background
          $ mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf -d 

          # To start using service
          $ sudo service mosquitto start

          # To stop using service
          $ sudo service mosquitto stop
          
          # To restart using service
          $ sudo service mosquitto restart
          
          # To check the status
          $ service mosquitto status
           
          
mosquittoChat Application
--------------------------

1. Start Server
   ::          
        
        $ mosquittoChat [options]
        
2. Options    
   
   :--port: Port number where the chat server will start
   
   * **Example**
     :: 
             
             $ mosquittoChat --port=9191
             
             
3. Stop mosquittoChat Server
   
   Click ``Ctrl+C`` to stop the server.



