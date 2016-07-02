# -*- coding: utf-8 -*-
"""
Python library for controlling the Teufel Raumfeld system

@author: Patrick Maier
@contact: mail@maierp.de

Based on python-raumfeld by Thomas Feldmann:
https://github.com/tfeldmann/python-raumfeld

Further information see README.md
"""

import logging
import socket
import threading
import time
import urllib2
import xml.dom.minidom
from httplib import BadStatusLine
from urllib2 import URLError
from uuid import uuid4

from pysimplesoap.client import SoapClient

__version__ = '0.5'

__zones = []
__zonesLock = threading.Lock()
__unassignedRooms = []
__unassignedRoomsLock = threading.Lock()

__zoneElements = []  # XML <zone> elements from getZones
__zoneElementsLock = threading.Lock()
__unassignedElements = []  # XML <room> elements from getZones
__unassignedElementsLock = threading.Lock()
__deviceElements = []  # XML <device> elements from listDevices
__deviceElementsLock = threading.Lock()

__mediaServer = None

__newZoneDataEvent = threading.Event()
__newDeviceDataEvent = threading.Event()
__dataProcessedEvent = threading.Event()

__sessionUUID = uuid4().hex
# __mediaServerUDN = ""
__callback = None

hostBaseURL = "http://hostip:47365"
socket.setdefaulttimeout(None)


