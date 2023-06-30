import statistics
from PIL import Image
import cv2
import numpy as np
import tkinter as tk
import threading
import math
import csv


def backCalcINT(H, S, V):
    E = 65535
    bitShift = 16
    RGB = [0, 0, 0]
    I = 0

    if S == 0 or V == 0:
        RGB = [V, V, V]
        return RGB

    # Step 1 - Back Calculate d and m
    d = int(((S * V) >> bitShift) + 1)
    m = int(V - d)

    # Step 2 - Determine the Selector index based on the value of H
    if H < E:
        I = 0
    elif E <= H < (2 * E):
        I = 1
    elif (2 * E) <= H < (3 * E):
        I = 2
    elif (3 * E) <= H < (4 * E):
        I = 3
    elif (4 * E) <= H < (5 * E):
        I = 4
    elif H >= (5 * E):
        I = 5

    # Step 3 Calculate F, add 1 if F is equal to 0
    F = int(H - (E * I))
    if F == 0:
        F += 1

    # Step 3 If the selector index is 1,3, or 5, undo the inversion of F done in the RGB-HSV conversion
    if I % 2 != 0:
        F = int(E - F)

    # Step 4 Calculate C based on F and D
    c = int(((F * d) >> bitShift) + m)

    # Step 5 Output the RGB values according to the selector index
    if I == 0:
        RGB = [V, c, m]
    elif I == 1:
        RGB = [c, V, m]
    elif I == 2:
        RGB = [m, V, c]
    elif I == 3:
        RGB = [m, c, V]
    elif I == 4:
        RGB = [c, m, V]
    elif I == 5:
        RGB = [V, m, c]

    return RGB


def calcHSVINT(R, G, B):
    E = 65535
    bitShift = 16
    temp_list = [R, G, B]

    # Step 1 calculate the min, max and middle values for RGB
    M = max(R, G, B)
    m = min(R, G, B)
    c = statistics.median(temp_list)

    # Step 2 Set V equal to M
    V = M

    # Step 3 calculate the difference between M and m, if its 0, set S to 0, and H to -1 (It is undefined in this case)
    d = int(M - m)
    if d == 0 or V == 0:
        S = 0
        H = -1
        return H, S, V

    # Step 4 find the selector index based on which color is the Min/Max, special case is needed if two are the same
    if R != G != B:
        if M == R and m == B:
            I = 0
        elif M == G and m == B:
            I = 1
        elif M == G and m == R:
            I = 2
        elif M == B and m == R:
            I = 3
        elif M == B and m == G:
            I = 4
        elif M == R and m == G:
            I = 5
    else:
        if M == R and m == B:
            I = 0
        elif M == G and m == B:
            I = 1
        elif M == G and m == R:
            I = 3
        elif M == B and m == R:
            I = 4
        elif M == B and m == G:
            I = 2
        elif M == R and m == G:
            I = 5

    # Step 5 calculate S using d and V
    S = int(((d << bitShift) - 1) / V)

    # Step 6 calculate F using c, m and d, check if I is 1,3,5 and set F to its inverse
    F = int((((c - m) << 16) / d) + 1)

    if I % 2 != 0:
        F = E - F

    # Step 7 calculate H using E, I and F
    H = (E * I) + F

    return H, S, V


