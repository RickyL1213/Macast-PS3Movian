# Copyright (c) 2022 by RickyL1213. All Rights Reserved.
#
# Macast Movian media renderer
#
# Macast Metadata
# <macast.title>Movian Renderer</macast.title>
# <macast.renderer>MovianRenderer</macast.renderer>
# <macast.platform>darwin,linux,win32</macast.platform>
# <macast.version>0.1</macast.version>
# <macast.author>RickyL1213</macast.author>
# <macast.desc>Macast Movian media renderer</macast.desc>


import os
import time
import threading
import cherrypy
import subprocess
import requests
import urllib.parse
from macast.utils import Setting
from macast.renderer import Renderer


class MovianRenderer(Renderer):
    ps3_ips = Setting.get_ps3_ips()
    current_volume = 0
    def __init__(self):
        super(MovianRenderer, self).__init__()
        self.start_position = 0
        self.position_thread_running = True
        self.position_thread = threading.Thread(target=self.position_tick, daemon=True)
        self.position_thread.start()

    def position_tick(self):
        while self.position_thread_running:
            time.sleep(1)
            self.start_position += 1
            sec = self.start_position
            position = '%d:%02d:%02d' % (sec // 3600, (sec % 3600) // 60, sec % 60)
            self.set_state_position(position)
            self.current_volume = self.get_state("Volume")

    def set_media_pause(self):
        print("Movian pause")
        self.set_state_transport('PAUSED_PLAYBACK')
        for ip in self.ps3_ips:
            self.try_get(f'http://{ip}:42000/showtime/input/action/pause')

    def set_media_resume(self):
        print("Movian play")
        self.set_state_transport("PLAYING")
        for ip in self.ps3_ips:
            self.try_get(f'http://{ip}:42000/showtime/input/action/play')

    def set_media_volume(self, data):
        print("Movian volume=-=-=-=-=-=-=-")
        print(data)
        print(self.current_volume)
        if data > self.current_volume:
            for ip in self.ps3_ips:
                self.try_get(f'http://{ip}:42000/showtime/input/action/VolumeUp')
        elif data < self.current_volume:
            for ip in self.ps3_ips:
                self.try_get(f'http://{ip}:42000/showtime/input/action/VolumeDown')

        # """ data : int, range from 0 to 100
        # """
        # self.send_command(['set_property', 'volume', data])

        # self.set_media_text(f'Volume: {data}')
    
    def set_media_stop(self):
        for ip in self.ps3_ips:
            self.try_get(f'http://{ip}:42000/showtime/input/action/stop')
        self.set_state_transport('STOPPED')
        cherrypy.engine.publish('renderer_av_stop')

    def set_media_url(self, url):
        self.set_media_stop()
        self.start_position = 0
        # stop current play and return to home(exist screensaver)
        for ip in self.ps3_ips:
            self.try_get(f'http://{ip}:42000/showtime/input/action/stop')
            self.try_get(f'http://{ip}:42000/showtime/input/action/home')
        print(url)
        self.set_state_transport("PLAYING")
        for ip in self.ps3_ips:
            self.try_get(f'http://{ip}:42000/?url='+urllib.parse.quote(url))
        cherrypy.engine.publish('renderer_av_uri', url)

    def try_get(self,url):
        try:
            requests.get(url, verify=False, timeout=0.5)
        except:
            print(f"failed to requests on some PS3 {url}")


    def stop(self):
        super(MovianRenderer, self).stop()
        self.set_media_stop()
        print("Movian stop")
        cherrypy.engine.publish('renderer_av_stop')

    def start(self):
        super(MovianRenderer, self).start()
        print("Movian start")


if __name__ == '__main__':
    cli(MovianRenderer())
