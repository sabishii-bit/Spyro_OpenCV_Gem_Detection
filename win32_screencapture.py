import win32gui, win32ui, win32con
import numpy as np
import cv2 as cv
from time import time


# Window capture class used for returning stream of screenshots at high framerate using Windows API
# Designed for compatibility with OpenCV
class WindowCapture:
    # Class Properties
    w = 0
    h = 0
    hwnd = None
    cropped_x = 0
    cropped_y = 0
    offset_x = 0
    offset_y = 0

    # Class Constructor
    def __init__(self, window_name=None):
        # Window capture using Windows API
        # Default the window_name parameter to None if nothing is passed
        if window_name is None:
            self.hwnd = win32gui.GetDesktopWindow()
        else:
            self.hwnd = win32gui.FindWindow(None, window_name)
            if not self.hwnd:
                raise Exception('Window not found: {}'.format(window_name))

        # Define width and height of the window
        window_rect = win32gui.GetWindowRect(self.hwnd)
        self.w = window_rect[2] - window_rect[0]
        self.h = window_rect[3] - window_rect[1]

        # Account for window border and titlebar to cut them off
        border_pixels = 8
        titlebar_pixels = 30
        self.w = self.w - (border_pixels * 2)
        self.h = self.h - titlebar_pixels - border_pixels
        self.cropped_x = border_pixels
        self.cropped_y = titlebar_pixels

        # Set the cropped coordinates offset so we can translate screenshot images into actual screen positions
        self.offset_x = window_rect[0] + self.cropped_x
        self.offset_y = window_rect[1] + self.cropped_y

    def get_screenshot(self):

        # get the window image data
        wDC = win32gui.GetWindowDC(self.hwnd)
        dcObj = win32ui.CreateDCFromHandle(wDC)
        cDC = dcObj.CreateCompatibleDC()
        dataBitMap = win32ui.CreateBitmap()
        dataBitMap.CreateCompatibleBitmap(dcObj, self.w, self.h)
        cDC.SelectObject(dataBitMap)
        cDC.BitBlt((0, 0), (self.w, self.h), dcObj, (self.cropped_x, self.cropped_y), win32con.SRCCOPY)

        # convert the raw data into a format opencv can read
        # dataBitMap.SaveBitmapFile(cDC, 'debug.bmp')
        signedIntsArray = dataBitMap.GetBitmapBits(True)
        img = np.fromstring(signedIntsArray, dtype='uint8')
        img.shape = (self.h, self.w, 4)

        # free resources
        dcObj.DeleteDC()
        cDC.DeleteDC()
        win32gui.ReleaseDC(self.hwnd, wDC)
        win32gui.DeleteObject(dataBitMap.GetHandle())

        # drop the alpha channel, or cv.matchTemplate() will throw an error like:
        #   error: (-215:Assertion failed) (depth == CV_8U || depth == CV_32F) && type == _templ.type()
        #   && _img.dims() <= 2 in function 'cv::matchTemplate'
        img = img[..., :3]

        # make image C_CONTIGUOUS to avoid errors that look like:
        #   File ... in draw_rectangles
        #   TypeError: an integer is required (got type tuple)
        # see the discussion here:
        # https://github.com/opencv/opencv/issues/14866#issuecomment-580207109
        img = np.ascontiguousarray(img)

        return img

    # Prints list of window names available to use for capture
    @staticmethod
    def list_window_names():
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                print(hex(hwnd), win32gui.GetWindowText(hwnd))

        win32gui.EnumWindows(winEnumHandler, None)

    # Translate a pixel position on a screenshot image to a pixel position on the screen
    # WARNING: If you move the window being captured after execution, this will return incorrect coordinates.
    # This is because the window position is only calculated in the __init__ constructor
    def get_screen_position(self, pos):
        return pos[0] + self.offset_x, pos[1] + self.offset_y

    # Acquires a video stream using the get_screenshot function
    # Has args for an exit key to the window that opens and a flag if the user wants to have the FPS printed to terminal
    def get_video_stream(self, EXIT_KEY='q', print_fps=False):
        fps_counter = time()  # Counter for framerate of window capture
        # Infinite loop to continuously each frame from the window
        while True:
            screenshot = self.get_screenshot()
            cv.imshow('Computer Vision', screenshot)

            # Shows the FPS
            if print_fps:
                print('{} FPS'.format(int(1 / (time() - fps_counter))))
                fps_counter = time()

            # Press the designated EXIT_KEY with the output window focused to exit.
            # Wait 1ms every loop to process key presses
            if cv.waitKey(1) == ord(EXIT_KEY):
                cv.destroyAllWindows()
                break

        return