def backCalcFP(H, S, V):
    h_floored = int(math.floor(H))
    h_sub_i = int(h_floored / 60) % 6
    var_f = (H / 60.0) - (h_floored // 60)
    var_p = V * (1.0 - S)
    var_q = V * (1.0 - var_f * S)
    var_t = V * (1.0 - (1.0 - var_f) * S)

    if h_sub_i == 0:
        rgb_r = V
        rgb_g = var_t
        rgb_b = var_p
    elif h_sub_i == 1:
        rgb_r = var_q
        rgb_g = V
        rgb_b = var_p
    elif h_sub_i == 2:
        rgb_r = var_p
        rgb_g = V
        rgb_b = var_t
    elif h_sub_i == 3:
        rgb_r = var_p
        rgb_g = var_q
        rgb_b = V
    elif h_sub_i == 4:
        rgb_r = var_t
        rgb_g = var_p
        rgb_b = V
    elif h_sub_i == 5:
        rgb_r = V
        rgb_g = var_p
        rgb_b = var_q

    RGB = [rgb_r, rgb_g, rgb_b]
    return RGB


def calcHSVFP(R, G, B):
    M = max(R, G, B)
    m = min(R, G, B)

    if M == m:
        H = 0.0
    elif M == R:
        H = (60.0 * ((G - B) / (M - m)) + 360) % 360.0
    elif M == G:
        H = 60.0 * ((B - R) / (M - m)) + 120
    elif M == B:
        H = 60.0 * ((R - G) / (M - m)) + 240.0

    if M == 0:
        S = 0
    else:
        S = 1.0 - (m / M)

    V = M

    return H, S, V


def process_image(input_filename, output_filename):
    # Open the input image
    image = Image.open(input_filename)
    pixels = image.load()
    # Process each pixel
    for y in range(image.height):
        for x in range(image.width):
            # Get the RGB values
            R, G, B = pixels[x, y]

            # Convert to HSV
            H, S, V = calcHSVINT(R, G, B)

            H = H + 6032  # Example adjustment
            S = S + 5875  # Example adjustment
            # Convert back to RGB
            R_new, G_new, B_new = backCalcINT(H, S, V)

            # Write the new RGB values back to the pixel
            pixels[x, y] = (int(R_new), int(G_new), int(B_new))

    # Save the output image
    image.save(output_filename)


def process_image_live(input_filename, h_adjust, s_adjust, v_adjust, r_adjust, g_adjust, b_adjust, processFormat):
    # Open the input image
    image = Image.open(input_filename)
    pixels = image.load()

    # Store the original RGB values
    original_pixels = [[pixels[x, y] for y in range(image.height)] for x in range(image.width)]
    while True:
        # Process each pixel
        for y in range(image.height):
            for x in range(image.width):
                # Get the original RGB values
                R, G, B = original_pixels[x][y]

                R += r_adjust.get()
                G += g_adjust.get()
                B += b_adjust.get()

                # Convert to HSV
                if processFormat == "INT":
                    H, S, V = calcHSVINT(R, G, B)
                elif processFormat == "FP":
                    H, S, V = calcHSVFP(R, G, B)

                # Adjust H, S, and V values
                if processFormat == "INT":

                    H += h_adjust.get()
                    S += s_adjust.get()
                    V += v_adjust.get()


                elif processFormat == "FP":
                    H += h_adjust.get()
                    S += (s_adjust.get() / 100)
                    V += v_adjust.get()

                # Convert back to RGB
                if processFormat == "INT":
                    R_new, G_new, B_new = backCalcINT(H, S, V)
                elif processFormat == "FP":
                    R_new, G_new, B_new = backCalcFP(H, S, V)

                cv2.setWindowProperty('Image', cv2.WND_PROP_AUTOSIZE, cv2.WINDOW_NORMAL)
                # Write the new RGB values back to the pixel
                pixels[x, y] = (int(R_new), int(G_new), int(B_new))

            # Update the image display after each row of pixels is processed
            cv2.imshow('Image', cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR))
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Break the infinite loop if 'q' was pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()


def tkinterWindow(imageFilename):
    window = tk.Tk()
    processFormat = "INT"
    if processFormat == "INT":
        h_adjust = tk.Scale(window, from_=-195_000, to=195_000, length=500, label='Hue Adjust', orient='horizontal')
        s_adjust = tk.Scale(window, from_=-65535, to=65535, length=500, label='Saturation Adjust', orient='horizontal')
        v_adjust = tk.Scale(window, from_=-255, to=255, length=500, label='Value Adjust', orient='horizontal')
    elif processFormat == "FP":
        h_adjust = tk.Scale(window, from_=-180, to=180, length=500, label='Hue Adjust', orient='horizontal')
        s_adjust = tk.Scale(window, from_=-100, to=100, length=500, label='Saturation Adjust', orient='horizontal')
        v_adjust = tk.Scale(window, from_=-100, to=100, length=500, label='Value Adjust', orient='horizontal')

    r_adjust = tk.Scale(window, from_=-255, to=255, length=500, label='Red CH Adjust', orient='horizontal')
    g_adjust = tk.Scale(window, from_=-255, to=255, length=500, label='Green CH Adjust', orient='horizontal')
    b_adjust = tk.Scale(window, from_=-255, to=255, length=500, label='Blue CH Adjust', orient='horizontal')

    h_adjust.pack()
    s_adjust.pack()
    v_adjust.pack()
    r_adjust.pack()
    g_adjust.pack()
    b_adjust.pack()

    threading.Thread(target=process_image_live, args=(imageFilename, h_adjust, s_adjust, v_adjust, r_adjust, g_adjust, b_adjust, processFormat)).start()

    window.mainloop()


