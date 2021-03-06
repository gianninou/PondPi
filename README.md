# PondPi

## The project

This project is a controller for pumps and UV for a pond.
The PI0 will check the water level and cut off the pump if the level is low.

It is also possible to cut the UV or a pump for winter for example.

The PI is also connected to some temperature sensors.

Finally, if a camera is installed, pictures could be made of the pond or the filtration system for example and send via SFTP.

## basic schema

![PondPi schema](PondPi_schema.jpg)

## Installation

The git folder was copied into the `/home/pi/PondPi` folder.

A virtual env should be created : `python -m venv /home/pi/PondPi/pondpi-venv`

A virtual env could be created befor in order to have a clean environment for the application.  
Then install the requirements with `pip install -r requirements.txt`

Install the package : `sudo apt-get install libatlas-base-dev libopenjp2-7`


## Usage

### Configuration file

There is 5 sections in the config.yamlfile.  
- The global section contains some constants and should be adapter for your needed and your system.
- The mail section will contains all related conf in order to be able to send email for alert.
- The logs section will contains the name of logs files for the graph and running logs.
- The relays section will contains the relays or led. These devices are "OUT" type. For the moment the application only handle relays (for pumps or UV) and led for the state of the application.
- The section sensors will contains all input devices such as temperature, humidity or water level switch. Only some sensors are implemented. For other type of sensor a feature request could be made, or even a pull request :)

### Run the app

#### Init
The init command will initialize the GPIO in order to be set as IN or OUT state.

#### print
The print command will display the information about the sensors and the states of the OUT pin.

#### manage
The manage command allows to power up or shutdown the relays. That will be used in case of interv on the filter for example.
At each change of an OUT pin, a backup file is created. Therefor if the system crash or reboot, the state of the PIN is kept in the backup file.

#### cron
The cron command should be run at least every 15min. The aims is to check the water level and cut the pumps in case of issues. An email is send and the red led will be put ON if one is installed.

#### restore
The restore command allows to restore the state from the backup file. That is usefull after a reboot for example.

TODO : take a file in input in order to set the system at a special state (in case of a lot of pump and devices managed by relays for example).

#### reset
The reset command allows to remove the alert state of the application. The alerte state is raised by the cron command if the water level is low. When a check about the water level and the potential leak is made, the reset command should be used in order to remove the alert state and restore the system in a stable state.

### Crontable

The following cron line should be added to the pi user (if the pi is the user that used the tool)

Edit the crontab for the pi user with : `sudo crontab -u pi -e`

Then add the following line. You can remove the `--ftp` flags if you are no using the FTP.
The first line is for the water level check, the second for taking a screenshot and the last to create a gif with all image from yesterday (and clean it). 

<code>
*/15 * * * * /home/pi/PondPi/pondpi-venv/bin/python /home/pi/PondPi/PondPi/pondpi.py cron >/dev/null 2>&1  
*/15 * * * * /home/pi/PondPi/pondpi-venv/bin/python /home/pi/PondPi/PondPi/pondpi.py camera --capture --ftp >/dev/null 2>&1  
0 1 * * * /home/pi/PondPi/pondpi-venv/bin/python /home/pi/PondPi/PondPi/pondpi.py camera --gif-yesterday --ftp >/dev/null 2>&1  
</code>


## Improvements

- Generate some report about collected sensor data (temp/moisture/etc)
- Create a REST API.

## Contact

By mail : valentin@gianninou.fr

