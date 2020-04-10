# coding: utf-8
import png
import math
import ephem
import datetime
import argparse
import os

sun = ephem.Sun()
moon = ephem.Moon()

def log_level(message, priority):
    if(args.verbosity >= priority and not args.quiet):
        print(message)

# Write 2d list of lists of percentages to png.(0-100 mapped to 0-255 b+w)
def write_img(arr, filenumber):
    height = len(arr)
    width  = len(arr[0])

    if(args.prefix):
        filename = args.prefix + "-" + str(filenumber) + ".png"
    else:
        filename = str(filenumber) + ".png"

    normalized = []
    for i in range(height):
        normalized.append([])
        for j in range(width):
            normalized[i].append(round(arr[i][j] * 2.55))
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        f = open(filename, 'wb')

    #pypng library supports 2d list of lists.
    w = png.Writer(width, height, greyscale=True)

    log_level('Writing ' + filename +', size=' + str(width)+ "x" + str(height), 3)

    w.write(f, normalized)
    f.close()


# Calculate the area of the "lunes" and "lens" of intersecting circles.
def lune_areas(a,b,c):
    delta=0.25*math.sqrt((a+b+c)*(b+c-a)*(c+a-b)*(a+b-c))
    a1 =2*delta + (a*a)*(math.acos(((b*b)-(a**2)-(c*c))/(2*a*c))) - (b*b)*(math.acos(((b*b)+(c*c)-(a*a))/(2*b*c)))
    alens = math.pi * a**2 - a1
    a2 = math.pi * b**2 - alens
    return (a1,alens,a2)

#Percentage of sun's area visible from behind moon.
def lune_percentage(datetime, lon_str, lat_str):

    location = ephem.Observer()
    location.lon = lon_str
    location.lat = lat_str
    location.date = datetime

    sun.compute(location)
    moon.compute(location)

    r_sun = sun.size/2
    r_moon = moon.size/2
    angular_sep = math.degrees(ephem.separation((sun.az, sun.alt), (moon.az, moon.alt)))*3600

    r_sun_rad = r_sun / (3600*180) * math.pi
    if(float(sun.alt) < -r_sun_rad): #Sun below horizon
        return 0

    if (angular_sep > r_sun + r_moon): #No Eclipse
        return 0

    #Determine larger disk
    if(r_moon > r_sun):
        log_level("Moon larger in sky", 4)
        if(r_moon-r_sun > angular_sep): #Sun fully Eclipsed, lune calculation outside domain.
            lune_area = 100
        else:
            areas = lune_areas(r_sun,r_moon,angular_sep)
            lune_area = areas[0]

    else: #Annular Eclipse
        log_level("Sun larger in sky, Annular Eclipse", 4)
        if(r_sun-r_moon > angular_sep): #Lune calculation ouside domain. (Annulus)
            return (math.pi * r_sun**2) - (math.pi*r_moon**2)
        else:
            areas = lune_areas(r_moon,r_sun,angular_sep)
            lune_area = areas[2]


    lune_percent=(1-(lune_area/(math.pi*(r_sun**2))))*100

    return lune_percent

# Calculate brightness percentage in equirectangular grid over earth's surface.
def equirec_percentages(datetime, resolution = 1):
    eclipsed = False
    value_array = []
    for lat in range(0, 180*resolution):
        value_array.append([])
        for lon in range(0, 360*resolution):
            percentage = lune_percentage(datetime,str((lon / resolution) -180), str((lat / resolution)-90))
            if (percentage > 0):
                eclipsed = True
            value_array[lat].append(percentage)
    if(eclipsed):
        return value_array
    else:
        return False


# If angular separation > 1.7 degrees, eclipse impossible.
def eclipse_impossible(datetime):
    location = ephem.Observer()
    location.lon = "0"
    location.lat = "0"
    location.elevation = -6378100
    location.date = datetime

    sun.compute(location)
    moon.compute(location)

    angular_sep = math.degrees(ephem.separation((sun.az, sun.alt), (moon.az, moon.alt)))

    #If angular seperation bigger than 1.7 degree there cannot be eclipse.
    log_level("No Eclipse; Angular Separation greater than 1.7 degrees at " + str(datetime) , 3)
    return angular_sep > 1.7


