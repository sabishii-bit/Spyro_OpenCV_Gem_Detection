import cv2 as cv
import numpy as np
import os
import sys
import win32gui, win32ui, win32con
import numpy as np
import cv2 as cv
from time import time
from win32_screencapture import WindowCapture
from cv_vision import Vision


def main():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    np.set_printoptions(threshold=sys.maxsize)  # For when printed results are too large for the terminal to contain

    detect_img_stream()

    return


# Detect image within video stream
def detect_img_stream():
    wincap = WindowCapture('ePSXe - Enhanced PSX emulator')
    fps_counter = time()
    vision_gem = Vision(None)
    # Load the trained model
    cascade_gem = cv.CascadeClassifier('assets/cascade_training/cascade.xml')

    while True:
        # Grabs updated image of the game
        screenshot = wincap.get_screenshot()

        # Do object detection
        rectangles = cascade_gem.detectMultiScale(screenshot)

        # Draw detection results onto the original image
        detection_image = vision_gem.draw_rectangles(screenshot, rectangles)

        # Display the image
        cv.imshow('Computer Vision', detection_image)

        # Displays FPS output
        print('{} FPS'.format(int(1 / (time() - fps_counter))))
        fps_counter = time()

        # Pressing 'q' closes the output window when it is in focus.
        # Pressing 'd' saves a screenshot of the output window to positive folder.
        # Pressing 'f' saves a screenshot of the output window to negative folder.
        # Wait 1ms every loop to process key input
        key = cv.waitKey(1)
        if key == ord('q'):
            cv.destroyAllWindows()
            print('Exiting...')
            break
        elif key == ord('d'):
            cv.imwrite('assets/positive/{}.jpg'.format(fps_counter), screenshot)
            print('Screenshot saved to positive folder.')
        elif key == ord('f'):
            cv.imwrite('assets/negative/{}.jpg'.format(fps_counter), screenshot)
            print('Screenshot saved to negative folder.')
    return

if __name__ == '__main__':
    main()
