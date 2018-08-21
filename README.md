# OctoPrint-JamSentry

This plugin provides support for JamSentry, a DIY sensor for detecting filament jam and runout conditions.
No printer hardware or firmware changes are required to use the sensor.  Information on how the concept
behind JamSentry and detailed instructions on how to build one can be found at: https://robogardens.com/?p=2220

JamSentry is a compact device consisting of a microprocessor (ES8266), a filament movement sensor, and a
magnetometer.  The magnetometer attaches to the side of the extruder motor and detects when the motor is driving.
Basically, if the motor is driving and the filament isn't moving, then you have a jam or have run out
of filament.  On detection of this condition the JamSentry can:
 1. Raise (or lower) a line to provide a hardware indication emulating a filament runout switch
 2. Send a message to the GCODE sender alerting it to the situation (this plugin implements the receiver)
 3. Send an alert of the condition (IFTTT is used)
 
The JamSentry is a WiFi device and is configured via a web interface.  For convenience, the JamSentry
plugin makes this status webpage available as a tab.

## Setup

Install via the bundled [Plugin Manager](https://github.com/foosel/OctoPrint/wiki/Plugin:-Plugin-Manager)
or manually using this URL:

    https://github.com/percy9427/OctoPrint-JamSentry/archive/master.zip

Nothing special is required to install the plugin.

## Configuration

The JamSentry detects filament jams and runouts.  When detected an alert is sent to the octoprint unit on a given port.
A password is also sent along to ensure that it is a legitimate JamSentry alert.  To receive the alert properly,
the following must be setup in the octoprint JamSentry plugin settings:
 1. The address of the JamSentry (typically http://192.168.1.xxx).  If the printer has multiple JamSentry units
 (one per extruder), then only one can be displayed.  However JamSentry will still receive alerts from all units.
 The status can be displayed on a separate webpage.  It isn't necessary to setup this parameter, but by having
 the JamSentry status available as a tab, it just makes things easier.
 2. The port to listen on.  This defaults to 27100.  You can change the default that JamSentry uses.  The JamSentry
 plugin must be configured to listen on whatever port the JamSentry uses to send the alert.
 3. Password. Since a jam detection will likely pause the print, you want to make sure it isn't a prankster.  A
 password can be set in the JamSentry.  If so, Octoprint must have the same password set so that it can authenticate
 the message.  The default password is "JamSentryPSWD".
 4. Custom GCode to send when a jam or filament runout is detected.
 5. Whether or not to pause when a jam or filament runout is detected.  If used, then GCODE for pause and resume should
 be set up in the GCODE Scripts in the Octoprint settings.  Note that pause should be avoided in Octoprint versions
 1.3.7 and 1.3.8 as it does not work reliably.
 
 NOTE:
 For the GCODE Script for Pause, I use the following:
    ; relative XYZE
    G91
    M83

    ; retract filament, move Z slightly upwards
    G1 Z+5 E-5 F4500 

    ; absolute XYZE
    M82
    G90

    ; move to a safe rest position, adjust as necessary
    G1 X0 Y0          

For the GCODE Script for Resume, I use the following:
	; relative extruder
	M83

	; prime nozzle
	G1 E-5 F4500
	G1 E5 F4500
	G1 E5 F4500

	; absolute E
	M82

	; absolute XYZ
	G90

	; reset E
	G92 E{{ pause_position.e }}

	; move back to pause position XYZ
	G1 X{{ pause_position.x }} Y{{ pause_position.y }} Z{{ pause_position.z }} F4500

	; reset to feed rate before pause
	G1 {{ pause_position.f }}