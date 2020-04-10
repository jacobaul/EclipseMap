```
usage: EclipseMap \[-h\] \[-d DURATION | -s | -e END\] \[-r RESOLUTION\] \[-t TIME_RESOLUTION\] \[-p STEP\] \[-f PREFIX\] \[-v | -q\] start

Generate maps of eclipse brightness across the earth

positional arguments:
  start                 Start Date (y-m-d-H-M-S)

optional arguments:
  -h, --help            show this help message and exit
  -d DURATION, --duration DURATION
                        Generate maps every (TIME-RESOLUTION) from (start) until (start)+duration (seconds)
  -s, --single          Calculate single map for (start) only
  -e END, --end END     Generate maps from (start) until (end) (y-m-d-H-M-S)
  -r RESOLUTION, --resolution RESOLUTION
                        Specify map resolution in pixels per lat/lon
  -t TIME_RESOLUTION, --time-resolution TIME_RESOLUTION
                        Generate map every (t) seconds
  -p STEP, --step STEP  Step size in seconds during coarse eclipse search
  -f PREFIX, --prefix PREFIX
                        Filename prefix
  -v, --verbosity       Verbose output. Useful for long time periods.
  -q, --quiet           Supress all output

```