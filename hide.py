#!/usr/bin/env python3
#encoding: UTF-8
from lib2to3.pgen2.token import AWAIT
from PIL import Image
from random import choice
from optparse import OptionParser
import pyaes, pbkdf2, secrets, os
from pymongo import MongoClient
import numpy as np
import os
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

client = MongoClient('mongodb://localhost:27017')
mydatabase = client['ImgStegno']
pikKey = mydatabase['picKey']
location = mydatabase['location']
nonce = b''
# password = "s3cr3t*c0d3"
# passwordSalt = os.urandom(16)
# AESkey = pbkdf2.PBKDF2(password, passwordSalt).read(32)
# k = secrets.randbits(256)
key = get_random_bytes(16)
cipher = AES.new(key, AES.MODE_CTR)

def pixelNumberToCoordinate(n, img):
    """
    Converts pixel number to coordinates.
    Ex: Image size is w=10, h=20
    The 23th pixel has coordinates of (3, 2).
    """
    return (n%img.size[0], n//img.size[0])

def coordinateToPixelNumber(x, y, img):
    """
    Converts coordinates to pixel number.
    Ex: Image size is w=10, h=20
    pixel (3, 2) is the 23th pixel.
    """
    return int(y*img.size[0]+x)

def setLSB(v, state):
    if state == "0":
        return v & 0b11111110
    elif state == "1":
        return v | 0b00000001
    else:
        print(f"invalide state: {state}")
        return v

def write(data, pixel, nextP, img):
    """
    Writes a block of data and pointer to the next pixel in binary format at a given pixel.

    @param data: Binary representation of a block of data.
    @type data: String

    @param pixel: Pixel number where the block starts.
    @type pixel: Int

    @param nextP: Pixel number to the next block of data.
    @type nextP: Int

    @param img: Image Object.
    @type img: Image
    """
    pix = img.load()
    x, y = pixelNumberToCoordinate(nextP, img)
    l = len(data)
    # binari representation of next pixel x
    col = bin(x)[2:].zfill(l)
    # binari representation of next pixel y
    lin = bin(y)[2:].zfill(l)

    for i in range(pixel, pixel+l):
        p = pix[pixelNumberToCoordinate(i, img)]
        if len(p) == 4:
            # With alpha channel
            pix[pixelNumberToCoordinate(i, img)] = (
            setLSB(p[0], data[i-pixel]),
            setLSB(p[1], col[i-pixel]),
            setLSB(p[2], lin[i-pixel]),
            p[3])
        else:
            # no alpha channel
            pix[pixelNumberToCoordinate(i, img)] = (
            setLSB(p[0], data[i-pixel]),
            setLSB(p[1], col[i-pixel]),
            setLSB(p[2], lin[i-pixel]))

def toBin(string):
    return ''.join(format(x, 'b').zfill(8) for x in string)

def chunkstring(string, length):
    return [string[0+i:length+i].ljust(length, "0") for i in range(0, len(string), length)]

def encrypt(data):
    global nonce
    d = data.encode()

    ciphertext= cipher.encrypt(d)
    nonce = cipher.nonce
    print(type(ciphertext))

    return ciphertext
    # aes = pyaes.AESModeOfOperationCTR(AESkey, pyaes.Counter(k))
    # ciphertext = aes.encrypt(data)
    # return ciphertext

def hide(data, imgName, startingPixel=(0,0)):
    """
    Hides the string data in the image imgName and creates a new image containing the data outName.
    startingPixel is optional and will be choosed randomly if not specified.

    @param data: Data to hide.
    @type data: String

    @param imgName: Name of the original image.
    @type imgName: String

    @param outName: Name of the resulting image.
    @type outName: String

    @param startingPixel: Optional starting pixel coordinates.
    @type startingPixel: Tuple

    @returns: The starting pixel used.
    @rtype: Tuple
    """
    img = Image.open(imgName)
    BLOCKLEN = len(bin(max(img.size))[2:])
    # The number of pixels in the image
    total = img.size[0] * img.size[1]
    # list of available block positions
    AVAILABLE = [x for x in range(1, total-1, BLOCKLEN)]
    # Check if the last position is big enough
    if AVAILABLE[-1] + BLOCKLEN >= total:
        AVAILABLE.pop()

    encryptData = encrypt(data)
    d = chunkstring(toBin(encryptData),BLOCKLEN)
    n = len(d)
    # choose the first pixel
    pixel = coordinateToPixelNumber(startingPixel[0], startingPixel[1], img)
    if pixel == 0:
        # Choose a random location because (0, 0) is not authorized
        pixel = choice(AVAILABLE)
        AVAILABLE.remove(pixel)
        startingPixel = pixelNumberToCoordinate(pixel, img)
    for i in range(n-1):
        # pointer to the next pixel
        nextP = choice(AVAILABLE)
        AVAILABLE.remove(nextP)
        write(d[i], pixel, nextP, img)
        # switch to next pixel
        pixel = nextP
    # last pointer towards NULL (0, 0)
    write(d[-1], pixel, 0, img)

    f = imgName.split('\\')[-1]
    f_path = f'./Output/{f}'
    os.makedirs(os.path.dirname(f_path), exist_ok=True)
    img.save(f_path)
    img.close()

    dataKey = {
        'imgName' : f,
        'key' : key,
        'nonce' :nonce
    }

    rec = mydatabase.picKey.insert_one(dataKey)

    dataLocation = {
        'imgName' : f,
        'x' : startingPixel[0],
        'y' : startingPixel[1]   
    }

    rec = mydatabase.location.insert_one(dataLocation)

    return startingPixel

def get_options():
    parser = OptionParser()
    # required
    parser.add_option("-f", "--inputfile", type="string", help="Input file in witch data should be hidden.")
    parser.add_option("-d", "--data", type="string", help="Data (represented as string) to hide.")
    parser.add_option("-s", "--secretfile", type="string", help="Secret file to hide.")
    # Optionals
    parser.add_option("-o", "--outputfile", type="string", default="out.png", help="Name of the output file containing the hidden data.")
    parser.add_option("-x", type=float, help="Starting pixel's x coordinate.")
    parser.add_option("-y", type=float, help="Starting pixel's y coordinate.")
    (options, args) = parser.parse_args()

    if len(args) != 0 or not options.inputfile or (not options.data and not options.secretfile):
        parser.print_help()
        raise SystemExit

    if options.secretfile and options.data:
        print("Only one of --secretfile (-s) or --data (-d) should be provided.")
        parser.print_help()
        raise SystemExit

    if options.secretfile:
        with open(options.secretfile, "rb") as f:
            options.data = f.read()

    # force bytes
    if type(options.data) == str:
        options.data = options.data.encode()

    return options

if __name__ == '__main__':
    options = get_options()

    if options.x and options.y:
        x = hide(options.data, options.inputfile, (options.x, options.y))
    else:
        x = hide(options.data, options.inputfile)
    
    if x:
        print("Success..")
