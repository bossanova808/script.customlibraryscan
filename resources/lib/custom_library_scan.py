# -*- coding: utf-8 -*-

import xbmc
import time
import json
from resources.lib.common import *

global paths_to_update


class MyMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        log('MyMonitor - init')

    # def onDatabaseUpdated(self, database):
    #     log("onDatabaseUpdated")
    #     log(database)
    #
    # def onNotification(self, sender, method, data):
    #     log("onNotification")
    #     log(sender)
    #     log(method)
    #     log(data)

    def onScanFinished(self, library):
        log("onScanFinished")
        log(library)

        if paths_to_update:
            sendLibraryScanRFequestForPath(paths_to_update[0])
            paths_to_update.pop(0)


def sendLibraryScanRFequestForPath(path):
    command = json.dumps({
        'jsonrpc': '2.0',
        'id': 0,
        'method': 'VideoLibrary.Scan',
        'params': {
            'directory': path,
            'showdialogs': True
        }
    })

    send_kodi_json(f'Kick off video library scan for path: {path}', command)


def run():

    global paths_to_update

    footprints()
    monitor = MyMonitor()

    paths_to_update = ["C:\\XBMC\\Video Files\\TV01\\", "C:\\XBMC\\Video Files\\TV02\\"]

    # Kick off the first path's update
    sendLibraryScanRFequestForPath(paths_to_update[0])
    # Remove the path from our list
    paths_to_update.pop(0)

    # xbmc.executebuiltin('UpdateLibrary(video,C:\\XBMC\\Video Files\\TV01\\)')
    # xbmc.executebuiltin('UpdateLibrary(video,C:\\XBMC\\Video Files\\TV02\\)')

    # # Run until abort requested
    while not monitor.abortRequested() and paths_to_update:
        if monitor.waitForAbort(1) or not paths_to_update:
            # Abort was requested while waiting. We should exit
            footprints(False)
            break
