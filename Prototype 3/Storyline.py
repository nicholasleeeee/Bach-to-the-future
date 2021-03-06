from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = ''
import pygame
import rgb
from UIManager import TextLine, TextBox
from state_manager import State_Manager, BaseState, ExitState, MainMenuState
import json
import vlc
from data_parser import get_config

class StoryState(BaseState):
	def __init__(self, fsm):
		super().__init__(fsm)
		#self.action_manager.add_button("Back", (50, 50), (50, 30))
		self.action_manager.add_keystroke("space", "space", ret= "Advance")
		self.action_manager.add_keystroke("enter", "return", ret= "Advance")
		self.action_manager.add_keystroke("Vol+", "up")
		self.action_manager.add_keystroke("Vol-", "down")
		self.font1= pygame.font.Font(self.fsm.SYSFONT, 22)
		self.font2= pygame.font.Font(self.fsm.SYSFONT, 14)
		self.title= TextLine("StoryState", self.font1, (400, 50)).align_ctr()
		self.curr_text= ""
		self.text_len= 0
		self.curr_text_box= TextBox(self.curr_text , self.font2, (50, 350), (700, 250))
		self.curr_frame= 0
		self.max_frame= 0
		self.scripts= []
		self.isDone= True
		self.forceDone= False
	
	def enter(self, args):
		self.background.fill(rgb.BLACK)
		with open(args["file"]) as file:
			self.script= json.load(file)
		self.curr_line= 0
		self.max_line= len(self.script)
		self.volume= int(get_config()["Default Volume"]["Value"])
		self.player= None

	def update(self, game_time, lag):
		actions= self.action_manager.chk_actions(pygame.event.get())
		for action in actions:
			if action == "Exit":
				self.fsm.ch_state(ExitState(self.fsm))
			elif action == "Back":
				self.fsm.ch_state(MainMenuState(self.fsm))
			
			elif action == "Vol+":
				self.volume += 1
				if self.player is not None:
					self.player.audio_set_volume(self.volume)
				print(f"Volume : {self.player.audio_get_volume()}")
			
			elif action == "Vol-":
				self.volume= max(0, self.volume-1)
				if self.player is not None:
					self.player.audio_set_volume(self.volume)
				print(f"Volume : {self.player.audio_get_volume()}")
			
			elif action == "Advance":
				if self.isDone:
					if self.curr_line == self.max_line:
						print("Scene completed!")
						self.fsm.ch_state(MainMenuState(self.fsm))
					else:
						self.advance(self.script[self.curr_line])
						self.curr_line += 1
				else:
					self.forceDone= True
					self.curr_frame= self.max_frame
		
		self.curr_text_pos= min(self.curr_frame, self.text_len)
		self.curr_text_box= TextBox(self.curr_text[:self.curr_text_pos] , self.font2, (50, 350), (700, 250))
		self.curr_frame += 1
		if self.curr_frame >= self.max_frame:
			self.isDone= True
		for script_code in self.scripts:
			exec(script_code)
		
	def advance(self, commands):
		self.curr_frame= 0
		self.max_frame= 0
		self.isDone= False
		self.forceDone= False
		self.scripts= []
		self.curr_text= ""
		for command in commands:
			print(command)
			if command["Type"] == "Title":
				self.title= TextLine(command["Text"], self.font1, (400, 50)).align_ctr()
			elif command["Type"] == "Speech":
				self.curr_text= command["Text"]
				self.text_len= len(self.curr_text)
				
			elif command["Type"] == "Audio Start":
				if self.player is not None:
					self.player.stop()
				self.player= vlc.MediaPlayer("Sheep may safely graze.ogg")
				self.player.play()
			
			elif command["Type"] == "Audio Stop":
				pygame.mixer.music.stop()
			
			elif command["Type"] == "Script":
				
				with open(command["File"]) as script_file:
					script_code= script_file.read()
				self.scripts.append(script_code)
				exec(command["Init"])
				self.max_frame= max(self.max_frame, command["max_frame"])
				
			elif command["Type"] == "Background":
				with open("fadein.py") as script_file:
					script_code= script_file.read()
				self.scripts.append(script_code)
				self.curr_alpha= 0
				self.bg_copy= self.background.copy()
				self.fade_spd= 2
				self.mask= pygame.image.load(command["File"]).convert()
				self.max_frame= max(self.max_frame, 128)

		self.max_frame= max(self.max_frame, self.text_len)
	
	def draw(self):
		self.fsm.screen.fill(rgb.BLACK)
		self.fsm.screen.blit(self.background, (0,0))
		self.action_manager.draw_buttons(self.fsm.screen)
		self.title.draw(self.fsm.screen)
		self.curr_text_box.draw(self.fsm.screen)
	
	def exit(self):
		if self.player is not None:
			self.player.stop()

if __name__ == "__main__":
	
	fsm = State_Manager()
	fsm.curr_state = MainMenuState(fsm)
	fsm.ch_state(StoryState(fsm), {"file" : "storyline.json"})
	while True:
		fsm.update()