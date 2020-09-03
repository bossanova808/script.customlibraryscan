# -*- coding: utf-8 -*-

import xbmc
import time
import json
import os
from .common import *

# This will hold all the paths we explicitly want to update
global paths_to_update


# Kodi monitor - listen to onScanFinished events
class MyMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        log('Custom Library Scan Monitor - init')

    def onScanFinished(self, library):

        global paths_to_update

        log("onScanFinished")
        if paths_to_update:
            sendLibraryScanRequestForPath(paths_to_update[0])
            paths_to_update.pop(0)


def sendLibraryScanRequestForPath(path):
    """
    Send a request to Kodi to update the video library by looking at a specific path.
    @param path: the path for which to request the library update
    """

    show_dialogs = get_setting_as_bool('')

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

    # This is another, more direct way to do this
    # Pro is that it doesn't require the JSON RPC to be active
    # Con is you can't control whether the update dialog shows
    # xbmc.executebuiltin('UpdateLibrary(video,C:\\XBMC\\Video Files\\TV01\\)')
    # xbmc.executebuiltin('UpdateLibrary(video,C:\\XBMC\\Video Files\\TV02\\)')


def run():
    """
    This is 'main' - kicks things off, creates the monitor etc..
    """
    global paths_to_update

    footprints()

    # Create an empty paths.txt file if it doesn't exist yet
    paths_file = PROFILE + "paths.txt"
    if not os.path.exists(paths_file):
        log("Creating " + paths_file + " as doesn't yet exist")
        os.makedirs(PROFILE)
        open(paths_file, 'a').close()

    # load the paths to update from our settings file...
    with open(paths_file) as f:
        paths_to_update = f.read().splitlines()

    if not paths_to_update:
        log("No paths to update found in paths.txt - nothing to do...")
    else:
        # Kick off the first path's update
        sendLibraryScanRequestForPath(paths_to_update[0])
        # Remove first path from our list
        paths_to_update.pop(0)

        # Create a monitor and give it the remaining paths to update - if there are any
        if paths_to_update:
            monitor = MyMonitor()

            # Now, run until abort requested, and while we have paths to update
            while not monitor.abortRequested() and paths_to_update:
                if monitor.waitForAbort(1):
                    log("Abort requested")
                elif not paths_to_update:
                    log("No more paths to update")
                # either way, we're done...
                break

    # We're exiting...
    footprints(False)





