PyRaumfeld 0.3
========

Python library for controlling the Teufel Raumfeld system

Author: Patrick Maier  
https://github.com/maierp/pyraumfeld

Based on python-raumfeld by Thomas Feldmann:  
https://github.com/tfeldmann/python-raumfeld

###Zone objects:
* Name, UDN, Location, Address, transport_state, uri, uri_metadata, track_uri, track_metadata  (readonly)
* volume, mute (read/write)
* play([uri(optional)]), next(), previous(), pause()
* A zone contains a list of Room objects which can be fetched with getRooms() -> returns an array
* You can search for Rooms in a Zone by calling getRoomsByName(name) -> returns array of found rooms ...
* ... or for a specific room by calling getRoomByUDN(udn) -> returns the room (None otherwise)

The Lib provides a data structure representing the Zone and room config of Raumfeld

###Room objects:
* Name, UDN (readonly)
* volume, mute (read/write)
* A room contains a list of Renderer objects which can be fetched with getRenderers() -> returns an array
* You can search for a Renderer in a Room by calling getRenderer(name) -> returns the renderer (None otherwise)

###Renderer objects:
* Name, UDN, Location, Address, transport_state, uri, uri_metadata, track_uri, track_metadata  (readonly)
* volume, mute (read/write)
* play([uri(optional)]), next(), previous(), pause()

###Global functions are:
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

###Zone-Configuration-Functions are:
* dropRoomByUDN(udn) drops a room from its Zone
* connectRoomToZone(room_udn, [zone_udn(optional)] puts the room with the given roomUDN in the zone with the zoneUDN. If no zone_udn is provided, a new zone is created

###Global variables:
* hostBaseURL (readonly) the base URL of the host
* debug (True/False) to show debug messages

##Sample Programs:
* PyRaumfeldSample.py: Shows the basic usage
* RaumfeldControl.py: Provides a web-based API to the Raumfeld system