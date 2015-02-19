# -*- coding: utf-8 -*-
'''
Created on 25.01.2015

@author: patrick
'''

import json
import raumfeld
import threading
from bottle import route, run
from urllib import quote, unquote

updateAvailableEvent = threading.Event()

def __getSingleZone(name_udn):
    """Tries to find the first occurring Zone with the specified name or UDN"""
    zone = None
    if (name_udn.startswith("uuid:")):
        zone = raumfeld.getZoneByUDN(name_udn)
    else:
        zones = raumfeld.getZonesByName(name_udn.decode('utf-8'))
        if (len(zones) > 0):
            zone = zones[0]
    return zone

def __getSingleRoom(name_udn):
    """Tries to find the first occurring Room with the specified name or UDN"""
    room = None
    if (name_udn.startswith("uuid:")):
        room = raumfeld.getRoomByUDN(name_udn)
    else:
        rooms = raumfeld.getRoomsByName(name_udn.decode('utf-8'))
        if (len(rooms) > 0):
            room = rooms[0]
    return room


@route('/')
def index():
    returndata = u'<html><body>'
    
    returndata += u'</body></html>'
    return returndata

################
# Global actions
################    
@route('/zones')
def getZones():
    """Returns the Zone names and UDNs in JSON format"""
    returndata = {}
    returndata["data"] = []
    returndata["success"] = False
    for zone in raumfeld.getZones():
        z = {}
        z['name'] = zone.Name
        z['udn'] = zone.UDN
        returndata["data"].append(z)
        returndata["success"] = True
    return json.dumps(returndata)

@route('/unassignedRooms')
def getUnassignedRooms():
    """Returns the unassigned room names and UDNs in JSON format"""
    returndata = {}
    returndata["data"] = []
    returndata["success"] = False
    for room in raumfeld.getUnassignedRooms():
        r = {}
        r['name'] = room.Name
        r['udn'] = room.UDN
        returndata["data"].append(r)
        returndata["success"] = True
    return json.dumps(returndata)



################
# Zone actions
################
@route('/zone/<name_udn>')
def getZone(name_udn):
    """Returns the Zone name and UDN in JSON format"""
    returndata = {}
    returndata["success"] = False
    zone = __getSingleZone(name_udn)
    if zone != None:
        z = {}
        z['name'] = zone.Name
        z['udn'] = zone.UDN
        returndata["data"] = z
        returndata["success"] = True
    return json.dumps(returndata)

@route('/zone/<name_udn>/volume')
def getZoneVolume(name_udn):
    """Gets the volume of the Zone defined by the name or UDN"""
    returndata = {}
    returndata["success"] = False
    zone = __getSingleZone(name_udn)
    if zone != None:
        returndata["data"] = zone.volume
        returndata["success"] = True
    return json.dumps(returndata)

@route('/zone/<name_udn>/volume/<volume:int>')
def setZoneVolume(name_udn, volume):
    """Sets the volume of the Zone defined by the name or UDN"""
    returndata = {}
    returndata["success"] = False
    zone = __getSingleZone(name_udn)
    if zone != None:
        zone.volume = volume
        returndata["success"] = True
    return json.dumps(returndata)

@route('/zone/<name_udn>/volume/<amount:re:[+-]d+>')
def changeZoneVolume(name_udn, amount):
    """Changes the volume of the Zone defined by the name or UDN"""
    returndata = {}
    returndata["success"] = False
    zone = __getSingleZone(name_udn)
    if zone != None:
        zone.changeVolume(int(amount))
        returndata["success"] = True
    return json.dumps(returndata)

@route('/zone/<name_udn>/rooms')
def getZoneRooms(name_udn):
    """Gets the rooms of the Zone defined by the name or UDN"""
    returndata = {}
    returndata["data"] = []
    returndata["success"] = False
    zone = __getSingleZone(name_udn)
    if zone != None:
        for room in zone.getRooms():
            r = {}
            r['name'] = room.Name
            r['udn'] = room.UDN
            returndata["data"].append(r)
            returndata["success"] = True
    return json.dumps(returndata)


