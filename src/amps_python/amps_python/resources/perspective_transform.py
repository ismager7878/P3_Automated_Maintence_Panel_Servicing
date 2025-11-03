import cv2 as cv
import numpy as np

def perspective_tf(img, src_points, show=False):
    """
    Apply a perspective transform to the given image, the output image will have a size of 680x930 pixels as a standard board.

    Parameters:
    - img: The input image.
    - src_points: Source points for the perspective transform. Should be given as the pixel coordinates for each corner of the board [top-left, top-right, bottom-left, bottom-right].
    - show: Boolean flag to indicate whether to display the transformed image.
    
    Returns:
    - The transformed image.
    """
    dst_points = np.float32([[0,0],[680,0],[0,930],[680,930]])
    M = cv.getPerspectiveTransform(src_points,dst_points)
    dst = cv.warpPerspective(img,M,(680,930))
    if show:
        cv.imshow('Transformed Image', dst)
        cv.waitKey(0)
        cv.destroyAllWindows()
    return dst