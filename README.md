EG-EMDR
=======

EMDR Consumer and batchs for EVE-Guidance project.

Important note
--------------

This "tool" is / will be a submodule for the main github project : https://github.com/Kyria/EVE-Guidance

Specific installation will be here, but if you want to use the whole application, please consider using the EVE-Guidance installation doc.

Project Requirements
--------------------
- Python >=2.7 <3 
- ZeroMQ
- MySQL (only for now)


Installation
------------

1. Create a virtual env ``` virtualenv egemdr_env```
2. Go into the virtualenv directory ```egemdr_env``` and clone the repository  ```  git clone https://github.com/Kyria/EG-EMDR.git``` 
3. Don't forget to use virtualenv with ``` source bin/activate ```
3. Install requirements ``` pip install -r EG-EMDR/requirements.txt ``` 
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