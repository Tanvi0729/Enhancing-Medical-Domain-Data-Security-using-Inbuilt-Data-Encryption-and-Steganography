#!/usr/bin/env python3
#encoding: UTF-8

from PIL import Image
import binascii
from optparse import OptionParser
import pyaes, pbkdf2, secrets, os
from pymongo import MongoClient
import numpy as np
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


client = MongoClient('mongodb://localhost:27017')
mydatabase = client['ImgStegno']
pikKey = mydatabase['picKey']
location = mydatabase['location']

def pixelNumberToCoordinate(n, img):
    return (n%img.size[0], n//img.size[0])

def coordinateToPixelNumber(x, y, img):
    return y*img.size[0]+x

def binToString(i):
    # pad i to be a multiple of 8
    if len(i) % 8 != 0:
        r = 8-(len(i)%8)
        i = i + "0"*r
    h = hex(int(i, 2))[2:]
    if len(h) % 2 != 0:
        h = "0"+h
    # remove last null byte
    return binascii.unhexlify(h)

def getData(img, startX, startY):
    n = coordinateToPixelNumber(startX, startY, img)
    pix = img.load()
    BLOCKLEN = len(bin(max(img.size))[2:])
    nx = ""
    ny = ""
    s = ""
    for i in range(BLOCKLEN):
        c = pixelNumberToCoordinate(n+i, img)
        s += str(pix[c][0] & 1)
        nx += str(pix[c][1] & 1)
        ny += str(pix[c][2] & 1)
    nx = int(nx, 2)
    ny = int(ny, 2)
    return (s,(nx, ny))

def decryptData(f, data):
    print(type(data))
    fname = f.split("\\")[-1]

    cursor = pikKey.find({'imgName' : fname})

    key = cursor[0]['key']
    nonce = cursor[0]['nonce']

    pikKey.delete_one({'imgName' : fname})

    cipher = AES.new(key, AES.MODE_CTR, nonce=nonce)
    de_data = cipher.decrypt(data)
    # print(de_data)
    return de_data
    # AESkey = cursor[0]['AESkey']
    # k = int(cursor[0]['k'])

    # pikKey.delete_one({'imgName' : fname})

    # aes = pyaes.AESModeOfOperationCTR(AESkey, pyaes.Counter(k))
    # decrypted = aes.decrypt(data)
    # return decrypted

def unhide(imgName):
    f = imgName
    img = f.split('\\')[-1]

    try:
        cursor = location.find({'imgName' : img})
        startX = cursor[0]['x']
        startY = cursor[0]['y']

        print(startX, startY)
        
        location.delete_one({'imgName' : img})
        img = Image.open(imgName)
        data, p = getData(img, startX, startY)
        while p != (0, 0):
            d, p = getData(img, p[0], p[1])
            data += d
        encryptData = binToString(data)

        return (decryptData(imgName, encryptData))
    except:
        print("No location Found..")


def get_options():
    parser = OptionParser()
    # required
    parser.add_option("-f", "--inputfile", type="string", help="Input file in witch data is hidden.")
    parser.add_option("-x", type=float, help="Starting pixel's x coordinate.")
    parser.add_option("-y", type=float, help="Starting pixel's y coordinate.")
    # Optionals
    parser.add_option("-o", "--outputfile", type="string", help="Name of the output file to write the hidden data to.")

    (options, args) = parser.parse_args()

    if len(args) != 0 or not options.inputfile:
        parser.print_help()
        raise SystemExit

    return options

if __name__ == '__main__':
    options = get_options()

    f = options.inputfile
    img = f.split('\\')[-1]

    try:
        cursor = location.find({'imgName' : img})
        x = cursor[0]['x']
        y = cursor[0]['y']
        location.delete_one({'imgName' : img})

        data = unhide(options.inputfile, x, y)            
        if options.outputfile:
            with open(options.outputfile, "wb") as f:
                f.write(data)
        else:
            print(data)
    except:
        print("No location Found..")