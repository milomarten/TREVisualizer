# TRE Simulator
(It's for TEXRail too)

The goal of this project was to create an animated visualization
that showed how the trains of the TRE and TEXRail systems interact
with themselves and one another. In both systems, most of the line
is single tracked, meaning that some measure of synchronicity is
required to make sure trains don't collide.

![Simulation Output](output.gif "Simulation Output")

## How does it work?
As input, the schedules are parsed from a tab-separated CSV file,
in `schedules/`. Each schedule is broken up into eastbound
and westbound. The first line (unused) should have the station names.
Each additional line is then the train number, followed by the departure
time for each station, in HH:MM format. Skipped stations should use `--:--` as the time.
Times that roll over to the next day should have a `#` appended.

Note that the code doesn't handle skipping stations.

At the end of the simulation, it will ask if you want the results
exported as a GIF. The output is `output.gif`. The end GIF does not take
into account pausing, or stepping through the minutes.

Please be patient...it is a long GIF, and takes
about 15 seconds to export. 

## What am I seeing?
The simulation will show a simplified map of the systems:
* Red squares indicate TRE trains
* Blue squares indicate TEXRail trains
* Purple squares indicate trains finished with their last route, but not yet on another. Both systems, during off-peak hours, store trains in their respective yards.
  * The "darkness" of purple is a rough indicator of quantity. Pure fuchsia means one, medium fuchsia means two, and dark means three or more.
* Each black-outlined circle represents a station.
  * The yellow-filled circle indicates the fare boundary for TRE. Crossing this boundary costs an additional fare.
* The top left corner shows the current time, in 24-hour format.
* The top right corner shows a summary for each system:
  * The number of currently running trains
  * The number of trains in the system idling: This only includes the termini of each system.
* The application itself has several buttons:
  * "Start" will begin the simulation. 
  * "Pause" or "Resume" will temporarily halt and resume the simulation.
  * "+1 Minute" will step to the next minute while the simulation is paused.
  * "Music ON" or "Music OFF" will turn music on or off.
  * "Reset" will revert the simulation to the beginning.

## What am I hearing?
For a lark, the application will play a piano note each time a train
enters a station. The notes correspond to the circle of fifths; TRE
uses the major scale, and TEXRail the minor scale. Using this sequence of notes
makes the music somewhat more pleasant to hear, but I haven't done
much to fine-tune it.

Music can be turned off with the "Music OFF" button.

## Prerequisites?
* Tkinter is used to display the UI
* Pillow is used to output to GIF
* pygame is used to play audio