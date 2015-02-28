# -*- coding: utf-8 -*-
'''
Sample application for the Python library for controlling the Teufel Raumfeld system

@author: Patrick Maier
@contact: mail@maierp.de
 
Webpage: https://github.com/maierp/pyraumfeld

Based on python-raumfeld by Thomas Feldmann:  
https://github.com/tfeldmann/python-raumfeld
'''
import raumfeld
from time import gmtime, strftime
import logging


def dataHasBeenUpdated():
    print("########## " + strftime("%Y-%m-%d %H:%M:%S", gmtime()) + " ##########")
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
    print("########## This gets updated when the config changes. To QUIT press any key... ##########")
     
    #kueche = raumfeld.getRoomsByName(u'Küche')[0]
    #kuecheZone = raumfeld.getZoneWithRoomName(u'Wohnzimmer')[0]
    #status = kuecheZone.mute
    #print("Mute: {0}".format(status))
    #kueche.mute = not status
    #kuecheZone.play()
    #print("Volume: {0}".format(kuecheZone.volume))
     
    #raumfeld.connectRoomToZone(kueche.UDN)
    

raumfeld.setLogging(logging.WARN);
raumfeld.registerChangeCallback(dataHasBeenUpdated)
raumfeld.init() # or with the host IP: raumfeld.init("192.168.0.10")
print("Host URL: " +raumfeld.hostBaseURL)

# To QUIT press any key...
raw_input()
