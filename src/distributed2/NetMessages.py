from enum import IntEnum

# CL: client sent
# SV: server sent
# B:  client/server sent
class NetMessages:
    CL_Hello = 0
    SV_Hello_Resp = 1

    # Change rate client wants snaphots
    CL_SetUpdateRate = 2
    # Change rate client sends commands
    CL_SetCMDRate = 3
    # Client is disconnecting
    CL_Disconnect = 4

    # Replace client interest zones
    CL_SetInterest = 5
    # Add client interest zones
    CL_AddInterest = 6
    # Remove client interest zones
    CL_RemoveInterest = 7
    # Server completed client's requested interest operation.
    SV_InterestComplete = 8

    # Snapshot of state of all objects at an instant in time.
    # May be delta compressed against last client acknowleged
    # snapshot.
    SV_Tick = 9

    # Client acknowledges snapshot.
    CL_Tick = 10

    # Non-stateful object message. Can be sent from
    # server or client depending on behavior defined
    # in DC file.
    B_ObjectMessage = 11

    # Server is granting ownership of an object to a client.
    SV_SetObjectOwner = 12

    # Object is coming into existance.
    SV_GenerateObject = 13
    # An object is coming into existance. The server has granted
    # ownership of the object to this client. The client will
    # instantiate an owner-view instance of the object.
    SV_GenerateOwnerObject = 14

    # Object is temporarily going away.
    SV_DisableObject = 15

    # Object is going away.
    SV_DeleteObject = 16
