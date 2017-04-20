        
import sys, os

### OS MAGIC ###

if sys.platform == "win32": # We are running on windows
    import datetime
    year = datetime.date.today().year
    stop = False
    for y in range(2000, year + 1 ):
        y = str(y)[-2:]
        try:
            print("Detecting visual studio [" + "VS"+y+"0" + "] installation in : " + os.environ["VS"+y+"0COMNTOOLS"])
            os.environ["VS90COMNTOOLS"] = os.environ["VS"+y+"0COMNTOOLS"]
            stop = True
        except:
            pass
        if stop:
            break
    if not stop:
        print("Will use binary files instead of cython") # If we dont find them, we wont use cython then.
    # Actually, we are detecting the OS
    # We must add to the current path the link to the build tools.
    # Since we dont know wich one we have, we go through every possible path
    # (aka current year - 2000) and we check if it exists.
    # If it does, we add it then we stop searching.
    # See http://stackoverflow.com/a/10558328/625189

elif sys.platform == "darwin":
    path = '/usr/local/Cellar/gcc/'
    name_list = os.listdir(path)
    full_list = [os.path.join(path,i) for i in name_list]
    time_sorted_list = sorted(full_list, key=os.path.getmtime)[::-1]
    found = False
    for p in time_sorted_list:
        try:
            version = p.split('/')[-1].split('.')[0]
            p += "/bin/"
            CXX = p + "g++-" + version
            CC = p + "gcc-" + version
            if os.path.isfile(CXX) and os.path.isfile(CC):
                found = True
                break
        except:
            continue
    if found:
        os.environ["CXX"] = CXX
        os.environ["CC"] = CC
    # TODO : Do something more elegant, using the $PATH and testing gcc instances with -fopenmp ie.
    # See https://github.com/ppwwyyxx/OpenPano/issues/16

### END OF OS MAGIC ###

import argparse
from core import ConfigParser

def IntegrityTest():
    import json, os
    from skimage import io
    import numpy as np

    # Disable
    def blockPrint():
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    # Restore
    def enablePrint():
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

    def dice(path1, path2):
        # https://gist.github.com/JDWarner/6730747
        im1 = io.imread(path1, as_grey=True)
        im2 = io.imread(path2, as_grey=True)

        im1 = np.asarray(im1).astype(np.bool)
        im2 = np.asarray(im2).astype(np.bool)

        if im1.shape != im2.shape:
            raise ValueError("Shape mismatch: im1 and im2 must have the same shape.")

        # Compute Dice coefficient
        intersection = np.logical_and(im1, im2)

        return 2. * intersection.sum() / (im1.sum() + im2.sum())


    j_name = "__IntegrityTest__.json"
    j_file = """{
   "preprocessing":[
      {
         "name":"AxonSeg",
         "params":{
            "input":"../config/input/Simulation_img.tif",
            "output":"Simulation_img.bin",
            "outputImage":"Simulation_img.png",
            "minSize":30,
            "maxSize":1600,
            "Solidity":0.7,
            "MinorMajorRatio":0.85,
            "display": "full",
            "displayColorLow":"0,0,255",
            "displayColorHigh":"255,0,0"
         }
      }
   ],
   "axonSegmentation":[
   ],
   "axonPostProcessing":[
      {
         "name":"MyelinSeg",
         "params":{
            "inputList": "Simulation_img.bin",
            "input":"../config/input/Simulation_img.tif",
            "outputImage":"Simulation_img.melyn.png",
            "outputList":"Simulation_img.melyn.csv",
            "minSize":30,
            "maxSize":1600,
            "Solidity":0.7,
            "MinorMajorRatio":0.85,
            "display":"full",
            "displayColorLow":"0,0,255",
            "displayColorHigh":"255,0,0"
         }
      }
   ]
}"""
    with open(j_name, 'w') as f:
        f.write(j_file)

    blockPrint()
    failure = False
    try:
        ConfigParser.parse(j_name)
    except:
        failure = True
    enablePrint()
    if failure:
        print("Error running tests, crash detected !")

    if (not os.path.isfile("Simulation_img.bin")) or (not os.path.isfile("Simulation_img.png")) :
        failure = True
        print("Error, failed the segmentation phase !")
    if (not os.path.isfile("Simulation_img.melyn.csv")) or (not os.path.isfile("Simulation_img.melyn.png")) :
        failure = True
        print("Error, failed the melyn phase !")

    if failure:
        try:
            os.remove(j_name)
            os.remove("Simulation_img.bin")
            os.remove("Simulation_img.png")
            os.remove("Simulation_img.melyn.png")
            os.remove("Simulation_img.melyn.csv")
        except:
            pass
        exit(-1)

    melyn = open("Simulation_img.melyn.csv").readlines()
    melyn = list(filter(None, melyn))

    EXPECTED_AXON = 200
    axonFound = len(melyn)
    print("Found %i/%i axon with current algorithmes. This is a %f%% difference !" % ( axonFound, EXPECTED_AXON, (EXPECTED_AXON - axonFound)/EXPECTED_AXON*100))
    try:
        dicing = dice("../config/input/Simulation_img.tif", "Simulation_img.melyn.png")
        print("And Mask is %f%% similar to original image." % (dicing * 100.0))
    except: 
        print("Dicing failed ! Error in melyn phase !")

    os.remove(j_name)
    os.remove("Simulation_img.bin")
    os.remove("Simulation_img.png")
    os.remove("Simulation_img.melyn.png")
    os.remove("Simulation_img.melyn.csv")



def main():
    # Get args
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config') 
    parser.add_argument('-t', '--test', action='store_true')

    # Parse args
    args = parser.parse_args()
    config = args.config
    test  = args.test

    if test == True:
        IntegrityTest()
    else :
        if config == "" or config == None:
            config = os.getcwd() + "/config.json" # Local configuration

        # We initialise the algo runner with an aldo
        ConfigParser.parse(config)

if __name__ == "__main__":
    main()
