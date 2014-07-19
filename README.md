Python-EMDR-Consumer
=====================

EMDR Consumer.

Important note
--------------

This "tool" provides a consumer written in python for EMDR (see http://eve-market-data-relay.readthedocs.org/en/latest/)

Project Requirements
--------------------
- Python >=2.7 <3 
- ZeroMQ
- MySQL (only for now)


Installation
------------

1. Create a virtual env ``` virtualenv egemdr_env```
2. Go into the virtualenv directory ```egemdr_env``` and clone the repository  ```  git clone https://github.com/Kyria/Python-EMDR-Consumer.git``` 
3. Don't forget to use virtualenv with ``` source bin/activate ```
3. Install requirements ``` pip install -r Python-EMDR-Consumer/requirements.txt ``` 
4. Configure the settings file in ```config```
5. On your database, execute ```sql/create_table.sql``` to create the required tables.
6. You are now ready to use it.


Using EG-EMDR
-------------

To use the emdr consumer, simply do this command : 
```
python consumer.py
```

You can call this python script in a daemon shell script to run it when you start your server. 

NOTE : The script will execute a "purge" at the start of the script and do one every 24 hours automatically, so you don't have to worry about "old data"
