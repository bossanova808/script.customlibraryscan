# -*- coding: utf-8 -*-

import xbmc
import xbmcvfs
import time
import json
import os
import sys
import yaml
from .common import *

# This will hold all the paths we explicitly want to update
global paths_to_update


# Kodi monitor - listen to onScanFinished events
class MyMonitor(xbmc.Monitor):

    def __init__(self, *args, **kwargs):
        xbmc.Monitor.__init__(self)
        log('Monitor - init')

    def onScanFinished(self, library):

        global paths_to_update

        log("onScanFinished")

        if paths_to_update:
            sendLibraryScanRequestForPath(paths_to_update[0])
            paths_to_update.pop(0)


def loadRecipe(recipe_name):
    """
    Load a custom scanning recipe from its yaml file - if no filename provided try and load default
    @return:
    """

    if not recipe_name:
        recipe_name = "default"

    if ADDON.getSetting("SettingsFolder"):
        settings_folder = ADDON.getSetting("SettingsFolder")
    else:
        settings_folder = PROFILE

    log("Settings folder: " + settings_folder)
    recipe_to_load = settings_folder + "/" + recipe_name
    log("Recipe to load is: " + recipe_name)

    # If there is no default, it's not actually a failure
    if not xbmcvfs.exists(recipe_to_load) and recipe_name == "default":
        return
    
    # https://stackoverflow.com/questions/1773805/how-can-i-parse-a-yaml-file-in-python
    with open(recipe_to_load, 'r') as stream:
        try:
            yaml.safe_load(recipe_to_load)
        except yaml.YAMLError as inst:
            notify(f'Error loading {recipe_to_load} - check logs!')
            log(inst)


def sendLibraryScanRequestForPath(path_and_method):
    """
    Send a request to Kodi to update the video library by looking at a specific path.
    @param path_and_method: tuple of (path, type) - the path for which to request the library update and a type of 'video' or 'music'
    """

    show_dialogs = get_setting_as_bool('ShowProgressDialogues')

    (path, method) = path_and_method

    if method == 'video':
        jsonMethod = 'VideoLibrary.Scan'
    else:
        jsonMethod = 'AudioLibrary.Scan'

    command = json.dumps({
        'jsonrpc': '2.0',
        'id': 0,
        'method': jsonMethod,
        'params': {
            'directory': path,
            'showdialogs': show_dialogs
        }
    })

    send_kodi_json(f'Kick off library scan for path: {path}', command)

    # This is another, more direct way to do this
    # Pro is that it doesn't require the JSON RPC to be active
    # Con is you can't control whether the update dialog shows
    # xbmc.executebuiltin('UpdateLibrary(video,C:\\XBMC\\Video Files\\TV01\\)')
    # xbmc.executebuiltin('UpdateLibrary(video,C:\\XBMC\\Video Files\\TV02\\)')


def customScanAllPaths():

    global paths_to_update

    if ADDON.getSetting("SettingsFolder"):
        settings_folder = ADDON.getSetting("SettingsFolder")
        paths_video_file = ADDON.getSetting("SettingsFolder") + "paths_video.txt"
        paths_music_file = ADDON.getSetting("SettingsFolder") + "paths_music.txt"
    else:
        settings_folder = PROFILE
        paths_video_file = PROFILE + "paths_video.txt"
        paths_music_file = PROFILE + "paths_music.txt"

    log("Settings folder: " + settings_folder)
    log("Location of paths_video.txt: " + paths_video_file)
    log("Location of paths_music.txt: " + paths_music_file)

    # Make the settings folder if it doesn't exist yet...
    if not xbmcvfs.exists(settings_folder):
        xbmcvfs.mkdirs(settings_folder)
    # Create empty paths_video.txt and paths_music.text files if they doesn't exist yet
    if not xbmcvfs.exists(paths_video_file):
        log("Creating " + paths_video_file + " as doesn't yet exist")
        with xbmcvfs.File(paths_video_file, 'w') as f:
            result = f.write("")
    if not xbmcvfs.exists(paths_music_file):
        log("Creating " + paths_music_file + " as doesn't yet exist")
        with xbmcvfs.File(paths_music_file, 'w') as f:
            result = f.write("")

    # load the paths to update from our settings files...
    with xbmcvfs.File(paths_video_file) as f:
        video_paths_to_update = f.read().splitlines()
    with xbmcvfs.File(paths_music_file) as f:
        music_paths_to_update = f.read().splitlines()

    # Make our total list of paths & types to update
    paths_to_update = []
    for path in video_paths_to_update:
        if path:
            paths_to_update.append((path.strip(), 'video'))
    for path in music_paths_to_update:
        if path:
            paths_to_update.append((path.strip(), 'music'))

    log("Updating paths, in this order:")
    log(paths_to_update)

    if not paths_to_update:
        log("No paths to update found in paths_video.txt or paths_music.txt - nothing to do...")
    else:
        # Kick off the first path's update
        sendLibraryScanRequestForPath(paths_to_update[0])
        # Remove first path from our list
        paths_to_update.pop(0)

        log("Paths to update is now")
        log(paths_to_update)

        # Create a monitor which will loop through the remaining paths as each scan finishes...
        if paths_to_update:
            monitor = MyMonitor()

            # Now, run until abort requested, and while we have paths to update
            while not monitor.abortRequested() and paths_to_update:
                if monitor.waitForAbort(1):
                    log("Abort requested")
                    break
                elif not paths_to_update:
                    log("No more paths to update")
                    break


def run(args):
    """
    This is 'main' - kicks things off, creates the monitor etc..
    """
    global paths_to_update

    footprints()

    # The addon is being called with a specific path as an argument...this only works for video paths currently
    if len(args) > 1 and args[1] == "scan_path":
        log("Request to scan specific path: " + sys.listitem.getLabel())
        sendLibraryScanRequestForPath((sys.listitem.getLabel(), 'video'))

    # The addon is being run as a service/or manually...update all the paths in paths_*.txt
    else:
        customScanAllPaths()

    # All done, we're exiting...
    footprints(False)





