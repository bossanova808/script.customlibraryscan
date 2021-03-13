# -*- coding: utf-8 -*-

import xbmc
import xbmcvfs
import xbmcgui
import time
import json
import os
import sys
import yaml
from .common import *
from .recipe import Recipe
from .store import Store
from .monitor import KodiMonitor


def run(args):
    """
    This is 'main' - kicks things off, creates the monitor etc..
    """

    footprints()

    # Special run mode... if the addon is called with the first argument as STOP, we want to cancel a run:
    if len(args) == 2 and args[1] == "STOP":
        log("Received STOP request, will stop at end of current path being scanned.")
        notify("Sending STOP request to to Custom Library Scan", xbmcgui.NOTIFICATION_INFO)
        ADDON.setSetting("StopRequested", "true")

    # Otherwise, if we're already running, prevent re-runs
    elif get_property_as_bool(HOME_WINDOW, "CustomLibraryScanIsRunning"):
        log("Addon is already running, can't re-run at the moment.")
        notify("Addon is already running, can't re-run at the moment.")

    else:
        # Set state as running and clear our marker for manual stop requests
        set_property(HOME_WINDOW, "CustomLibraryScanIsRunning", "true")
        ADDON.setSetting('StopRequested', "false")

        # addon can be called with zero, or one or more recipes as arguments
        # if no recipe is provided, will attempt to load the 'default.yaml' recipe
        # can also be called with a sublist of media types to specify just running those
        # sections of default.yaml

        recipes_to_load = ['default']
        if len(args) > 1 \
                and 'tv' not in args \
                and 'movies' not in args \
                and 'music' not in args \
                and 'musicvideos' not in args:
            recipes_to_load = args[1:]

        for recipe in recipes_to_load:

            # Load each recipe into Store
            Recipe.loadRecipe(recipe)

            # Short circuit if there is no recipe supplied and default.yaml not found
            if not Store.recipe:
                log('No scanning recipe loaded.')
                continue

            log(f'Scan in this order: {Store.recipe["order"]}')

            # Sub scan of one type specified just using just default.yaml?
            # Strip out the other types from our recipe's order
            if 'tv' in args or 'movies' in args or 'music' in args or 'musicvideos' in args:
                for media_type in ['tv', 'movies', 'music', 'musicvideos']:
                    if media_type not in args:
                        try:
                            Store.recipe["order"].remove(media_type)
                        except ValueError:
                            pass

            # Loop through and scan things in the order specified...
            for library_type_to_scan in Store.recipe["order"]:

                method = None
                show_dialog = None
                paths = []

                if library_type_to_scan == 'tv':
                    method = 'video'
                    try:
                        paths = Store.recipe['tv']['paths']
                        show_dialog = Store.recipe['tv']['show_dialog']
                    except KeyError:
                        log(f'No {library_type_to_scan} paths found to update')
                        continue
                elif library_type_to_scan == 'movies':
                    method = 'video'
                    try:
                        paths = Store.recipe['movies']['paths']
                        show_dialog = Store.recipe['movies']['show_dialog']
                    except KeyError:
                        log(f'No {library_type_to_scan} paths found to update')
                        continue
                elif library_type_to_scan == 'music':
                    method = 'audio'
                    try:
                        paths = Store.recipe['music']['paths']
                        show_dialog = Store.recipe['music']['show_dialog']
                    except KeyError:
                        log(f'No {library_type_to_scan} paths found to update')
                        continue
                elif library_type_to_scan == 'musicvideos':
                    method = 'video'
                    try:
                        paths = Store.recipe['musicvideos']['paths']
                        show_dialog = Store.recipe['musicvideos']['show_dialog']
                    except KeyError:
                        log(f'No {library_type_to_scan} paths found to update')
                        continue
                else:
                    log(f'Library type of {library_type_to_scan} not recognised. ')

                log(
                    f'Queueing scan of {library_type_to_scan}, method {method}, show_dialogs {show_dialog}, paths {paths}')

                # store our list of paths to update
                for path in paths:
                    Store.paths_to_update.append((method, path, show_dialog))

        # If we've read in the recipe(s) ok, we now have a stored list of paths to scan...
        if len(Store.paths_to_update) > 0 and not get_setting_as_bool('StopRequested'):

            # Create a monitor to listen to onScanFinished whilst we loop through the things to update...
            Store.kodi_event_monitor = KodiMonitor()

            log("Store.paths_to_update is")
            log(Store.paths_to_update)
            # Kick off by scanning the first path
            # from then on, we'll listen to onScanFinished and trigger the rest of the scans sequentially
            first_path = Store.paths_to_update.pop(0)
            Store.kodi_event_monitor.sendLibraryScanRequestForPath(first_path)

            while not Store.kodi_event_monitor.abortRequested() \
                    and Store.paths_to_update \
                    and not get_setting_as_bool('StopRequested'):

                if Store.kodi_event_monitor.waitForAbort(1):
                    log('Abort requested')
                    break
                elif not Store.paths_to_update:
                    log('No more paths to update')
                    break

            # Log that we have recognised a manual request to stop scanning
            if get_setting_as_bool('StopRequested'):
                log('A manual stop request has been received, stopping now.')
                # Don't need the double notification...
                # notify('Manual stop of Custom Library Scan requested', xbmcgui.NOTIFICATION_INFO)
                ADDON.setSetting('StopRequested', 'false')

    # All recipes supplied have now been processed, or a manual stop has been received, so we exit...
    set_property(HOME_WINDOW, "CustomLibraryScanIsRunning", "")
    footprints(False)
