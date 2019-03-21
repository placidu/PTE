# -*- coding: utf-8 -*-
"""
Created on Wed Oct 31 18:16:46 2018

@author: Placid
"""

import os
import ncs2py
from collections import OrderedDict
from blackfynn import Blackfynn
from numpy import arange, int64
from pandas import DataFrame
from scipy.signal import resample_poly
from datetime import datetime
#%%
def convert_ncs2bfts(dataFolder, resultFolder=None, bfFileName=None, dsName=None, fs=None):
    """
        param dataFolder: folder containing ncs files
        param resultFolder: folder to contain results
        param bfFileName: name to save generated bfts file
        param dsName: name (or id) of dataset
        param fs: sampling rate
        return: _____
    """
    dataFolder = os.path.abspath(dataFolder)
    if not bfFileName:
        bfFileName = os.path.basename(dataFolder)+'.bfts'
    if resultFolder:
        resultFolder = os.path.abspath(resultFolder)
        resultFile = os.path.join(resultFolder, bfFileName)
    else:
        resultFile = bfFileName
#
    if os.path.isfile(resultFile):
        print(bfFileName, 'exists')
    else:
        print('Converting to', bfFileName, '...')
        chls = OrderedDict() # dictionary to store channel values
        for chFile in os.listdir(dataFolder):
            if chFile.endswith('ncs'):
                ncs = ncs2py.load_ncs(os.path.join(dataFolder, chFile)) # import neuralynx data. NOTE: import stores information as a dictionary
                rawData = ncs['data']
                rawData = resample_poly(rawData, 1.0, ncs['sampling_rate']/fs)
                chls.update({'ch'+chFile.split('.')[0][3:]:rawData})
#        
        TimeCreated = [line.strip() for line in ncs['raw_header'].split('\r\n') if line != '' if 'TimeCreated' == line.strip()[1:12]][0]
        TimeCreated = ncs2py.parse_neuralynx_time_string(TimeCreated)
        TimeCreated = (TimeCreated - datetime(1970,1,1)).total_seconds()*(1e6)
        timeVec = ncs['timestamp'] + TimeCreated
        timeVec = arange(timeVec[0], timeVec[-1], (1.0/fs)*(1e6), dtype=int64)
        sampleSize = timeVec.shape[0]
#
        df = DataFrame(chls)[0:sampleSize]
        df.insert(0,'timeStamp',timeVec)
        df.to_csv(resultFile,index=False)
#
    if dsName:
        bf = Blackfynn()
        ds = bf.get_dataset(dsName)
        if os.path.basename(resultFile)[:-5] in ds.get_items_names():
            print(bfFileName, 'uploaded')
        else:
            print('uploading', bfFileName, 'to Blackfynn...')
            ds.upload(resultFile)
