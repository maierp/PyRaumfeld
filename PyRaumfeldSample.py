# -*- coding: utf-8 -*-
'''
Sample application for the Python library for controlling the Teufel Raumfeld system

@author: Patrick Maier
@contact: mail@maierp.de

Based on python-raumfeld by Thomas Feldmann:
https://github.com/tfeldmann/python-raumfeld

The Lib provides a data structure representing the Zone and room config of Raumfeld

Zone objects:
* Name, UDN, Location, Address, transport_state, uri, uri_metadata, track_uri, track_metadata  (readonly)
* volume, mute (read/write)
* play([uri(optional)]), next(), previous(), pause()
* A zone contains a list of Room objects which can be fetched with getRooms() -> returns an array
* You can search for Rooms in a Zone by calling getRoomsByName(name) -> returns array of found rooms ...
* ... or for a specific room by calling getRoomByUDN(udn) -> returns the room (None otherwise)

Room objects:
* Name, UDN (readonly)
* volume, mute (read/write)
* A room contains a list of Renderer objects which can be fetched with getRenderers() -> returns an array
* You can search for a Renderer in a Room by calling getRenderer(name) -> returns the renderer (None otherwise)

Renderer objects:
* Name, UDN, Location, Address, transport_state, uri, uri_metadata, track_uri, track_metadata  (readonly)
* volume, mute (read/write)
* play([uri(optional)]), next(), previous(), pause()

Global functions are:
* init([hostIP(optional)]) this inits the library and searches for the hostIP if none is provided.
* registerChangeCallback(callback) here you can register your function which should be called when something in the data structure has changed
* getRoomsByName(name) searches for all rooms containing the string in their name
* getRoomByUDN(udn) returns the Room object defined by the UDN
* getZones() returns the list of Zone objects
* getUnassignedRooms() returns the list of unassigned room objects
* getZonesByName(name) searches for all zones containing the string in their name
* getZoneByUDN(udn) returns the Zone object defined by the UDN
* getZoneWithRoom(room_obj) returns the Zone containing the provided room object
* getZoneWithRoomName(name) returns the Zone containing a room defined by its name
* getZoneWithRoomUDN(udn) returns the Zone containing a room defined by its UDN

Zone-Configuration-Functions are:
* dropRoomByUDN(udn) drops a room from its Zone
* connectRoomToZone(room_udn, [zone_udn(optional)] puts the room with the given roomUDN in the zone with the zoneUDN. If no zone_udn is provided, a new zone is created

Global variables:
* hostBaseURL (readonly) the base URL of the host
* debug (True/False) to show debug messages
'''
import raumfeld

raumfeld.debug = True
raumfeld.init("10.10.10.93")
#raw_input('Press any key to end...')


print(raumfeld.hostBaseURL)


inp = ''
while inp == '':
    print("Zones:")
    for zone in raumfeld.getZones():
        print("UDN: " + zone.UDN + " Name: " + zone.Name + " Location: " + zone.Location)
        for room in zone.getRooms():
            print("\tUDN: " + room.UDN + " Name: " + room.Name)
            for renderer in room.getRenderers():
                print("\t\tUDN: " + renderer.UDN + " Name: " + renderer.Name + " Location: " + renderer.Location + " Volume: " + unicode(renderer.volume))
     
    print("Unassigned Rooms:")
    for room in raumfeld.getUnassignedRooms():
        print("Name: " + room.Name + " UDN: " + room.UDN)
        for renderer in room.getRenderers():
            print("\tUDN: " + renderer.UDN + " Name: " + renderer.Name + " Location: " + renderer.Location)
     
    #kueche = raumfeld.getRoomsByName(u'Küche')[0]
    #kuecheZone = raumfeld.getZoneWithRoomName(u'Wohnzimmer')[0]
    #status = kuecheZone.mute
    #print("Mute: {0}".format(status))
    #kueche.mute = not status
    #kuecheZone.play()
    #print("Volume: {0}".format(kuecheZone.volume))
     
    #raumfeld.connectRoomToZone(kueche.UDN)
    inp = raw_input("prompt")
