# cycling-cadence-display

A terminal user interface for displaying information about a bike cadence sensor that connects via Bluetooth.

# Installation
To install from pypi:
```
pip3 install --user cycling-cadence-display
```

Note: the package `gnuplot` must be installed separately on the host where this will run. For Debian, Ubuntu et al  this will do it:

```
sudo apt install gnuplot
```

# Running the app

```
> cycling_cadence_display --help
usage: A TUI to display a dashboard of information about a  cycling cadence meter including the RPM over time [-h] --device-address DEVICE_ADDRESS

optional arguments:
  -h, --help            show this help message and exit
    --device-address DEVICE_ADDRESS
```

# Development
```
# create a virtualenv and start using it
python3 -m venv venv
. venv/bin/activate

# install the dependencies etc.
python3 seetup.py develop


# run the test-suite
pytest
```
