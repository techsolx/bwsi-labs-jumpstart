"""
Copyright MIT and Harvey Mudd College
MIT License
Summer 2020

Lab 2B - Color Image Cone Parking
"""
RealCar = False
# RealCar = True
# Change the line above to true when we are ready to test on the real car!
# If on the real car hold down the right bumper button to let the car drive

########################################################################################
# Imports
########################################################################################

import sys
import cv2 as cv
import numpy as np
import enum


sys.path.insert(1, "../../library")
import racecar_core
import racecar_utils as rc_utils

########################################################################################
# Global variables
########################################################################################

rc = racecar_core.create_racecar()

########################################################################################
########################################################################################
########################################################################################
#
# Adjust the values in this section to tune how the car drives
#
# The HSV range for the color orange, stored as (hsv_min, hsv_max)
# Hint: You can use the widget in the lab2.ipynb to help tune this value
# In real-world conditions the car might see glare on the tape, washing out the colors
# We might also have a shadow making the color sometimes appear darker than others
# What is the best HSV range to only find the tape we want and avoid distractions?
hsv_lower = (0, 0, 0)
hsv_upper = (179, 255, 255)

# John hacked these values to help you!!!!!
# then I reformatted the whole file to be pep8 compliant
# your values included WAY too much red:
# hsv_lower = (164,155,78)
# hsv_upper = (179,255,255)
# my values are:
hsv_lower = (0, 40, 40)
hsv_upper = (30, 255, 255)
ORANGE = (hsv_lower, hsv_upper)

# Area of the cone contour when we are the correct distance away (must be tuned)
# your values was:
# GOAL_AREA = 27474
# It's silly to spend time on any values past the 100's my value is:
GOAL_AREA = 26000

########################################################################################
########################################################################################
########################################################################################
#
# To fine-tune your car you may need to change values within this section.
#
# >> Constants
# The smallest contour we will recognize as a valid contour
MIN_CONTOUR_AREA = 30
# MIN_CONTOUR_AREA = 30 # Default

# Area of the cone contour when we should switch to reverse while aligning
REVERSE_AREA = GOAL_AREA * 0.4
# REVERSE_AREA = GOAL_AREA * 0.4 # Default

# Area of the cone contour when we should switch to forward while aligning
FORWARD_AREA = GOAL_AREA * 0.2
# FORWARD_AREA = GOAL_AREA * 0.2 # Default

# Speed to use in parking and aligning modes
PARK_SPEED = 0.25
# PARK_SPEED = 0.25 # Default

ALIGN_SPEED = 0.75
# ALIGN_SPEED = 0.75 # Default

# If desired speed/angle is under these thresholds, they are considered "close enough"
SPEED_THRESHOLD = 0.04
# SPEED_THRESHOLD = 0.04 # Default

ANGLE_THRESHOLD = 0.1
# ANGLE_THRESHOLD = 0.1 # Default

"""
These values are ints, somehow these got changed,
park = 0.25 is NOT an integer!!!
This is one of 2 things that made the car not drive.
your values were:
class Mode(enum.IntEnum):
    park = 0.25
    forward = 1
    reverse = 2
"""

# my values are:
class Mode(enum.IntEnum):
    park = 0
    forward = 1
    reverse = 2


# >> Initialize these Variables
# your value was:
# speed = 0.5  # The current speed of the car
# my value is:
speed = 0.0  # The current speed of the car
angle = 0.0  # The current angle of the car's wheels
contour_center = None  # The (pixel row, pixel column) of contour
contour_area = 0  # The area of contour
cur_mode = Mode.forward


########################################################################################
# Functions
########################################################################################


def update_contour():
    """
    Finds contours in the current color image and uses them to update contour_center
    and contour_area
    """
    global contour_center
    global contour_area

    image = rc.camera.get_color_image()

    if image is None:
        contour_center = None
        contour_area = 0
    else:
        # Find all of the orange contours
        contours = rc_utils.find_contours(image, ORANGE[0], ORANGE[1])

        # Select the largest contour
        contour = rc_utils.get_largest_contour(contours, MIN_CONTOUR_AREA)

    if contour is not None:
        # Calculate contour information
        contour_center = rc_utils.get_contour_center(contour)
        contour_area = rc_utils.get_contour_area(contour)

        # Draw contour onto the image
        rc_utils.draw_contour(image, contour)
        rc_utils.draw_circle(image, contour_center)

    else:
        contour_center = None
        contour_area = 0

    # Display the image to the screen
    rc.display.show_color_image(image)


def start():
    """
    This function is run once every time the start button is pressed
    """
    global speed
    global angle

    # Initialize variables
    speed = 0
    angle = 0

    # Set initial driving speed and angle
    rc.drive.set_speed_angle(speed, angle)

    # Set update_slow to refresh every half second
    rc.set_update_slow_time(0.5)

    # Begin in "forward" mode
    cur_mode = Mode.forward

    # Print start message
    print(">> Lab 2 - Color Image Cone Driving")


