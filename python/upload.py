# -*- coding: utf-8 -*-
"""
Created on Sun Feb 24 18:58:11 2019

@author: Placid
"""

# should be ran in the /pyhon folder
import convert_ncs

dsDirectory = r'C:\Users\Placid\OneDrive - PennO365\Litt_Lab\PTE'
resultFolderName = 'pyData2000Hz'
resultFolderName2 = 'matData2000Hz'

# folders2exclude = ['1st_month', 'long_data', 'spike_data', 'Data_February2019']
# convert_ncs.to_bfts(dsDirectory, resultFolderName, folders2exclude=folders2exclude, dsName='John Wolf Data')

folders2exclude = ['1st_month', 'long_data']
convert_ncs.to_bfts(dsDirectory, resultFolderName, folders2exclude=folders2exclude, dsName=None, fs=2000.0)
convert_ncs.to_mat(dsDirectory, resultFolderName, resultFolderName2, folders2exclude=folders2exclude)