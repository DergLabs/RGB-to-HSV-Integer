# RGB-to-HSV-Integer
Integer-based method for converting RGB image data to HSV and back using only integer arithmetic


Two python files are provided in this repo: int_RGB_to_HSV_Slow and int_RGB_to_HSV_Fast. The slow version of this program is meant for debugging and use with small images. It was built to debug the pure hardware implementation of this RGB to HSV converter, which can be found in my PLU Image processor repo. The fast version of this program is intended to work on large images, and it is more for fun but still uses the same integer-based conversion method. 

These programs were written based on the conversion methods outlined in the Journal of Computers & Electrical Engineering Volume 46, in an article titled "Integer-based accurate conversion between RGB and HSV color spaces". All credit for this conversion method goes to the authors, Vladimir Chernov, Jarmo Alander, Vladimir Bochko

The research paper can be found here: https://www.sciencedirect.com/science/article/abs/pii/S0045790615002827