def update():
    """
    After start() is run, this function is run every frame until the back button
    is pressed
    """
    global speed
    global angle
    global cur_mode

    # Search for contours in the current color image
    update_contour()

    # Goal: Park the car 12 inches away from the closest orange cone

    # If no cone is found, stop
    if contour_center is None or contour_area == 0:
        # your value was, set based on our testing attempts:
        # speed = 1  # set the speed for the car to stop
        # I reset that to 0
        speed = 0  # set the speed for the car to stop
        angle = 0  # set the angle for the car to stop pointing straight ahead

    else:  # if a cone is found, run the next section of code
        # Use proportional control to set wheel angle based on contour x position
        angle = rc_utils.remap_range(contour_center[1], 0, rc.camera.get_width(), -1, 1)

    # PARK MODE: Move forward or backward until contour_area is GOAL_AREA
    if cur_mode == Mode.park:
        speed = rc_utils.remap_range(contour_area, GOAL_AREA / 2, GOAL_AREA, 1.0, 0.0)
        speed = rc_utils.clamp(speed, -PARK_SPEED, PARK_SPEED)

        """
        John changed this, this and Mode were the real problem the others
        were just making it worse.
        Also this is how you do a multi line comment in python, it uses 3 "
        This is the one that fixed it, your value was:
        if SPEED_THRESHOLD < speed < SPEED_THRESHOLD:
        the first compair value should be, -SPEED_THRESHOLD, see it!!!!
        this is a very common way to find a between value in python,
        you would read the line like this:
        if speed is between minus SPEED_THRESHOLD and SPEED_THRESHOLD
        """

        # If speed is close to 0, round to 0 to "park" the car
        if -SPEED_THRESHOLD < speed < SPEED_THRESHOLD:
            speed = 0

        # If the angle is no longer correct, choose mode based on area
        if abs(angle) > ANGLE_THRESHOLD:
            cur_mode = Mode.forward if contour_area < FORWARD_AREA else Mode.reverse

    # FORWARD MODE: Move forward until area is greater than REVERSE_AREA
    elif cur_mode == Mode.forward:
        speed = rc_utils.remap_range(
            contour_area, MIN_CONTOUR_AREA, REVERSE_AREA, 1.0, 0.0
        )
        speed = rc_utils.clamp(speed, 0, ALIGN_SPEED)

        # Once we pass REVERSE_AREA, switch to reverse mode
        if contour_area > REVERSE_AREA:
            cur_mode = Mode.reverse

        # If we are close to the correct angle, switch to park mode
        if abs(angle) < ANGLE_THRESHOLD:
            cur_mode = Mode.park

    # REVERSE MODE: move backward until area is less than FORWARD_AREA
    else:
        speed = rc_utils.remap_range(
            contour_area, REVERSE_AREA, FORWARD_AREA, -1.0, 0.0
        )
        speed = rc_utils.clamp(speed, -ALIGN_SPEED, 0)

        # Once we pass FORWARD_AREA, switch to forward mode
        if contour_area < FORWARD_AREA:
            cur_mode = Mode.forward

        # If we are close to the correct angle, switch to park mode
        if abs(angle) < ANGLE_THRESHOLD:
            cur_mode = Mode.park

    # Reverse the angle if we are driving backward
    if speed < 0:
        angle *= -1

    # If the right button is not held down (as a kill switch)
    if rc.controller.is_down(rc.controller.Button.RB) == False and RealCar == True:
        speed = 0

    rc.drive.set_speed_angle(speed, angle)

    # Print the current speed and angle when the A button (1 key) is held down
    if rc.controller.is_down(rc.controller.Button.A):
        print("Speed:", speed, "Angle:", angle)

    # Print the center and area of the largest contour when B button (2 key) is held down
    if rc.controller.is_down(rc.controller.Button.B):
        if contour_center is None:
            print("No contour found")
    else:
        print("Center:", contour_center, "Area:", contour_area)


def update_slow():
    """
    After start() is run, this function is run at a constant rate that is slower
    than update().  By default, update_slow() is run once per second
    """
    # Print a line of ascii text denoting the contour area and x position
    if rc.camera.get_color_image() is None:
        # If no image is found, print all X's and don't display an image
        print("X" * 10 + " (No image) " + "X" * 10)
    else:
        # If an image is found but no contour is found, print all dashes
        if contour_center is None:
            print("-" * 32 + " : area = " + str(contour_area))

        # Otherwise, print a line of dashes with a | indicating the contour x-position
        else:
            s = ["-"] * 32
            s[int(contour_center[1] / 20)] = "|"
            print("".join(s) + " : area = " + str(contour_area))


########################################################################################
# DO NOT MODIFY: Register start and update and begin execution
########################################################################################

if __name__ == "__main__":
    rc.set_start_update(start, update, update_slow)
    rc.go()
