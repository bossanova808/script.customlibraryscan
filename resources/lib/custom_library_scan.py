# -*- coding: utf-8 -*-

import xbmc
import time
import json
from resources.lib.common import *


def run():

    footprints()

    command = json.dumps({
        'jsonrpc': '2.0',
        'id': 0,
        'method': 'VideoLibrary.Scan',
        'params': {
            'directory': 'C:/XBMC/Video Files/TV01/',
            'showdialogs': True
        }
    })

    send_kodi_json("Kick off video library scan", command)


    # # Run until abort requested
    # while not kodi_monitor.abortRequested():
    #     if kodi_monitor.waitForAbort(1):
    #         # Abort was requested while waiting. We should exit
    #         footprints(False)
    #         break

    footprints(False)