# Step by interval until separation < 1.7 degrees (eclipse possible)
def find_next_start(start_date, interval = 100):
    current_date = start_date
    last_date = current_date
    while(eclipse_impossible(current_date)):
        log_level("No eclipse possible at " + str(current_date), 3)
        last_date = current_date
        current_date = current_date + datetime.timedelta(seconds=100)
    return(last_date)

# Write to disk equirectangular maps every temporal_res seconds until eclipse over.
def write_one_eclipse(start_date, spatial_res = 1, temporal_res = 100, index = 1):
    current_date = start_date
    eclipse_started = False

    while True:
        arr = equirec_percentages(current_date, spatial_res)
        if(arr):
            log_level("Eclipse Happening at " + str(current_date) , 2)
            write_img(arr, index)
            index = index + 1
            current_date = current_date + datetime.timedelta(seconds=temporal_res)
            eclipse_started = True

            if(eclipse_started == False):
                log_level("Eclipse begins at " + str(current_date) , 1)
        else:
            current_date = current_date + datetime.timedelta(seconds=temporal_res)
            if(eclipse_started):
                log_level("Eclipse ends at " + str(current_date) , 1)
                return (current_date, index)
            if(eclipse_impossible(current_date)):
                log_level("Lat/Lon calculation finds no eclipse (near miss)" + str(current_date) , 1)
                return(current_date, index)

            log_level("Eclipse not yet started at " + str(current_date) , 2)

# Write to disk every eclipse in given interval.
def write_all_in_range(start, end, spatial_res = 1, temporal_res = 100, search_interval = 100):
    current_date= start
    index = 1
    while(current_date<end):
        log_level("Looking eclipse alignment potential on or after " + str(current_date), 1)
        current_date = find_next_start(current_date, interval = search_interval)
        if(current_date > end):
            log_level("End date reached " + str(current_date) , 1)
            break
        log_level("Potential Eclipse at " + str(current_date) + "\nSwitching to lat/lon calculation" , 1)
        current_date, index = write_one_eclipse(current_date, spatial_res, temporal_res, index)


parser = argparse.ArgumentParser(description='Generate maps of eclipse brightness across the earth',
                                 prog='EclipseMap')
task = parser.add_mutually_exclusive_group()
parser.add_argument("start", help="Start Date (y-m-d-H-M-S)")
task.add_argument("-d", "--duration", type=int, help="Generate maps every (TIME-RESOLUTION) from (start) until (start)+duration (seconds)")
task.add_argument("-s", "--single", help="Calculate single map for (start) only",action="store_true")
task.add_argument("-e", "--end", help="Generate maps from (start) until (end) (y-m-d-H-M-S)")

parser.add_argument("-r","--resolution", type=int, help="Specify map resolution in pixels per lat/lon", default = 1)
parser.add_argument("-t","--time-resolution", type=int, help="Generate map every (t) seconds", default = 100)
parser.add_argument("-p","--step", type=int, help="Step size in seconds during coarse eclipse search", default = 100)
parser.add_argument("-f","--prefix", help="Filename prefix", default = "")


output = parser.add_mutually_exclusive_group()
output.add_argument("-v", "--verbosity", action="count", default=1, help="Verbose output. Useful for long time periods.")
output.add_argument("-q", "--quiet", action="store_true" , help="Supress all output")
args = parser.parse_args()


start_date = datetime.datetime.strptime(args.start, '%Y-%m-%d-%H-%M-%S')
if(args.end):
    end_date = datetime.datetime.strptime(args.end, '%Y-%m-%d-%H-%M-%S')
if(args.duration):
    end_date = datetime.datetime.strptime(args.start, '%Y-%m-%d-%H-%M-%S') + datetime.timedelta(seconds=args.duration)

if(args.single):
    write_img(equirec_percentages(start_date, ))
else:
    write_all_in_range(start_date, end_date, args.resolution, args.time_resolution, args.step)
