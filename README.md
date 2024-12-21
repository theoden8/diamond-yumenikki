# installing VM

(go to ./dataset)

1. Download xubuntu-24 as iso file (xfce4 is using x11, not wayland).
2. Run `./run_xfce_img.sh`:
3. If './yume-nikki-vm.qcow2' doesn't exist, it will run the installer. You can automate the process using:

![xubuntu-installer](./images/xubuntu-installer.png)

    * No need for third-party software and such
    * Do not require password to log in

4. If `./yume-nikki-vm.qcow2` does exist, it will boot the system.
5. Log into your user (e.g. user: dweam password: dweam) and run:
```bash
# disable password prompts for the user in /etc/sudoers:
$ sudo vi /etc/sudoers
# - %sudo ALL=(ALL:ALL) ALL
# + %sudo ALL=(ALL:ALL) NOPASSWD: ALL
# :x!
$ sudo apt install openssh-server
$ sudo systemctl enable ssh
$ sudo systemctl start ssh
```
6. Run yume-nikki with wine:
```
cd ~/yumenikki
wine RPG_RT.exe
# install wine-mono when prompted
```
7. Disable display power management or suspension in Settings > Power Management.
8. Run `python3 capture_data.py` in the home directory.

To start recording, press 't'. This will generate `./data/video_{id:04d}/` which will be periodically rsync'ed to host to free up space on the VM.

# training

1. Create dweam conda environment and add it as ipython kernel accessible in jupyter.
2. Run `YN-Dataset.ipynb` (so that dataset is created)
3. Run `./preprocess_data.sh` to put all hdf5 files into .tar.gz archive (alternatively, you can download the archive from huggingface and don't need steps 2 and 3).
4. Edit AI-MarioKart64/diamond/configs/training.yaml, set wandb stuff:
```yaml
wandb:
  mode: online
  ...
```
5. Run `wandb login` and paste API key.
6. Run `python src/main.py`
  * On RTX4090 (24GB VRAM) set denoising acc=6 batch=10 upsampler acc=1 batch=1
7. To explore a model checkpoint, run `YN-run.upynb` (basically get spawn locations)
8. To run it, use the src/play.py but change `path_ckpt` and `spawn_dir` to your spawn and checkpoint locations.
