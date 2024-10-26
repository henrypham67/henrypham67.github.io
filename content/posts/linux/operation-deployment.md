# Operation Deployment

1. reboot
2. poweroff

--force \
--force --force

sudo shutdown <hh:MM>
sudo shutdown +<mins>
sudo shutdown -r <hh:MM>
sudo shutdown -r +<mins>
sudo systemctl reboot
sudo shutdown <hh:MM> "Wall message, show people why it's being shutdown/reboot"

`systemctl set-default multi-user.target`

`systemctl isolate graphical.target`

`systemctl isolate emergency.target`

root read-only

`rescue.target`

root shell

## script

when to and not add `.sh` extension to a file?

1st line = #1 (shebang) + path to the intepreter

`test` command check file types and compare values

return 0 -> success

other -> fail

## process

units, an instructions to know how to do its job:

- service: tell the system how it should manage the a certain app lifecycle
- socket
- device
- timer

