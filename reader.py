# Defining  all the imports
import rticonnextdds_connector as rti
import rtde_control
import re

# Connecting to the robot IP
rtde_c = rtde_control.RTDEControlInterface("xx.xx.xx.xx")
#Using config.xml
with rti.open_connector(
        config_name="FotfParticipantLibrary::FotfSubParticipant",
        url="./config.xml") as connector:

    input = connector.get_input("FotfSubscriber::FotfColorReader")

    print("Waiting for publications...")
    input.wait_for_publications() # wait for at least one matching publication

    print("Waiting for data...")
    while True:
        input.wait() # wait for data on this input
        input.take()
        for sample in input.samples.valid_data_iter:
            # You can get all the fields in a get_dictionary()
            data = sample.get_dictionary()
            command = data["command"]
            
            # If the string matches the RegEx, we can execute the command
            if command[:11] == "rtde_c.move" and re.fullmatch(r"^[0-9,.\s\-]{0,38}$", command[14:52]):
                print("command: " + repr(command))
                eval(command)
            else:
                print("Unexpected command received")