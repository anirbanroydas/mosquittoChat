Usage
=====

There are two types of Usage. One using mosquittoChat as a binary by installaing from pip and running the application in  the local machine directly. Another method is running the application from Docker. Hence another set of usage steps for the Docker use case.


[Docker Method] 
----------------

After having installed the above dependencies, and ran the **Optional** (If not using any CI Server) or **Required** (If using any CI Server) **CI Setup** Step, then just run the following commands to use it:


You can run and test the app in your local development machine or you can run and test directly in a remote machine. You can also run and test in a production environment. 



[Docker Method] Run
--------------------

The below commands will start everythin in development environment. To start in a production environment, suffix ``-prod`` to every **make** command.

For example, if the normal command is ``make start``, then for production environment, use ``make start-prod``. Do this modification to each command you want to run in production environment. 

**Exceptions:** You cannot use the above method for test commands, test commands are same for every environment. Also the  ``make system-prune`` command is standalone with no production specific variation (Remains same in all environments).

* **Start Applcation**
  ::

      $ make clean
      $ make build
      $ make start

      # OR

      $ docker-compose up -d


    
  
* **Stop Application**
  ::

      $ make stop

      # OR

      $ docker-compose stop


* **Remove and Clean Application**
  ::

      $ make clean

      # OR

      $ docker-compose rm --force -v
      $ echo "y" | docker system prune


* **Clean System**
  ::

      $ make system-prune

      # OR

      $ echo "y" | docker system prune






[Docker Method] Logging
------------------------


* To check the whole application Logs
  ::

      $ make check-logs

      # OR

      $ docker-compose logs --follow --tail=10



* To check just the python app\'s logs
  ::

      $ make check-logs-app

      # OR

      $ docker-compose logs --follow --tail=10 identidock




[Standalone Binary Method] Run
--------------------------------

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



