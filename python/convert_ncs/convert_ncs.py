import os
import ncs2bfts
import scipy.io as sio
import pandas as pd

def to_bfts(dsDirectory, resultFolderName, folders2exclude=[], folders2exclude2=[], dsName=None, fs=2000.0):
    """
        param dsDirectory: dataset directory (ex.,'/mnt/local/gdrive/public/USERS/punegbu/PTE' )
        param resultFolderName: name of folder to contain results (ex., 'pyData2000Hz')
        param folders2exclude: folders to exclude
        param folders2exclude2: folders to exclude
        param dsName: dataset name
        param fs: sampling rate
        return: _____
    """
    for folders in os.listdir(dsDirectory):
        if folders not in folders2exclude:
            for folders2 in os.listdir(os.path.join(dsDirectory, folders)):
                if folders2 not in folders2exclude2:
                    for folders3 in os.listdir(os.path.join(dsDirectory, folders, folders2)):
                        if folders3 == 'rawData':
                            dataDirectory = os.path.join(dsDirectory, folders, folders2, folders3)
                            print(dataDirectory, end=': ')
                            print(len(os.listdir(dataDirectory)), 'files')
                            resultFolder = os.path.join(dsDirectory, folders, folders2, resultFolderName)
                            if not os.path.isdir(resultFolder):
                                os.mkdir(resultFolder)
                            for dataFolderName in os.listdir(dataDirectory):
                                dataFolder = os.path.join(dataDirectory, dataFolderName)
                                ncs2bfts.convert_ncs2bfts(dataFolder, resultFolder=resultFolder, dsName=dsName, fs=fs)
                        else:
                            print(folders3+': not rawData folder')
                else:
                    print('skipping', folders2)
        else:
            print('skipping', folders)
    print('All done!')

def to_mat(dsDirectory, desiredFolderName, resultFolderName, folders2exclude=[], folders2exclude2=[]):
    """
        param dsDirectory: dataset directory
        param desiredFolderName: name of folder to look for
        param resultFolderName: name of folder to contain results
        param folders2exclude: folders to exclude
        param folders2exclude2: folders to exclude
        return: _____
    """
    for folders in os.listdir(dsDirectory):
        if folders not in folders2exclude:
            for folders2 in os.listdir(os.path.join(dsDirectory, folders)):
                if folders2 not in folders2exclude2:
                    for folders3 in os.listdir(os.path.join(dsDirectory, folders, folders2)):
                        if folders3 == desiredFolderName:
                            bftsFolder = os.path.join(dsDirectory, folders, folders2, folders3)
                            print(bftsFolder, end=': ')
                            print(len(os.listdir(bftsFolder)), 'files')
                            resultFolder = os.path.join(dsDirectory, folders, folders2, resultFolderName)
                            if not os.path.isdir(resultFolder):
                                os.mkdir(resultFolder)
                            for dataFile in os.listdir(bftsFolder):
                                dataFileName = dataFile.replace('bfts', 'mat')
                                temp_resultFile = os.path.join(resultFolder, dataFileName)
                                if os.path.isfile(temp_resultFile):
                                    print(dataFileName, 'exists')
                                else:
                                    print('Converting to', dataFileName, '...')
                                    df = pd.read_csv(os.path.join(bftsFolder, dataFile))
                                    sio.savemat(temp_resultFile, {'data':df.iloc[:,1:].values})
                        else:
                            print(folders3+':', 'not', desiredFolderName, 'folder')
                else:
                    print('skipping', folders2)
        else:
            print('skipping', folders)
    print('All done!')