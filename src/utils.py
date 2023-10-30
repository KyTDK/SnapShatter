from ppadb.client import Client as AdbClient
import cv2
import time

# Connect to ADB
adb = AdbClient(host="127.0.0.1", port=5037)
# Get ADB devices
devices = adb.devices()
# Check if at least one device is connected
assert devices, "No ADB devices found."
device = devices[0]

# Check if the tap command was executed successfully
output = device.shell("echo success")
assert "success" in output, "Failed to execute adb command."

default_scale = None
attempts = 0
height = 0
width = 0
previous_image = None
previous_click_times = None

show_roi = False


def get_device():
    return device


def get_device_dimensions():
    return height, width


def set_default_scale(scale):
    global default_scale
    default_scale = scale

def tap(x, y):
    device.shell(f"input touchscreen swipe {x} {y} {x} {y} 50")

def swipe(x, y, x1, y1, duration):
    device.shell(f"input touchscreen swipe {x} {y} {x1} {y1} {duration}")


def find_image(
    image_name,
    click=True,
    scale=None,
    click_times=1,
    roi_height_percentage=100,
    roi_top_percentage=0,
    failsafe=True,
):
    global attempts, height, width, previous_image, previous_click_times
    # Capture the screenshot
    image = device.screencap()
    if scale is None:
        scale = float(default_scale) if default_scale is not None else 1.36
    # Save the screenshot as 'screen.png'
    with open("screen.png", "wb") as file:
        file.write(image)

    # Load the screenshot as an image in grayscale
    screenshot = cv2.imread("screen.png", cv2.IMREAD_GRAYSCALE)

    # Calculate the region of interest (ROI) based on the provided percentage values
    height, width = screenshot.shape

    roi_top = int(height * (roi_top_percentage / 100))
    roi_height = int(height * (roi_height_percentage / 100))
    roi_bottom = roi_top + roi_height

    # Crop the screenshot to the defined ROI
    screenshot_roi = screenshot[roi_top:roi_bottom, :]

    # Load the template image to be recognized in grayscale
    template_image = cv2.imread(f"./images/{image_name}", cv2.IMREAD_GRAYSCALE)

    # List of scales to consider (adjust as needed)
    threshold = 0.9

    # Resize the template image
    resized_template = cv2.resize(template_image, None, fx=scale, fy=scale)
    if show_roi:
        # Display the image
        cv2.imshow("Image", screenshot_roi)
        # Wait for a key event and close the window
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    # Perform template matching at the current scale
    result = cv2.matchTemplate(screenshot_roi, resized_template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    # Check if a match was found at the current scale
    if max_val > threshold:
        # Get the coordinates of the top-left corner of the matched region
        x, y = max_loc
        y = y + (roi_top)
        print(f"Found {image_name} at {x}, {y} with {max_val} certainty")
        if failsafe is True:
            attempts = 0
        previous_image = image_name
        previous_click_times = click_times
        # Click on the recognized image
        if click:
            for i in range(click_times):
                tap(x, y)
                if click_times > 1:
                    time.sleep(0.1)
        return x, y
    elif failsafe is True:
        attempts = attempts + 1
        if attempts >= 50:
            device.shell("am force-stop com.snapchat.android")
            device.shell(
                "am start -n com.snapchat.android/com.snapchat.android.LandingPageActivity"
            )
            time.sleep(5)
            attempts = 0
            raise ("System broken, restarting...")
        elif attempts % 10 == 0:
            print(f"Failed to find {image_name}, moving to next step...")
            return False
        else:
            if previous_image is not None and find_image(
                previous_image, failsafe=False, click=False
            ):
                print(
                    f"Stuck on {previous_image}, attempting again, {attempts} attempts"
                )
                find_image(
                    previous_image, failsafe=False, click_times=previous_click_times
                )
            else:
                print(
                    f"{image_name} not found in the screenshot. Certainty of {max_val}, trying again, {attempts} attempts"
                )
            find_image(
                image_name,
                click=click,
                scale=scale,
                click_times=click_times,
                roi_height_percentage=roi_height_percentage,
                roi_top_percentage=roi_top_percentage,
                failsafe=failsafe,
            )
