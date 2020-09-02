# -*- coding: utf-8 -*-

import xbmc
import time
from resources.lib.common import *

def run():

    footprints()

    # # Run until abort requested
    # while not kodi_monitor.abortRequested():
    #     if kodi_monitor.waitForAbort(1):
    #         # Abort was requested while waiting. We should exit
    #         footprints(False)
    #         break

    footprints(False)