@route('/zone/<name_udn>/play/<uri:path>')
def zonePlayURI(name_udn, uri):
    returndata = {}
    returndata["success"] = False
    zone = __getSingleZone(name_udn)
    if zone != None:
        #zone.play("dlna-playcontainer://{udn}?sid={sid}&cid={cid}&md=0".format(udn=quote(raumfeld.getMediaServerUDN()), sid=quote("urn:upnp-org:serviceId:ContentDirectory"), cid=quote("0/Playlists/MyPlaylists/Radio/" + unicode(index))))
        zone.play(unquote(uri))
        returndata["success"] = True
    return json.dumps(returndata)
    
@route('/zone/<name_udn>/play')
def zonePlay(name_udn):
    returndata = {}
    returndata["success"] = False
    zone = __getSingleZone(name_udn)
    if zone != None:
        zone.play()
        returndata["success"] = True
    return json.dumps(returndata)

################
# Room actions
################
@route('/room/<name_udn>')
def getRoom(name_udn):
    """Returns the Room name and UDN in JSON format"""
    returndata = {}
    returndata["success"] = False
    room = __getSingleRoom(name_udn)
    if room != None:
        z = {}
        z['name'] = room.Name
        z['udn'] = room.UDN
        returndata["data"] = z
        returndata["success"] = True
    return json.dumps(returndata)

@route('/room/<name_udn>/volume')
def getRoomVolume(name_udn):
    """Gets the volume of the Room defined by the name or UDN"""
    returndata = {}
    returndata["success"] = False
    room = __getSingleRoom(name_udn)
    if room != None:
        returndata["data"] = room.volume
        returndata["success"] = True
    return json.dumps(returndata)

@route('/room/<name_udn>/volume/<volume:int>')
def setRoomVolume(name_udn, volume):
    """Sets the volume of the Room defined by the name or UDN"""
    returndata = {}
    returndata["success"] = False
    room = __getSingleRoom(name_udn)
    if room != None:
        room.volume = volume
        returndata["success"] = True
    return json.dumps(returndata)

@route('/room/<name_udn>/zone')
def getRoomZone(name_udn):
    """Gets the zone json of the Room defined by the name or UDN"""
    returndata = {}
    returndata["success"] = False
    room = __getSingleRoom(name_udn)
    if room != None:
        zone = raumfeld.getZoneWithRoomUDN(room.UDN)
        returndata["data"] = {}
        returndata["data"]["udn"] = zone.UDN
        returndata["data"]["name"] = zone.Name
        returndata["success"] = True
    return json.dumps(returndata)

@route('/room/<name_udn>/separate')
def separateRoom(name_udn):
    """Separates the the Room defined by the name or UDN from its zone"""
    global updateAvailableEvent
    returndata = {}
    returndata["success"] = False
    room = __getSingleRoom(name_udn)
    if room != None:
        raumfeld.connectRoomToZone(room.UDN)
        updateAvailableEvent.wait()
        returndata["success"] = True
    return json.dumps(returndata)


##################
# Wait for Changes
##################
@route('/waitForChanges')
def waitForChanges():
    """Returns when an update in the DataStructure happened"""
    global updateAvailableEvent
    updateAvailableEvent.wait()
    returndata = []
    r = {}
    r['changes'] = True
    returndata.append(r)
    return json.dumps(returndata)


def __updateAvailableCallback():
    global updateAvailableEvent
    updateAvailableEvent.set()

def __resetUpdateAvailableEventThread():
    global updateAvailableEvent
    while True:
        updateAvailableEvent.wait()
        updateAvailableEvent.clear()
        

raumfeld.registerChangeCallback(__updateAvailableCallback)
raumfeld.init()

# Start observing the device list
resetUpdateAvailableEventThread = threading.Thread(target=__resetUpdateAvailableEventThread)
resetUpdateAvailableEventThread.daemon = True
resetUpdateAvailableEventThread.start()

run(host='0.0.0.0', port=8080, debug=True)