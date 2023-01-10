# Defining  all the imports
from time import sleep
import rticonnextdds_connector as rti

#Using config.xml
with rti.open_connector(
        config_name="FotfParticipantLibrary::FotfPubParticipant",
        url="./config.xml") as connector:

    output = connector.get_output("FotfPublisher::FotfColorWriter")

    #Wait for at least one matching subscription
    print("Waiting for subscriptions...")
    output.wait_for_subscriptions()

    #Defining the possible commands in this array
    commands = ['rtde_c.moveJ([1.000, -1.57, -2.04, -1.06, 1.55, 2.93])',
        'rtde_c.moveJ([2.617, -1.57, -2.04, -1.06, 1.55, 2.93])']


    print("Writing...")
    while True:
        #Every 3sec we send a command
        for command in commands:
            output.instance.set_dictionary({"command": command})
            output.write()
            sleep(3)

    print("Exiting...")
    output.wait() # Wait for all subscriptions to receive the data before exiting