# Used for finding edge case bugs
def singlePixelTest():
    while True:
        R = int(input("Enter a R Value to test (or 999 to exit): "))
        if R == 999:
            exit()
        G = int(input("Enter a G Value to test: "))
        B = int(input("Enter a B Value to test: "))
        E = 65537

        print("Hex Values for RGB: {} {} {}\n".format(hex(R), hex(G), hex(B)))

        print("Calculating HSV values from RGB")
        H, S, V = calcHSVINT(R, G, B)
        print("H: {} | S: {} | V: {}\n".format(H, S, V))

        # If the HSV conversion is correct, then it should perfectly back calculate to the original RGB values
        print("---------------------------------------------------------------")
        print("Back Calculating RGB values from HSV")
        R, G, B = backCalcINT(H, S, V)
        print("RGB Values: R: {} | G: {} | B:{}\n".format(R, G, B))


def color_tester():
    match = 0
    fuzzy = 0
    mismatch = 0
    mismatched_colors = []
    print("Testing Integer Converter...\n")
    for R in range(256):
        for G in range(256):
            for B in range(256):
                H, S, V = calcHSVINT(R, G, B)
                R_back, G_back, B_back = backCalcINT(H, S, V)

                if R == R_back and G == G_back and B == B_back:
                    match += 1
                elif (abs(R - R_back) / 255) <= 0.02 and (abs(G - G_back) / 255) <= 0.02 and (
                        abs(B - B_back) / 255) <= 0.02:
                    fuzzy += 1
                else:
                    mismatch += 1
                    mismatched_colors.append(((R, G, B), (R_back, G_back, B_back)))

    print(f"Percentage of colors that perfect: {(match / (256 ** 3)) * 100}% | {match} Colors")
    print(
        f"Percentage of colors that are near perfect (+/- <2%): {(fuzzy / (256 ** 3)) * 100}% | {fuzzy} near perfect Colors")
    print(
        f"Percentage of colors that mismatched (+/- >2%): {(mismatch / (256 ** 3)) * 100}% | {mismatch} mismatched Colors")

    # Open a CSV file in write mode ('w') and write the mismatched colors to it.
    with open('mismatched_colors_ints.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Original RGB', 'Calculated RGB'])  # Write header
        for original, calculated in mismatched_colors:
            writer.writerow([original, calculated])  # Write each row

    '''
    print("----------------------------------------------------------------------------------------")
    print("Testing Floating Point Converter...\n")
    match = 0
    fuzzy = 0
    mismatch = 0
    mismatched_colors = []

    for R in range(256):
        for G in range(256):
            for B in range(256):
                H, S, V = calcHSVFP(R, G, B)
                R_back, G_back, B_back = backCalcFP(H, S, V)

                if R == R_back and G == G_back and B == B_back:
                    match += 1
                elif (abs(R - R_back) / 255) <= 0.05 and (abs(G - G_back) / 255) <= 0.05 and (
                        abs(B - B_back) / 255) <= 0.05:
                    fuzzy += 1
                else:
                    mismatch += 1
                    mismatched_colors.append(((R, G, B), (R_back, G_back, B_back)))

    print(f"Percentage of colors that matched: {(match / (256 ** 3)) * 100}% | {match} Colors")
    print(f"Percentage of colors that are fuzzy (+/- 2%-5%): {(fuzzy / (256 ** 3)) * 100}% | {fuzzy} fuzzy Colors")
    print(f"Percentage of colors that mismatched (+/- >5%): {(mismatch / (256 ** 3)) * 100}% | {mismatch} mismatched Colors")

    # Open a CSV file in write mode ('w') and write the mismatched colors to it.
    with open('mismatched_colors_FP.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Original RGB', 'Calculated RGB'])  # Write header
        for original, calculated in mismatched_colors:
            writer.writerow([original, calculated])  # Write each row
    '''


if __name__ == '__main__':
    option = "lia"
    imageFilename = "window.jpg"
    if option == "pi":
        process_image('contrastIN.png',
                      'contrastOUT.png')  # Used for single shot image adjustment, not especially usefull
    elif option == "spt":
        singlePixelTest()  # Used for edge case debugging
    elif option == "lia":
        tkinterWindow(imageFilename)  # Live image adjustments!
    elif option == "ct":
        color_tester()
