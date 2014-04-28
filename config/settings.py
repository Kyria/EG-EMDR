
# The maximum number of greenlet workers in the greenlet pool. 
# This is not one # per processor, a decent machine 
# can support hundreds or thousands of greenlets.
# I recommend setting this to almost the maximum number of connections your database
# backend can accept, if you must open one connection per save op.
MAX_NUM_POOL_WORKERS = 200

# uncomment relay you want to use
RELAYS = [
    #"tcp://relay-us-west-1.eve-emdr.com:8050"    , # Cogent    Sacramento, CA	
    #"tcp://relay-us-central-1.eve-emdr.com:8050" , # Ubuquity  Hosting	Chicago.
    #"tcp://relay-us-east-1.eve-emdr.com:8050"    , # Digital   Ocean	New York, NY
    #"tcp://relay-ca-east-1.eve-emdr.com:8050"    , # OVH US    Montreal, CA
    "tcp://relay-eu-germany-1.eve-emdr.com:8050" , # Hetzner   Germany
]

DB_HOST = ""
DB_USER = ""
DB_PASS = ""
DB_NAME = ""