class MediaServer(object):
    """Raumfeld MediaServer"""

    def __init__(self, udn, location):
        self._udn = udn
        self._location = location
        scheme, netloc, _, _, _, _ = urllib2.urlparse.urlparse(location)
        self._address = '{0}://{1}'.format(scheme, netloc)
        # ToDo: get correct ControlLocation from the XML file
        self._contentDirectory = SoapClient(
            location='{0}/cd/Control'.format(self._address),
            action='urn:schemas-upnp-org:service:ContentDirectory:1#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)

    @property
    def UDN(self):
        """Get the UDN of the MediaServer"""
        return self._udn

    @property
    def Location(self):
        """Get the location URI"""
        return self._location

    # Browse and Search
    def browse(self, object_id, browse_flag="BrowseMetadata", filter="*", request_count="25"):
        """Browse Media Server"""
        return self._contentDirectory.Browse(ObjectID=object_id, BrowseFlag=browse_flag,
                                             Filter=filter, StartingIndex="0",
                                             RequestedCount=request_count, SortCriteria="").Result

    def browse_children(self, object_id, filter="*", request_count="25"):
        """Convenience function for browsing child elements; returns Result and NumberReturned"""
        children = self._contentDirectory.Browse(ObjectID=object_id,
                                                 BrowseFlag="BrowseDirectChildren",
                                                 Filter=filter, StartingIndex="0",
                                                 RequestedCount=request_count, SortCriteria="")
        result = children.Result
        count_returned = children.NumberReturned
        return result, count_returned

    def search(self, container_id, search_criteria, filter="*", request_count="25"):
        """Search Media Server"""
        return self._contentDirectory.Search(ContainerID=container_id,
                                             SearchCriteria=search_criteria,
                                             Filter=filter, StartingIndex="0",
                                             RequestedCount=request_count, SortCriteria="").Result

    # Queue Operations
    def create_queue(self, desired_name, container_id):
        """CreateQueue Returns GivenName and QueueID"""
        self._contentDirectory.CreateQueue(DesiredName=desired_name, ContainerID=container_id)

    def add_container(self, queue_id, container_id, source_id="", criteria="", start_index="0",
                      end_index="0", position="0"):
        """AddContainerToQueue"""
        self._contentDirectory.AddContainerToQueue(QueueID=queue_id, ContainerID=container_id,
                                                   SourceID=source_id, SearchCriteria=criteria,
                                                   StartIndex=start_index, EndIndex=end_index,
                                                   Position=position)

    def add_item(self, queue_id, object_id, position):
        """AddItemToQueue"""
        self._contentDirectory.AddItemToQueue(QueueID=queue_id, ObjectID=object_id,
                                              Position=position)

    def move_in_queue(self, object_id, new_position):
        """MoveInQueue"""
        self._contentDirectory.MoveInQueue(ObjectID=object_id, NewPosition=new_position)

    def remove_from_queue(self, queue_id, from_position, to_position):
        """RemoveFromQueue"""
        self._contentDirectory.RemoveFromQueue(QueueID=queue_id, FromPosition=from_position,
                                               ToPosition=to_position)


class Renderer(object):
    """Raumfeld Renderer"""

    def __init__(self, name, udn, location):
        self._name = name
        self._udn = udn
        self._location = location
        scheme, netloc, _, _, _, _ = urllib2.urlparse.urlparse(location)
        self._address = '{0}://{1}'.format(scheme, netloc)
        # ToDo: get correct ControlLocation from the XML file
        self._renderingControl = SoapClient(
            location='{0}/RenderingControl/ctrl'.format(self._address),
            action='urn:upnp-org:serviceId:RenderingControl#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)
        self._avTransport = SoapClient(
            location='{0}/AVTransport/ctrl'.format(self._address),
            action='urn:schemas-upnp-org:service:AVTransport:1#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)

    def reinit(self, name, udn, location):
        self._name = name
        self._udn = udn
        self._location = location
        scheme, netloc, _, _, _, _ = urllib2.urlparse.urlparse(location)
        self._address = '{0}://{1}'.format(scheme, netloc)
        # ToDo: get correct ControlLocation from the XML file
        self._renderingControl = SoapClient(
            location='{0}/RenderingControl/ctrl'.format(self._address),
            action='urn:upnp-org:serviceId:RenderingControl#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)
        self._avTransport = SoapClient(
            location='{0}/AVTransport/ctrl'.format(self._address),
            action='urn:schemas-upnp-org:service:AVTransport:1#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)

    @property
    def Name(self):
        """Get the name of the renderer"""
        return self._name

    @property
    def UDN(self):
        """Get the UDN of the renderer"""
        return self._udn

    @property
    def Location(self):
        """Get the location URI"""
        return self._location

    @property
    def Address(self):
        """Get the network address"""
        return self._address

    def play(self, uri=None, meta=""):
        """Start playing
        :param uri: (optional) play a specific uri
        :param meta: (optional) meta data in DIDL-Lite format
        """
        if uri:
            self._avTransport.SetAVTransportURI(
                InstanceID=0, CurrentURI=uri, CurrentURIMetaData=meta)
        else:
            self._avTransport.Play(InstanceID=1, Speed=2)

    def next(self):
        """Next"""
        self._avTransport.Next(InstanceID=1)

    def previous(self):
        """Previous"""
        self._avTransport.Previous(InstanceID=1)

    def pause(self):
        """Pause"""
        self._avTransport.Pause(InstanceID=1)

    def seek(self, target, unit='ABS_TIME'):
        """Seek; unit = _ABS_TIME_/REL_TIME/TRACK_NR"""
        return self._avTransport.Seek(InstanceID=1, Unit=unit, Target=target)

    def stop(self):
        """Stop"""
        self._avTransport.Stop(InstanceID=1)

    @property
    def volume(self):
        """get/set the current volume"""
        try:
            return int(self._renderingControl.GetVolume(InstanceID=1).CurrentVolume)
        except:
            return 0

    @volume.setter
    def volume(self, value):
        self._renderingControl.SetVolume(InstanceID=1, DesiredVolume=value)

    def changeVolume(self, value):
        self._renderingControl.ChangeVolume(InstanceID=1, Amount=value)

    @property
    def mute(self):
        """get/set the current mute state"""
        response = self._renderingControl.GetMute(InstanceID=1, Channel=1)
        return int(response.CurrentMute) == 1

    @mute.setter
    def mute(self, value):
        self._renderingControl.SetMute(InstanceID=1, DesiredMute=1 if value else 0, Channel=1)


class Zone(Renderer):
    """Raumfeld Zone"""

    def __init__(self, name, udn, location):
        self._rooms = []
        self._udn = udn
        self._name = name
        self._location = location
        scheme, netloc, _, _, _, _ = urllib2.urlparse.urlparse(location)
        self._address = '{0}://{1}'.format(scheme, netloc)
        # ToDo: get correct ControlLocation from the XML file
        self._renderingControl = SoapClient(
            location='{0}/RenderingService/Control'.format(self._address),
            action='urn:upnp-org:serviceId:RenderingControl#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)
        self._avTransport = SoapClient(
            location='{0}/TransportService/Control'.format(self._address),
            action='urn:schemas-upnp-org:service:AVTransport:1#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)

    def reinit(self, name, udn, location):
        self._udn = udn
        self._name = name
        self._location = location
        scheme, netloc, _, _, _, _ = urllib2.urlparse.urlparse(location)
        self._address = '{0}://{1}'.format(scheme, netloc)
        # ToDo: get correct ControlLocation from the XML file
        self._renderingControl = SoapClient(
            location='{0}/RenderingService/Control'.format(self._address),
            action='urn:upnp-org:serviceId:RenderingControl#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)
        self._avTransport = SoapClient(
            location='{0}/TransportService/Control'.format(self._address),
            action='urn:schemas-upnp-org:service:AVTransport:1#',
            namespace='http://schemas.xmlsoap.org/soap/envelope/',
            soap_ns='soap', ns='s', exceptions=False)

    def _removeRoomByUDN(self, udn):
        """Remove the room with the UDN from the list of rooms"""
        for room_element in self._rooms:
            if room_element.UDN == udn:
                self._rooms.remove(room_element)

    def getRoomByUDN(self, udn):
        """Try to get the room of the zone by its UDN"""
        for room_element in self._rooms:
            if room_element.UDN == udn:
                return room_element
        return None

    def getRooms(self):
        """Returns the list of rooms in this zone"""
        return self._rooms

    def getRoomsByName(self, name):
        """Searches for rooms with a special name"""
        rooms = []
        for room in self._rooms:
            if room.Name.find(name):
                rooms.append(room)
        return rooms

    def bend(self, uri=None, meta=None):
        """BendAVTransportURI"""
        self._avTransport.BendAVTransportURI(
            InstanceID=0, CurrentURI=uri, CurrentURIMetaData=meta)

    """Generic function for getting all media info"""

    @property
    def media_info(self):
        """Get the media information"""
        info = self._avTransport.GetMediaInfo(InstanceID=1)
        info_dict = {'NrTracks': info.NrTracks,
                     'MediaDuration': info.MediaDuration,
                     'CurrentURI': info.CurrentURI,
                     'CurrentURIMetaData': info.CurrentURIMetaData,
                     'NextUri': info.NextUri,
                     'NextUriMetaData': info.NextUriMetaData,
                     'PlayMedium': info.PlayMedium,
                     'RecordMedium': info.RecordMedium,
                     'WriteStatus': info.WriteStatus
                     }
        return info_dict

    """For each info there are extra functions"""

    @property
    def media_info_NrTracks(self):
        return self.media_info()['NrTracks']

    @property
    def media_info_MediaDuration(self):
        return self.media_info()['MediaDuration']

    @property
    def media_info_CurrentURI(self):
        return self.media_info()['CurrentURI']

    @property
    def media_info_CurrentURIMetaData(self):
        return self.media_info()['CurrentURIMetaData']

    @property
    def media_info_NextUri(self):
        return self.media_info()['NextUri']

    @property
    def media_info_NextUriMetaData(self):
        return self.media_info()['NextUriMetaData']

    @property
    def media_info_PlayMedium(self):
        return self.media_info()['PlayMedium']

    @property
    def media_info_RecordMedium(self):
        return self.media_info()['RecordMedium']

    @property
    def media_info_WriteStatus(self):
        return self.media_info()['WriteStatus']

    """Generic function for getting all position info"""

    @property
    def position_info(self):
        """Get the position information"""
        info = self._avTransport.GetPositionInfo(InstanceID=1)
        info_dict = {'Track': info.Track,
                     'TrackDuration': info.TrackDuration,
                     'TrackMetaData': info.TrackMetaData,
                     'TrackURI': info.TrackURI,
                     'RelTime': info.RelTime,
                     'AbsTime': info.AbsTime,
                     'RelCount': info.RelCount,
                     'AbsCount': info.AbsCount
                     }
        return info_dict

    """For each info there are extra functions"""

    @property
    def position_info_Track(self):
        return self.position_info()['Track']

    @property
    def position_info_TrackDuration(self):
        return self.position_info()['TrackDuration']

    @property
    def position_info_TrackMetaData(self):
        return self.position_info()['TrackMetaData']

    @property
    def position_info_TrackURI(self):
        return self.position_info()['TrackURI']

    @property
    def position_info_RelTime(self):
        return self.position_info()['RelTime']

    @property
    def position_info_AbsTime(self):
        return self.position_info()['AbsTime']

    @property
    def position_info_RelCount(self):
        return self.position_info()['RelCount']

    @property
    def position_info_AbsCount(self):
        return self.position_info()['AbsCount']

    """Generic function for getting all transport info"""

    @property
    def transport_info(self):
        """Get the transport information"""
        info = self._avTransport.GetTransportInfo(InstanceID=1)
        info_dict = {'CurrentTransportState': info.CurrentTransportState,
                     'CurrentTransportStatus': info.CurrentTransportStatus,
                     'CurrentSpeed': info.CurrentSpeed
                     }
        return info_dict

    """For each info there are extra functions"""

    @property
    def transport_info_CurrentTransportState(self):
        return self.transport_info()['CurrentTransportState']

    @property
    def transport_info_CurrentTransportStatus(self):
        return self.transport_info()['CurrentTransportStatus']

    @property
    def transport_info_CurrentSpeed(self):
        return self.transport_info()['CurrentSpeed']


class Room(object):
    """Raumfeld Room"""

    def __init__(self, name, udn):
        self._renderers = []
        self._udn = udn
        self._name = name

    def _removeRendererByUDN(self, udn):
        """Remove the renderer with the UDN from the list of renderers"""
        for renderer_element in self._renderers:
            if renderer_element.UDN == udn:
                self._renderers.remove(renderer_element)

    def getRenderer(self, udn):
        """Try to get the renderer of the room by its UDN"""
        for renderer_element in self._renderers:
            if renderer_element.UDN == udn:
                return renderer_element
        return None

    def getRenderers(self):
        """Returns the list of renderers in this zone"""
        return self._renderers

    @property
    def Name(self):
        """Get the name of the device"""
        return self._name

    @property
    def UDN(self):
        """Get the UDN of the device"""
        return self._udn

    def play(self, uri=None, meta=""):
        """Start playing
        :param uri: (optional) play a specific uri
        :param meta: (optional) meta data in DIDL-Lite format
        """
        self._renderers[0].play(uri, meta)

    def next(self):
        """Next"""
        self._renderers[0].next()

    def previous(self):
        """Previous"""
        self._renderers[0].previous()

    def pause(self):
        """Pause"""
        self._renderers[0].pause()

    def seek(self, target, unit='ABS_TIME'):
        """Seek; unit = _ABS_TIME_/REL_TIME/TRACK_NR"""
        return self._renderers[0].seek(target, unit)

    def stop(self):
        """Stop"""
        self._renderers[0].stop()

    @property
    def volume(self):
        """get/set the current volume"""
        return self._renderers[0].volume

    @volume.setter
    def volume(self, value):
        self._renderers[0].volume = value

    def changeVolume(self, value):
        self._renderers[0].changeVolume(value)

    @property
    def mute(self):
        """get/set the current mute state"""
        return self._renderers[0].mute

    @mute.setter
    def mute(self, value):
        self._renderers[0].mute = value


def __listDevicesThread():
    """Thread for LongPolling the listDevices Web-Service of Raumfeld"""
    global hostBaseURL, __newDeviceDataEvent, __dataProcessedEvent, __deviceElements, __deviceElementsLock, __mediaServer
    listDevices_updateID = ''

    while True:
        try:
            request = urllib2.Request("{0}/{1}/listDevices".format(hostBaseURL, __sessionUUID),
                                      headers={"updateID": listDevices_updateID})
            response = urllib2.urlopen(request)
            listDevices_updateID = response.info().getheader('updateID')
            devices_xml = response.read()
            logging.debug(devices_xml.decode('utf-8'))
            dom = xml.dom.minidom.parseString(devices_xml)

            __deviceElementsLock.acquire()
            __deviceElements = dom.getElementsByTagName("device")
            __deviceElementsLock.release()

            for device_element in __deviceElements:
                if device_element.childNodes[0].nodeValue == "Raumfeld MediaServer":
                    __mediaServer = MediaServer(device_element.getAttribute("udn"),
                                                device_element.getAttribute("location"))
                    break

            # signal changes
            __newDeviceDataEvent.set()
            __dataProcessedEvent.wait()
        except (BadStatusLine, URLError, socket.timeout):
            logging.warning("Connection to host was lost. waiting 1 second and retrying...")
            time.sleep(1)


def __getZonesThread():
    """Thread for LongPolling the listDevices Web-Service of Raumfeld"""
    global hostBaseURL, __newZoneDataEvent, __dataProcessedEvent, __zoneElements, __zoneElementsLock, __unassignedElements, __unassignedElementsLock
    getZones_updateID = ''

    while True:
        try:
            request = urllib2.Request("{0}/{1}/getZones".format(hostBaseURL, __sessionUUID),
                                      headers={"updateID": getZones_updateID})
            response = urllib2.urlopen(request)
            getZones_updateID = response.info().getheader('updateID')
            zone_xml = response.read()
            logging.debug(zone_xml.decode('utf-8'))
            dom = xml.dom.minidom.parseString(zone_xml)

            __zoneElementsLock.acquire()
            __zoneElements = dom.getElementsByTagName("zone")
            __zoneElementsLock.release()

            # Get all the unassigned rooms
            __unassignedElementsLock.acquire()
            if dom.getElementsByTagName("unassignedRooms").length > 0:
                __unassignedElements = dom.getElementsByTagName("unassignedRooms")[
                    0].getElementsByTagName('room')
            else:
                __unassignedElements = []
            __unassignedElementsLock.release()

            # signal changes
            __newZoneDataEvent.set()
            __dataProcessedEvent.wait()
        except (BadStatusLine, URLError, socket.timeout):
            logging.warning("Connection to host was lost. waiting 1 second and retrying...")
            time.sleep(1)


def __updateZonesAndRoomsThread():
    """Thread for updating the Zone and Room data structure"""
    global __newZoneDataEvent, __newDeviceDataEvent, __newDeviceElementsEvent, __dataProcessedEvent, __zones, __zonesLock, __unassignedRooms, __unassignedRoomsLock, __zoneElements, __zoneElementsLock, __unassignedElements, __unassignedElementsLock, __deviceElements, __deviceElementsLock, __callback

    # Start observing the device list
    device_list_thread = threading.Thread(target=__listDevicesThread)
    device_list_thread.start()

    # Start observing the zone list
    zone_list_thread = threading.Thread(target=__getZonesThread)
    zone_list_thread.start()

    __newDeviceDataEvent.wait()

    while True:
        # Wait until there are new zone elements
        __newZoneDataEvent.wait()
        __newZoneDataEvent.clear()

        # Process Data...
        # Build data structure and fill with information from listDevices

        # List of unresolved devices
        unresolved_devices = []

        __zonesLock.acquire()
        __zoneElementsLock.acquire()

        # Create List of all UDNs from which we will delete the UDNs that are handled by the
        # following code. Remaining UDNs are elements to be removed from the data structure,
        # because they no longer exist
        udn_list = []
        for zone_element in __zones:
            udn_list.append(zone_element.UDN)
            for room_element in zone_element._rooms:
                udn_list.append(room_element.UDN)
                for renderer_element in room_element._renderers:
                    udn_list.append(renderer_element.UDN)

        # Modify data structure
        for zone_element in __zoneElements:
            zone_udn = zone_element.getAttribute("udn")

            # Fetch the device information from the listDevices elements
            __deviceElementsLock.acquire()
            zone_device = __getDeviceByUDN(__deviceElements, zone_udn)
            __deviceElementsLock.release()
            if zone_device is None:
                unresolved_devices.append(zone_udn)
                continue
            zone_location = zone_device.getAttribute("location")

            # Try to get existing zone, otherwise create a new zone
            zone = __getZoneByUDN(zone_udn)
            if zone is None:
                # Create Zone with information
                zone = Zone(zone_device.childNodes[0].nodeValue, zone_udn, zone_location)
                # Append the zone to the zones list
                __zones.append(zone)
            else:
                zone.reinit(zone_device.childNodes[0].nodeValue, zone_udn, zone_location)
                udn_list.remove(zone.UDN)

            # Fill zone with rooms
            for room_element in zone_element.getElementsByTagName("room"):
                # Try to get existing room, otherwise create a new room
                room = zone.getRoomByUDN(room_element.getAttribute("udn"))
                if room is None:
                    # Create the room with information
                    room = Room(room_element.getAttribute("name"), room_element.getAttribute("udn"))
                    # Append the room to the room list of the zone
                    zone._rooms.append(room)
                else:
                    udn_list.remove(room.UDN)

                # Fill room with renderers
                for renderer_element in room_element.getElementsByTagName("renderer"):
                    renderer_udn = renderer_element.getAttribute("udn")

                    # Fetch the device information from the listDevices elements
                    __deviceElementsLock.acquire()
                    renderer_device = __getDeviceByUDN(__deviceElements, renderer_udn)
                    __deviceElementsLock.release()
                    if renderer_device is None:
                        unresolved_devices.append(renderer_udn)
                        continue
                    renderer_location = renderer_device.getAttribute("location")

                    # Try to get existing renderer, otherwise create a new renderer
                    renderer = room.getRenderer(renderer_udn)
                    if renderer is None:
                        # Create Renderer with information
                        renderer = Renderer(renderer_element.getAttribute("name"), renderer_udn,
                                            renderer_location)
                        # Append the renderer to the list of renderers in the room
                        # (normally there is only one renderer)
                        room._renderers.append(renderer)
                    else:
                        renderer.reinit(renderer_element.getAttribute("name"), renderer_udn,
                                            renderer_location)
                        udn_list.remove(renderer.UDN)

        # Now delete the remaining UDNs from the data structure, because they don't exist anymore
        for zone_element in __zones:
            for room_element in zone_element._rooms:
                for udn in udn_list:
                    room_element._removeRendererByUDN(udn)
            for udn in udn_list:
                zone_element._removeRoomByUDN(udn)
        for udn in udn_list:
            __removeZoneByUDN(udn)

        __zoneElementsLock.release()
        __zonesLock.release()

        # Get all the unassigned rooms
        __unassignedRoomsLock.acquire()
        __unassignedElementsLock.acquire()

        # Create List of all UDNs from which we will delete the UDNs that are handled by the
        # following code. Remaining UDNs are elements to be removed from the data structure,
        # because they no longer exist
        udn_list = []
        for room_element in __unassignedRooms:
            udn_list.append(room_element.UDN)
            for renderer_element in room_element._renderers:
                udn_list.append(renderer_element.UDN)

        # Modify the data structure
        for room_element in __unassignedElements:
            # Try to get existing room, otherwise create a new room
            room = __getUnassignedRoomByUDN(room_element.getAttribute("udn"))
            if room is None:
                # Create the room with information
                room = Room(room_element.getAttribute("name"), room_element.getAttribute("udn"))
                # Append the room to the list of unassigned rooms
                __unassignedRooms.append(room)
            else:
                udn_list.remove(room.UDN)
            # Create the room with information
            for renderer_element in room_element.getElementsByTagName("renderer"):
                renderer_udn = renderer_element.getAttribute("udn")

                # Fetch the device information from the listDevices elements
                __deviceElementsLock.acquire()
                renderer_device = __getDeviceByUDN(__deviceElements, renderer_udn)
                __deviceElementsLock.release()
                if renderer_device is None:
                    unresolved_devices.append(renderer_udn)
                    continue
                renderer_location = renderer_device.getAttribute("location")

                # Try to get existing renderer, otherwise create a new renderer
                renderer = room.getRenderer(renderer_udn)
                if renderer is None:
                    # Create Renderer with information
                    renderer = Renderer(renderer_element.getAttribute("name"), renderer_udn,
                                        renderer_location)
                    # Append the renderer to the list of renderers in the room
                    # (normally there is only one renderer)
                    room._renderers.append(renderer)
                else:
                    renderer.reinit(renderer_element.getAttribute("name"), renderer_udn,
                                        renderer_location)
                    udn_list.remove(renderer.UDN)

        # Now delete the remaining UDNs from the data structure, because they don't exist anymore
        for room_element in __unassignedRooms:
            for udn in udn_list:
                room_element._removeRendererByUDN(udn)
        for udn in udn_list:
            __removeUnassignedRoomByUDN(udn)

        __unassignedElementsLock.release()
        __unassignedRoomsLock.release()

        logging.debug("Unresolved devices: " + str(unresolved_devices))

        if (__callback is not None) & (len(unresolved_devices) == 0):
            logging.info("Zone configuration changed.")
            __callback()

        # Notify the observing threads to continue
        __dataProcessedEvent.set()


def __getZoneByUDN(zone_udn):
    """return the zone with the given UDN (private function without lock)"""
    for zone_element in __zones:
        if zone_element.UDN == zone_udn:
            return zone_element
    return None


def __removeZoneByUDN(udn):
    """Remove the zone with the UDN from the list of zones"""
    for zone_element in __zones:
        if zone_element.UDN == udn:
            __zones.remove(zone_element)


def __getUnassignedRoomByUDN(room_udn):
    """return the unassigned room with the given UDN (private function without lock)"""
    for room_element in __unassignedRooms:
        if room_element.UDN == room_udn:
            return room_element
    return None


def __removeUnassignedRoomByUDN(udn):
    """Remove the unassigned room with the UDN from the list of unassigned rooms"""
    for room_element in __unassignedRooms:
        if room_element.UDN == udn:
            __unassignedRooms.remove(room_element)


def __getDeviceByUDN(deviceElements, udn):
    """Search and return the device element defined by the UDN from the listDevices elements"""
    for device_element in deviceElements:
        if device_element.getAttribute("udn") == udn:
            return device_element


def __discoverHost():
    """Discover the Raumfeld Host and return the IP Address"""
    group = ('239.255.255.250', 1900)
    service = 'urn:schemas-raumfeld-com:device:ConfigDevice:1'
    message = '\r\n'.join(['M-SEARCH * HTTP/1.1',
                           'HOST: {group[0]}:{group[1]}',
                           'MAN: "ssdp:discover"',
                           'ST: {st}',
                           'MX: 1', '', '']).format(group=group, st=service)

    socket.setdefaulttimeout(10)
    sock = socket.socket(socket.AF_INET,
                         socket.SOCK_DGRAM,
                         socket.IPPROTO_UDP)

    # socket options
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)

    # send group multicast
    sock.sendto(message.encode('utf-8'), group)

    while True:
        try:
            response = sock.recv(2048).decode('utf-8')
            # logging.debug(response)
            for line in response.split('\r\n'):
                if line.startswith('Location: '):
                    sock.close()
                    location = line.split(' ')[1].strip()
                    # Extract the netloc fragment of the URL
                    netloc = urllib2.urlparse.urlparse(location)[1]
                    sock.close()
                    socket.setdefaulttimeout(None)
                    # Return the IP-Address
                    return netloc.split(':')[0]
        except socket.timeout:
            sock.close()
            socket.setdefaulttimeout(None)
            break
    return ""


def registerChangeCallback(callback):
    """Method to register a callback function which is called when the data structure has changed"""
    global __callback
    __callback = callback


def getMediaServer():
    """Returns the Raumfeld Media Server"""
    return __mediaServer


def getMediaServerUDN():
    """Returns the UDN of the Raumfeld Media Server"""
    return __mediaServer.UDN


def getRoomsByName(name):
    """Searches for rooms with a special name"""
    global __zonesLock, __unassignedRoomsLock

    __zonesLock.acquire()
    __unassignedRoomsLock.acquire()
    roomList = []
    for zone in __zones:
        for room in zone._rooms:
            if (room.Name.find(name) >= 0):
                roomList.append(room)
    for room in __unassignedRooms:
        if (room.Name.find(name) >= 0):
            roomList.append(room)
    __unassignedRoomsLock.release()
    __zonesLock.release()
    return roomList


def getRoomByUDN(udn):
    """Searches for a room_element with a given UDN"""
    global __zonesLock, __unassignedRoomsLock

    __zonesLock.acquire()
    __unassignedRoomsLock.acquire()
    for zone_element in __zones:
        for room_element in zone_element._rooms:
            if room_element.UDN == udn:
                __unassignedRoomsLock.release()
                __zonesLock.release()
                return room_element
    for room_element in __unassignedRooms:
        if room_element.UDN == udn:
            __unassignedRoomsLock.release()
            __zonesLock.release()
            return room_element
    __unassignedRoomsLock.release()
    __zonesLock.release()
    return None


def getZones():
    """get all discovered zones. Requires initialize('Host-IP-Address')"""
    return __zones


def getUnassignedRooms():
    """get all unassigned rooms. Requires initialize('Host-IP-Address')"""
    return __unassignedRooms


def getZonesByName(name):
    """Searches for zones with a special name"""
    global __zonesLock

    zoneList = []
    __zonesLock.acquire()
    for zone_element in __zones:
        if (zone_element.Name.find(name) >= 0):
            zoneList.append(zone_element)
    __zonesLock.release()
    return zoneList


def getZoneByUDN(udn):
    """Searches for the zone with a given UDN"""
    global __zonesLock

    __zonesLock.acquire()
    for zone_element in __zones:
        if zone_element.UDN == udn:
            __zonesLock.release()
            return zone_element
    __zonesLock.release()
    return None


def getZoneWithRoom(room):
    """Returns the zone containing the room"""
    global __zonesLock

    __zonesLock.acquire()
    for zone_element in __zones:
        for room_element in zone_element._rooms:
            if room_element.UDN == room.UDN:
                __zonesLock.release()
                return zone_element
    __zonesLock.release()
    return None


def getZoneWithRoomName(name):
    """Returns the zones containing a room defined by its name"""
    global __zonesLock

    __zonesLock.acquire()
    zoneList = []
    for zone in __zones:
        for room_element in zone._rooms:
            if (room_element.Name.find(name) >= 0):
                zoneList.append(zone)
                break
    __zonesLock.release()
    return zoneList


def getZoneWithRoomUDN(udn):
    """Returns the zone containing a room defined by its UDN"""
    global __zonesLock

    __zonesLock.acquire()
    for zone_element in __zones:
        for room_element in zone_element._rooms:
            if room_element.UDN == udn:
                __zonesLock.release()
                return zone_element
    __zonesLock.release()
    return None


def dropRoomByUDN(udn):
    """Drops the room with the given UDN from the zone it is in"""
    global hostBaseURL
    urllib2.urlopen("{0}/dropRoomJob?roomUDN={1}".format(hostBaseURL, udn))


def connectRoomToZone(roomUDN, zoneUDN=''):
    """Puts the room with the given roomUDN in the zone with the zoneUDN"""
    global hostBaseURL
    urllib2.urlopen(
        "{0}/connectRoomToZone?roomUDN={1}&zoneUDN={2}".format(hostBaseURL, roomUDN, zoneUDN))


def setLogging(level=logging.DEBUG):
    logging.getLogger().setLevel(level)


def init(hostIPAddress=""):
    global hostBaseURL
    if hostIPAddress == "":
        hostIPAddress = __discoverHost()
    if hostIPAddress == "":
        logging.warning("Cannot determine host IP Address.")
        return

    hostBaseURL = "http://{0}:47365".format(hostIPAddress)
    # Start Thread which keeps the data structure updated
    updateThread = threading.Thread(target=__updateZonesAndRoomsThread)
    updateThread.daemon = True
    updateThread.start()
    __dataProcessedEvent.wait()


if __name__ == '__main__':
    print('Library version {0}'.format(__version__))
