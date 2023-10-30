import os
import time
import cv2
import traceback
from src.utils import (
    find_image,
    get_device,
    get_device_dimensions,
    set_default_scale,
    tap,
    swipe,
)

device = get_device()

import cv2
import json


def calibrate_scale(image_name):
    input(f"Open snapchat page that contains {image_name}, then press enter")

    # Capture the screenshot
    image = device.screencap()

    # Save the screenshot as 'screen.png'
    with open("screen.png", "wb") as file:
        file.write(image)

    # Load the screenshot as an image in grayscale
    screenshot = cv2.imread("screen.png", cv2.IMREAD_GRAYSCALE)

    # Load the template image to be recognized in grayscale
    template_image = cv2.imread(f"./images/{image_name}", cv2.IMREAD_GRAYSCALE)

    # Initial scale and peak accuracy
    scale = 0.1
    peak_accuracy = 0

    while True:
        # Resize the template image
        template_resized = cv2.resize(template_image, None, fx=scale, fy=scale)

        # Check if the template image exceeds the size of the screenshot
        if (
            template_resized.shape[0] > screenshot.shape[0]
            or template_resized.shape[1] > screenshot.shape[1]
        ):
            break  # Stop if the template image is too large

        # Perform template matching at the current scale
        result = cv2.matchTemplate(screenshot, template_resized, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Check if the current accuracy is greater than the peak accuracy
        if max_val > peak_accuracy:
            print(f"New best accuracy: {max_val} at scale {scale}")
            peak_accuracy = max_val
            best_scale = scale

        # Increase the scale for the next iteration
        scale += 0.01

    return best_scale, peak_accuracy


def send_snaps():
    try:
        while True:
            while find_image("sending.png", click=False, failsafe=False):
                print("Still sending, waiting...")
                time.sleep(5)
            while not find_image(
                "camera.png",
                roi_height_percentage=30,
                roi_top_percentage=70,
                failsafe=False,
            ) and find_image("send.png", failsafe=False, click=False):
                print("Still processing, waiting")
            if not find_image(
                "multi_snap_selected.png", click=False, failsafe=False
            ) and find_image("snap.png", click=False, failsafe=False):
                print("Multi-snap not enabled, enabling now...")
                find_image("more.png")
                time.sleep(1)
                result = find_image("director_mode.png", click=False)
                if result:
                    x, y = result
                    swipe(x, y, x, y - 500, 500)
                    swipe(x, y, x, y - 500, 500)
                    swipe(x, y, x, y - 500, 500)
                else:
                    # multi-snap full is frequency problem, check
                    if find_image("multi_snap_full.png", click=False, failsafe=False):
                        find_image("ok.png")
                if find_image("multi_snap.png"):
                    print("Multi-snap enabled!")
            if not find_image(
                "edit_and_send.png",
                failsafe=False,
                roi_height_percentage=30,
                roi_top_percentage=70,
            ):
                find_image("snap.png", click_times=7)
                time.sleep(1)
                find_image(
                    "edit_and_send.png", roi_height_percentage=30, roi_top_percentage=70
                )
            time.sleep(1)
            find_image("next.png", roi_height_percentage=30, roi_top_percentage=70)
            time.sleep(1)
            find_image("shortcut.png", roi_height_percentage=30, roi_top_percentage=0)
            time.sleep(1)
            find_image(
                "select_all.png",
                roi_height_percentage=30,
                roi_top_percentage=0,
            )
            time.sleep(1)
            find_image("send.png")
            time.sleep(1)
    except Exception as e:
        print(f"Function a: Caught an exception - {e}")
        traceback.print_exc()
        send_snaps()


def do_streaks():
    scrolls_without_streaks = 0
    height_percentage = 10
    try:
        while True:
            result = find_image("streak.png", failsafe=False, click=False)
            if result:
                x, y = result
                height, width = get_device_dimensions()
                top_percentage = (y / height) * 100 - 5
                if find_image(
                    "delivered.png",
                    failsafe=False,
                    click=False,
                    roi_height_percentage=height_percentage,
                    roi_top_percentage=top_percentage,
                ):
                    print("Already delivered, moving on...")
                    swipe(x, y, x, y - 200, 100)
                    continue
                if find_image("new_snap.png", failsafe=False):
                    tap(x / 2, y / s)
                result = find_image(
                    "camera_person.png",
                    failsafe=False,
                    roi_height_percentage=height_percentage,
                    roi_top_percentage=top_percentage,
                ) or find_image(
                    "snap_reply.png",
                    failsafe=False,
                    roi_height_percentage=height_percentage,
                    roi_top_percentage=top_percentage,
                )
                if result:
                    time.sleep(1)
                    find_image("snap_single.png")
                    time.sleep(1)
                    find_image("send_direct.png")
                else:
                    result = find_image(
                        "message_person.png",
                        failsafe=False,
                        roi_height_percentage=height_percentage,
                        roi_top_percentage=top_percentage,
                    )
                    if result:
                        time.sleep(1)
                        find_image("camera_dms.png")
                        time.sleep(1)
                        find_image("snap_single.png")
                        time.sleep(1)
                        find_image("send_direct.png")
                        time.sleep(1)
                        find_image("exit_dms.png")
                scrolls_without_adds = 0
            else:
                result = (
                    find_image("camera_person.png", failsafe=False, click=False)
                    or find_image("message_person.png", failsafe=False, click=False)
                    or find_image("first_snap.png", failsafe=False, click=False)
                )
                if result:
                    x, y = result
                    swipe(x, y, x, y - 200, 100)
                    if not find_image("streak.png", failsafe=False):
                        scrolls_without_streaks += 1
                        if scrolls_without_streaks >= 10:
                            print("No more streaks available, exiting...")
                            break
    except Exception as e:
        print(f"Caught an exception - {e}")
        traceback.print_exc()


def add_friends():
    find_image("friends.png", failsafe=False)
    scrolls_without_adds = 0
    try:
        while True:
            result = find_image("add.png", failsafe=False) or find_image(
                "accept.png", failsafe=False
            )
            if not result:
                result = find_image("message.png", failsafe=False, click=False)
                if result:
                    x, y = result
                    swipe(x, y, x, y - 200, 100)
                    if not find_image("add.png", failsafe=False):
                        scrolls_without_adds += 1
                        if scrolls_without_adds >= 10:
                            print("No more adds available, exiting...")
                            break
            else:
                scrolls_without_adds = 0
    except Exception as e:
        print(f"Caught an exception - {e}")
        traceback.print_exc()
        add_friends()


print("1. Send snaps")
print("2. Add friends")
print("3. Do streaks")
print("4. Recalibrate scale")
choice = input("Enter your choice: ")
scale = None
# Check if calibrate.txt exists
if os.path.exists("calibrate.txt"):
    with open("calibrate.txt", "r") as calibrate_file:
        scale = calibrate_file.read().strip()

# If calibrate.txt doesn't exist or is empty, call calibrate() and write into calibrate.txt
if not scale:
    best_scale, peak_accuracy = calibrate_scale("snap.png")
    with open("calibrate.txt", "w") as calibrate_file:
        calibrate_file.write(str(best_scale))

if scale:
    set_default_scale(scale)
if choice == "1":
    send_snaps()
elif choice == "2":
    add_friends()
elif choice == "3":
    do_streaks()
elif choice == "4":
    calibrate_scale(input("Enter image name, press enter to continue: "))
    print("Calibration complete")
