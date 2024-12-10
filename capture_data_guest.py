#!/usr/bin/env python


import os
import sys
import shutil
import subprocess
import typing
import time
import threading
import random
import re
import json
import base64

import numpy as np
import cv2
import PIL
import PIL.Image
import mss
import Xlib
import Xlib.display

import openai


class Agent:
    def __init__(self, skip_intro=False) -> None:
        if skip_intro:
            self.index = 0
            self.key_sequence = [
                #'alt+Return',
                'space', None, 'space', None, 'space', None,
                'space', None, 'space', None, 'space', None,
                'space', None, 'space', None, 'space', None,
                'space', None, 'space', None, 'space', None,
            ]
        else:
            self.index = 0
            self.key_sequence = []
        self.llm_max_retries = 5
        self.llm_retries = 0
        try:
            self.client = openai.OpenAI(
                base_url="http://127.0.0.1:21090/v1",
                api_key="-",
            )
            self.llm_retries = self.llm_max_retries
        except Exception as e:
            self.client = None

    @staticmethod
    def image_to_base64(image_path: str) -> bytes:
        with PIL.Image.open(image_path) as img:
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode('utf-8')

    def get_random_keypress(self, no_skip=False):
        for i in range(2):
            key = random.choice([
                'Right', 'Left', 'Up', 'Down',
                'z', None,
            ])
            if no_skip and key is None:
                continue
            break
        return key, random.uniform(0.1, 1.0), 'press'

    def get_llm_keypress(self, frame_path: str):
#        class Key(str, enum.Enum):
#            up = "up"
#            down = "down"
#            left = "left"
#            right = "right"
#            interact = "z"
#
#        class Action(pydantic.BaseModel):
#            key: Key
#            duration: float

#        keys = {
#            Key.up: "Up",
#            Key.down: "Down",
#            Key.left: "Left",
#            Key.right: "Right",
#            Key.interact: 'z',
#        }
        action_keys = dict(
            up="Up", down="Down", left="Left", right="Right",
            interact="z",
        )
        try:
            completion = self.client.chat.completions.create(
                model="llm",
                temperature=0.9,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Which button would you press playing the Yume Nikki game given this screenshot?\n"},
                            {"type": "image_url", "image_url": {"url": f'data:image/png;base64,{image_to_base64(frame_path)}'}},
                        ],
                    },
                ],
                request_timeout=3.,
                extra_body={"guided_choice": list(action_keys.keys())},
            )
            key = action_keys[completion.choices[0].message.content]
            self.llm_retries = self.llm_max_retries
            return key, random.uniform(0.1, 1.0), 'press'
        except Exception as e:
            self.llm_retries -= 1
            return self.get_random_keypress()

    def get_key(self, frame_path: typing.Optional[str]):
        if self.index < len(self.key_sequence):
            key = self.key_sequence[self.index]
            self.index += 1
            return key, .3, 'press'
        return self.get_random_keypress()
#        if self.llm_retries <= 0 or frame_path is None:
#            return self.get_random_keypress()
#        return self.get_llm_keypress(frame_path=frame_path)


