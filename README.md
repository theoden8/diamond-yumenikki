# installing VM

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
7. Run `python3 capture_data.py` in the home directory.
