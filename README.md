wing-wakatime
=============

Metrics, insights, and time tracking automatically generated from your programming activity.


Installation
------------

1. Run `install.py`:

  **Mac and Linux**

  `curl -fsSL https://raw.githubusercontent.com/wakatime/wing-wakatime/master/install.py | python`

  **Windows**

  Download and extract [wing-wakatime-master.zip](https://github.com/wakatime/wing-wakatime/archive/master.zip), then double click `install.py`.

2. Restart Wing.

3. Enter your [api key](https://wakatime.com/settings), then press `enter`. If not prompted, select File -> WakaTime.

4. Use Wing and your time will be tracked for you automatically.

5. Visit https://wakatime.com/dashboard to see your logged time.


Screen Shots
------------

![Project Overview](https://wakatime.com/static/img/ScreenShots/Screen-Shot-2016-03-21.png)


Troubleshooting
---------------

First, turn on debug mode in your `~/.wakatime.cfg` file by adding this line:

`debug = true`

Then, look for error messages in the Messages window at the bottom.

Also, tail your `$HOME/.wakatime.log` file to debug wakatime cli problems.

For more general troubleshooting information, see [wakatime/wakatime#troubleshooting](https://github.com/wakatime/wakatime#troubleshooting).
