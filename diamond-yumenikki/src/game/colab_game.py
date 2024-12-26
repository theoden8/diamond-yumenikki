from typing import Tuple, Union

import numpy as np
from PIL import Image

from ..csgo.action_processing import CSGOAction
from .dataset_env import DatasetEnv
from .play_env import PlayEnv
from IPython.display import display, clear_output
from ipywidgets import widgets
from IPython.display import clear_output
from IPython.display import display
import time


steering_value = 0.0
stop_task = False
output = None

class ColabGame:
	def __init__(
		self,
		play_env: Union[PlayEnv, DatasetEnv],
		size: Tuple[int, int],
		mouse_multiplier: int,
		fps: int,
		verbose: bool,
	) -> None:
		self.env = play_env
		self.height, self.width = size
		self.mouse_multiplier = mouse_multiplier
		self.fps = fps
		self.verbose = verbose

		print("\nControls:\n")
		print(" m  : switch control (human/replay)") # Not for main as Game can use either PlayEnv or DatasetEnv
		print(" .  : pause/unpause")
		print(" e  : step-by-step (when paused)")
		print(" ⏎  : reset env")
		print("Esc : quit")
		print("\n")

	def on_slider_change(self, change):
		global steering_value
		steering_value = change['new']  # Update the global variable

	def stop_monitoring(self, change):
		global stop_task
		stop_task = True  # Set the flag to stop the task

	def run(self) -> None:
		global steering_value, output
		cooldown = float(input("Time between frames: "))

		output = widgets.Output()
		display(output)
		def draw_obs(obs, obs_low_res=None):
			assert obs.ndim == 4 and obs.size(0) == 1
			img = Image.fromarray(obs[0].add(1).div(2).mul(255).byte().permute(1, 2, 0).cpu().numpy())
			with output:
				clear_output(wait=True)
				display(img)
			#plt.imshow(obs[0].add(1).div(2).mul(255).byte().permute(1, 2, 0).cpu().numpy(), interpolation='nearest')
			#plt.show()
			#display(slider)

		def reset():
			nonlocal obs, info, do_reset, ep_return, ep_length, keys_pressed, l_click, r_click
			global steering_value
			obs, info = self.env.reset()
			do_reset = False
			ep_return = 0
			ep_length = 0
			keys_pressed = []
			steering_value = 0.0
			l_click = r_click = False

		reset()
		
		obs, info, do_reset, ep_return, ep_length, keys_pressed, l_click, r_click = (None,) * 8
		

		while not stop_task:
			if do_reset:
				reset()
			do_wait = False
			csgo_action = CSGOAction([], steering_value)
			next_obs, rew, end, trunc, info = self.env.step(csgo_action)
			time.sleep(cooldown)
			draw_obs(next_obs)
			if end or trunc:
				reset()

			else:
				obs = next_obs