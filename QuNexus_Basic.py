#-----------------------------------------------#
#												#
#	Keith McMillen Instruments 2013				#
#												#
#	Authors: 									#
#		Sarah Howe	sarah@keithmcmillen.com 	#
#		Conner Lacy	conner@keithmcmillen.com	#
#												#
#-----------------------------------------------#


import Live #Now the Live API is available
import time #Now we can use time functions for time-stamping our log file outputs

from _Framework.ButtonElement import ButtonElement
from _Framework.ChannelStripComponent import ChannelStripComponent
from _Framework.ClipSlotComponent import ClipSlotComponent
from _Framework.CompoundComponent import CompoundComponent
from _Framework.ControlElement import ControlElement
from _Framework.ControlSurface import ControlSurface
from _Framework.ControlSurfaceComponent import ControlSurfaceComponent
from _Framework.InputControlElement import *
from _Framework.MixerComponent import MixerComponent
from _Framework.SceneComponent import SceneComponent
from _Framework.SessionComponent import SessionComponent
from _Framework.SessionZoomingComponent import SessionZoomingComponent
from _Framework.SliderElement import SliderElement
from _Framework.EncoderElement import EncoderElement
from _Framework.DeviceComponent import DeviceComponent
from _Framework.TransportComponent import TransportComponent

from QuNexusSessionComponent import QuNexusSessionComponent

#define global variables
CHANNEL = 8  #channels are numbered 0 - 15

class QuNexus_Basic(ControlSurface):
	__module__ = __name__
	__doc__ = "QuNexus Keyboard controller script"
	
	def __init__(self, c_instance):
		#everything except the '_on_selected_track_changed' override and 'disconnect' runs from here
		ControlSurface.__init__(self, c_instance)
		#Turn off rebuild MIDI map until after we're done setting up
		self.set_suppress_rebuild_requests(True)
		
		#set up some variables I want to use in multiple functions
		self.mixer = None
		self.session = None
		
		#Setup the mixer and session object
		self._setup_session_control()
		self._setup_mixer_control()
		self._setup_device_control()

		self.set_suppress_rebuild_requests(False)
		
		
	#note that we have split the mixer functions across two scripts, in order to have two session highlight boxes (one red, one yellow), so there are a few things which we are not doing here...
	def _setup_session_control(self):
		is_momentary = True
		num_tracks = 1 #one column (track)
		num_scenes = 8 #eight rows, which will be mapped to eight "white" notes
		
		#(num_tracks, num_scenes) a session highlight ("red box") will appear with any two non-zero values
		self.session = QuNexusSessionComponent(num_tracks,num_scenes)
		#(track_offset, scene_offset) Sets the initial offset of the "red box" from top left
		self.session.set_offsets(0,0)
		
		self.session.set_select_buttons(ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,63), ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,61))
		self.session.set_scene_bank_buttons(ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,51), ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,49))
		self.session.set_track_bank_buttons(ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,56), ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,54))
		
		self.session.set_stop_all_clips_button(ButtonElement(is_momentary, MIDI_NOTE_TYPE, CHANNEL, 58))
		for row in range(8):
			for col in range(1):
				self.session.scene(row).clip_slot(col).set_started_value(127)
				self.session.scene(row).clip_slot(col).set_stopped_value(0)
		
		#here we set up the clip launch assignments for the session	
		clip_launch_notes = [48,50,52,53,55,57,59,60] #set of eight white notes starting at C3/C4
		for index in range(num_scenes):
			#step though scenes and assign a note to first slot of each
			self.session.scene(index).clip_slot(0).set_started_value(127)
			self.session.scene(index).clip_slot(0).set_stopped_value(3)
			#self.session.scene(index).clip_slot(0).set_recording_value(64)
			self.session.scene(index).clip_slot(0).set_launch_button(ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,clip_launch_notes[index]))
		#here we set up a mixer and channel strip(s) which move with the session
		self.session.set_mixer(self.mixer)  #bind the mixer to the session so that they move together


	def _setup_mixer_control(self):
		is_momentary = True
		#A mixer is one-dimensional; here we define the width in tracks - seven columns, which we will map to the seven "white" notes
		num_tracks = 1
		#set up the mixer
		self.mixer = MixerComponent(num_tracks, 2, with_eqs=True, with_filters=True)  #(num_tracks, num_returns, with_eqs, with_filters)
		self.mixer.set_track_offset(0)  #sets start point for mixer strip (offset from left)
		#set the selected strip to the first track, so that we don't, for example, try to assign a button to arm the master track, which would cause an assertion error
		self.song().view.selected_track = self.mixer.channel_strip(0)._track
		#set up the mixer buttons
		#self.mixer.set_select_buttons(ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,68),ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,66)) #left, right track select

	def _on_selected_track_changed(self):

		ControlSurface._on_selected_track_changed(self)
		is_momentary = True
		#Get our currently selected Track Object
		selected_track = self.song().view.selected_track
		#typecast a tuple of all tracks into a list
		list_of_tracks = list(((self.song().tracks + self.song().return_tracks) + (self.song().master_track, )))
		#find out how many tracks there are total for use in the for loop below
		total_tracks = len(list_of_tracks)
		#Get index/int of currently selected Track Object by using the index method on the list of tracks
		selected_track_index = list_of_tracks.index(selected_track)
				
		#to prevent assertion errors I deassign the launch button for any track that is not the selected track, then assign the selected track
		for index in range(total_tracks):
			if index != selected_track_index:
				#self.log_message("************ De-assign this track's launch button: " + str(index) + "***********")
				self.session.selected_scene().clip_slot(index).set_launch_button(None)
			else:
				#self.log_message("************ assign this track's launch button: " + str(index) + "************")
				self.session.selected_scene().clip_slot(selected_track_index).set_launch_button(ButtonElement(is_momentary,MIDI_NOTE_TYPE,CHANNEL,70))
				
	def _setup_device_control(self):
		sliders = []
		pressures = [92,94,98,102,106,108]
		for index in range(6):
			sliders.append(SliderElement(MIDI_CC_TYPE, CHANNEL, pressures[index]))
			
		self._sliders = tuple(sliders)
		device = DeviceComponent()
		device.name = 'Device_Component'
		self.set_device_component(device)
		device.set_parameter_controls(self._sliders)

	def disconnect(self):
		#clean things up on disconnect
		
		#create entry in log file
		self.log_message(time.strftime("%d.%m.%Y %H:%M:%S", time.localtime()) + "----------QuNexus Basic log closed----------")
		
		ControlSurface.disconnect(self)
		return None
