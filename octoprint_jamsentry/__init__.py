# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin  # @UnresolvedImport
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer  # @UnresolvedImport
import json
import threading
import time

def AlertHandlerFactory(jamSentryInstance):
    class AlertHandler(BaseHTTPRequestHandler,object):
        def __init__(self, *args, **kwargs):
            self.jamSentryInstance=jamSentryInstance
            super(AlertHandler, self).__init__(*args, **kwargs)
            
                #Handler for the GET requests
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type','text/html')
            self.end_headers()
            self.wfile.write("<html><body><h1>GET!</h1></body></html>")
            return
    
        def do_POST(self):
            # Send the html message
            try:
                content_length = int(self.headers['Content-Length']) # <--- Gets the size of data
                post_data = self.rfile.read(content_length) # <--- Gets the data itself
                receivedFields=json.loads(post_data.decode("utf-8"))
                reportingMachine=receivedFields['value1']
                reportingExtruder=receivedFields['value2']
                passwordToMatch=receivedFields['value3']
                self.jamSentryInstance.jamMessageReceived(reportingMachine,reportingExtruder,passwordToMatch)
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                self.wfile.write("<html><body><h1>POST!</h1></body></html>")
            except:
                pass
            return
    return AlertHandler

class JamSentryPlugin(octoprint.plugin.StartupPlugin,
                       octoprint.plugin.TemplatePlugin,
                       octoprint.plugin.SettingsPlugin,
                       octoprint.plugin.AssetPlugin):
    
    @property
    def ipaddr(self):
        return str(self._settings.get(["ipaddr"]))

    @property
    def port(self):
        return int(self._settings.get(["port"]))

    @property
    def pswd(self):
        return str(self._settings.get(["pswd"]))

    @property
    def jam_gcode(self):
        return str(self._settings.get(["jam_gcode"]))

    @property
    def pause_print(self):
        return self._settings.get_boolean(["pause_print"])
    

    def get_assets(self):
        return dict(js=["js/jamsentry.js"],css=["css/jamsentry.css"])
    

    def get_settings_defaults(self):
        return dict(
            ipaddr     = "",   # Default address
            port  = 27100,  # Default listen port
            pswd  = 'JamSentryPSWD',    # Default password sent by JamSentry
            jam_gcode = '',
            pause_print = True,
        )

    def get_template_configs(self):
        return [dict(type="settings", custom_bindings=False)]

    def jamMessageReceived(self,machine,extruder,password):
        if password==self.pswd:
            self._logger.info("Jam Detected")
            if self.pause_print:
                self._logger.info("Pausing print.")
                self._printer.pause_print()
            if self.no_filament_gcode:
                self._logger.info("Sending out of filament GCODE")
                self._printer.commands(self.no_filament_gcode)
        else:
            self._logger.info("JamSentry message received, but password was invalid: " + str(password))

    def waitForJamSentryAlarm(self):
        time.sleep(1)  #Give it a second in case previous shutdown needs to finish
        self.waitForAlert=True
        server_address = ('', self.port)
        HandlerClass=AlertHandlerFactory(self)
        self.jamSentryServer = HTTPServer(server_address, HandlerClass)
        while self.waitForAlert:
            self.jamSentryServer.handle_request() 
                
    def stopWaitingForJamSentryAlarm(self):
        if self.jamSentryServer is None:
            return
        self.waitForAlert=False
        self.jamSentryServer.socket.close()
        self.jamSentrySever = None

    def on_settings_save(self, data):
        octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
#        print('Data being updated: ipaddr: ' + str(self.ipaddr) + ', port: ' + str(self.port) + ', pswd: ' + str(self.pswd))
        self.stopWaitingForJamSentryAlarm()
        self.jamsentryMontitorThread=threading.Thread(target=self.waitForJamSentryAlarm,name='Monitor JamSentry')
        self.jamsentryMontitorThread.start()
        self._logger.info("Listening for JamSentry alerts on port " +str(self.port))
    
    def on_after_startup(self):
        self.jamsentryMontitorThread=threading.Thread(target=self.waitForJamSentryAlarm,name='Monitor JamSentry')
        self.jamsentryMontitorThread.start()
        self._logger.info("JamSentry thread started to listening for alerts on port " +str(self.port))
                
__plugin_name__ = "JamSentry"
__plugin_implementation__ = JamSentryPlugin()