class Game(object):
    def __init__(self, exe_file: str, exe_dir: str, window_name: str) -> None:
        self.exe_file = exe_file
        self.exe_dir = exe_dir
        self.window_name = window_name
        self.game_process = None
        self.screen_window_id, self.control_window_id = None, None
        self.key_record = 't'
        self.recording = False
        self.running = False
        self.agent = Agent(skip_intro=self.recording)
        self.now = 0
        self.now_time = time.time()
        self.delta_t = 0
        self.fps = 24
        self.pressed_keys = set()
        self.releasing_keys = set()
        self.frame_path = None

    def attach(self) -> None:
        while not self.screen_window_id or not self.control_window_id:
            time.sleep(1)
            self.set_window_id()
        print("Game screen window ID:", self.screen_window_id)
        print("Game control window ID:", self.control_window_id)
        geometry = self.get_window_geometry()
        print("Window geometry:", geometry)
        self.running = True

    def launch(self) -> None:
        # Launch the game via Wine
        self.game_process = subprocess.Popen(["wine", self.exe_file], cwd=self.exe_dir)
        self.attach()

    def set_window_id(self) -> None:
        # Use xdotool to search for window
        try:
            output = subprocess.check_output(['xdotool', 'search', '--name', self.window_name])
            window_ids = output.strip().split()
            if window_ids:
                for window_id in window_ids:
                    window_id = window_id.decode()
                    if window_id.startswith('0x'):
                        window_id = int(window_id, 16)
                    else:
                        window_id = int(window_id)
                    geometry = self.get_window_geometry(window_id=window_id)
                    if geometry['width'] == 1 and geometry['height'] == 1:
                        self.control_window_id = window_id
                    else:
                        self.screen_window_id = window_id
        except subprocess.CalledProcessError:
            return

    def get_window_geometry(self, window_id=None) -> dict:
        if window_id is None:
            window_id = self.screen_window_id
        try:
            output = subprocess.check_output(['xwininfo', '-id', str(window_id)]).decode()
            geometry = dict()
            for line in output.splitlines():
                if 'Absolute upper-left X:' in line:
                    geometry['x'] = int(line.split()[-1])
                elif 'Absolute upper-left Y:' in line:
                    geometry['y'] = int(line.split()[-1])
                elif 'Width:' in line:
                    geometry['width'] = int(line.split()[-1])
                elif 'Height:' in line:
                    geometry['height'] = int(line.split()[-1])
            self.last_geometry = geometry
            return geometry
        except subprocess.CalledProcessError:
            self.running = False
            return self.last_geometry

    def step(self) -> None:
        now_time = time.time()
        self.delta_t = now_time - self.now_time
        delta_delta_t = (1. / self.fps) - self.delta_t
        if delta_delta_t > 0:
            time.sleep(delta_delta_t)
        self.now_time = now_time
        self.now += 1
        self.releasing_keys = set()

    def capture_window(self) -> np.ndarray:
        keys = list(set.union(self.pressed_keys, self.releasing_keys))
        geometry = self.get_window_geometry()
        with mss.mss() as sct:
            img = np.array(sct.grab(dict(
                top=geometry['y'],
                left=geometry['x'],
                width=geometry['width'],
                height=geometry['height'],
            )))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2RGB)
            return keys, frame

    def screencast_loop(self) -> None:
        if not os.path.exists('./data'):
            os.makedirs('./data')
        video_name = None
        for i in range(10000):
            video_name = f'./data/video_{i:04d}'
            if not os.path.exists(video_name):
                os.makedirs(video_name)
                break
        print('SCREENCAST ON')
        start = time.time()
        j = dict()
        while self.running:
            if not self.recording:
                continue
            now = self.now
            keys, frame = self.capture_window()
            tmpfile = f'/tmp/capture-{os.getpid()}-{random.randint(0, int(1e12))}.jpg'
            PIL.Image.fromarray(frame).save(tmpfile)
            frame_path = os.path.join(video_name, f'frame_{now:06d}.jpg')
            shutil.move(tmpfile, frame_path)
            self.frame_path = frame_path
            cv2.putText(frame, str(keys), (50,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, str(now), (250,50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            PIL.Image.fromarray(frame).save(tmpfile)
            shutil.move(tmpfile, os.path.join(video_name, f'image_{now:06d}.jpg'))
            self.step()
            j[now] = dict(
                keys=keys,
                elapsed=self.delta_t,
            )
#            cv2.imshow("Game Screencast", frame)
#            if cv2.waitKey(1) & 0xFF == ord('q'):
#                break
            if now % 100 == 0:
                print('now', now, now / (time.time() - start))
            if now == 200000:
                self.running = False
                self.recording = False
        tmpfile = f'/tmp/writejson-{os.getpid()}-{random.randint(0, int(1e12))}.json'
        with open(tmpfile, 'w') as f:
            json.dump(j, f)
        shutil.move(tmpfile, os.path.join(video_name, f"actions.json"))
        cv2.destroyAllWindows()
        print('screencast done')

    def send_actions_loop(self) -> None:
        time.sleep(3)
        while self.running:
            if not self.recording:
                continue
            key, wait_time, press = self.agent.get_key(frame_path=self.frame_path)
            print('sending', key)
            window_id = self.control_window_id
            if press == 'single':
                time.sleep(wait_time)
                if key is not None:
                    r = subprocess.call(['xdotool', 'key', '--window', str(window_id), '--delay', '0', key])
                    if r != 0:
                        self.running = False
                        return
            elif press == 'press':
                if key is not None:
                    r = subprocess.call(['xdotool', 'keydown', '--window', str(window_id), key])
                    if r != 0:
                        self.running = False
                        return
                time.sleep(wait_time)
                if key is not None:
                    r = subprocess.call(['xdotool', 'keyup', '--window', str(window_id), key])
                    if r != 0:
                        self.running = False
                        return
        print('sendkeys done')

    def set_key_press(self, key: str) -> None:
        if key == self.key_record:
            self.recording = True
            return
        elif self.recording and key not in self.pressed_keys:
            self.pressed_keys.add(key)

    def set_key_release(self, key: str) -> None:
        if not self.recording or key == self.key_record:
            return
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        if key not in self.releasing_keys:
            self.releasing_keys.add(key)

    def xev_parser(self, window_id: int) -> None:
        # Start xev with the given window ID
        # -id <window_id> attaches xev to that window
        process = subprocess.Popen(["xev", "-id", str(window_id), '-event', 'keyboard'],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   text=True,
                                   universal_newlines=True)
        os.set_blocking(process.stdout.fileno(), False)
        os.set_blocking(process.stderr.fileno(), False)

        # Regex patterns to identify key press/release lines
        key_press_pattern = re.compile(r"KeyPress event, serial \d+, synthetic .*, window 0x[0-9a-fA-F]+")
        key_release_pattern = re.compile(r"KeyRelease event, serial \d+, synthetic .*, window 0x[0-9a-fA-F]+")
        keysym_pattern = re.compile(r"state 0x[0-9a-fA-F]+, keycode (\d+) \(keysym 0x([0-9a-fA-F]+), (.+)\)")

        def key_event_params(line):
            line = line.strip()
            kv_pairs = line.strip(',')
            info = dict()
            for kv in kv_pairs:
                args = kv.strip().split(' ')
                if len(args) == 2:
                    k, v = args
                    info[k.strip()] = v.strip()
            return info

        # Continuously read lines from xev
        current_action = None
        while self.running:
            line = process.stdout.readline()
            if not line:  # Process finished or no more output
                continue

            line = line.strip()

            # Check for key press
            if key_press_pattern.match(line) or key_release_pattern.match(line):
                params = key_event_params(line).get('synthetic', 'unknown')
                synthetic = dict(
                    YES=True,
                    NO=False,
                    unknown=None,
                )[key_event_params(line).get('synthetic', 'unknown')]
                if key_press_pattern.match(line):
                    current_action = dict(
                        event_name='KeyPress',
                        start=self.now,
                        synthetic=synthetic,
                    )
                # Check for key release
                elif key_release_pattern.match(line):
                    if current_action is None:
                        current_action = dict(
                            event_name='KeyRelease',
                            start=self.now,
                            synthetic=synthetic,
                        )
                    assert current_action['synthetic'] == synthetic
                    current_action['stop'] = self.now
                    print(current_action)

            # keysym
            match = keysym_pattern.search(line)
            if match:
                keycode = match.group(1)
                keysym_hex = match.group(2)
                keysym_name = match.group(3)
                print(f"KeyPress: keycode={keycode}, keysym=0x{keysym_hex} ({keysym_name})")
                current_action['keycode'] = keycode
                current_action['keysym'] = keysym_name
                if 'stop' not in current_action:
                    self.set_key_press(keysym_name)
                else:
                    current_action = None
                    self.set_key_release(keysym_name)
        print('xev_server', window_id, 'done')
        process.terminate()

    def capture(self) -> None:
        threads = [
            threading.Thread(target=game.screencast_loop),
            threading.Thread(target=game.send_actions_loop),
            threading.Thread(target=game.xev_parser, args=(game.control_window_id,)),
            threading.Thread(target=game.xev_parser, args=(game.screen_window_id,)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        game.game_process.terminate()


if __name__ == "__main__":
    # launch game
    game = Game(
        exe_dir='/home/dweam/yumenikki',
        exe_file='RPG_RT.exe',
        window_name="YUME NIKKI",
    )
    game.launch()
    game.capture()
