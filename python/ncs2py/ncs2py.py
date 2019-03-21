#coding=utf-8

"""
    Author: Placid Unegbu
    Version: 2
    
    Credit:
    https://github.com/alafuzof/NeuralynxIO
"""
import os
import warnings
import numpy as np
import datetime

HEADER_LENGTH = 16 * 1024  # 16 kilobytes of header 

NCS_SAMPLES_PER_RECORD = 512
NCS_RECORD = np.dtype([('TimeStamp',       np.uint64),       # Cheetah timestamp for this record. This corresponds to
                                                             # the sample time for the first data point in the Samples
                                                             # array. This value is in microseconds.
                       ('ChannelNumber',   np.uint32),       # The channel number for this record. This is NOT the A/D
                                                             # channel number
                       ('SampleFreq',      np.uint32),       # The sampling frequency (Hz) for the data stored in the
                                                             # Samples Field in this record
                       ('NumValidSamples', np.uint32),       # Number of values in Samples containing valid data
                       ('Samples',         np.int16, NCS_SAMPLES_PER_RECORD)])  # Data points for this record. Cheetah
                                                                                # currently supports 512 data points per
                                                                                # record. At this time, the Samples
                                                                                # array is a [512] array.
																				

VOLT_SCALING = (1, 'V')
MILLIVOLT_SCALING = (1000, 'mV')
MICROVOLT_SCALING = (1000000, 'µV')

def read_header(fid):
    # Read the raw header data (16 kb) from the file object fid. Restores the position in the file object after reading.
    pos = fid.tell()
    fid.seek(0)
    raw_hdr = fid.read(HEADER_LENGTH).strip(b'\0')
    fid.seek(pos)

    return raw_hdr.decode('utf-8')

def read_records(fid, record_dtype, record_skip=0, count=None):
    # Read count records (default all) from the file object fid skipping the first record_skip records. Restores the
    # position of the file object after reading.
    if count is None:
        count = -1

    pos = fid.tell()
    fid.seek(HEADER_LENGTH, 0)
    fid.seek(record_skip * record_dtype.itemsize, 1)
    rec = np.fromfile(fid, record_dtype, count=count)
    fid.seek(pos)

    return rec

def parse_header(raw_hdr):
    # Parse the header string into a dictionary of name value pairs
    hdr = dict()
    
    # Neuralynx headers seem to start with a line identifying the file, so
    # let's check for it
    hdr_lines = [line.strip() for line in raw_hdr.split('\r\n') if line != '']
    if hdr_lines[0] != '######## Neuralynx Data File Header':
        warnings.warn('Unexpected start to header: ' + hdr_lines[0])

    # Try to read the original file path
    try:
        assert hdr_lines[5][1:].split()[0] == 'OriginalFileName'
        hdr['OriginalFileName']  = ' '.join(hdr_lines[5][1:].split()[1:])
    except:
        warnings.warn('Unable to parse original file path from Neuralynx header: ' + hdr_lines[5])

    # Process lines with file opening and closing times
    hdr['TimeCreated'] = hdr_lines[6][1:]
    hdr['TimeCreated_dt'] = parse_neuralynx_time_string(hdr_lines[6][1:])
    hdr['TimeClosed'] = hdr_lines[7][1:]
    hdr['TimeClosed_dt'] = parse_neuralynx_time_string(hdr_lines[7][1:])

    # Read the parameters, assuming "-PARAM_NAME PARAM_VALUE" format
    a = list(range(len(hdr_lines)))
    for ii in range(5,7+1):
        a.remove(ii)
    
    for line in [hdr_lines[ii] for ii in a][1:]:
        try:
            parameters = line[1:].split()  # Ignore the dash and split PARAM_NAME and PARAM_VALUE
            name = parameters[0]
            value = ''.join(parameters[1:])
            hdr[name] = value
        except:
            warnings.warn('Unable to parse parameter line from Neuralynx header: ' + line)

    return hdr

def parse_neuralynx_time_string(time_string):
    # Parse a datetime object from the idiosyncratic time string in Neuralynx file headers
    try:
        tmp_date = [int(x) for x in time_string.split()[1].split('/')]
        tmp_time = [int(x) for x in time_string.split()[-1].replace('.', ':').split(':')]
        if len(tmp_time) == 3:
            tmp_microsecond = 0
        else:
            tmp_microsecond = tmp_time[3] * 1000
    except:
        warnings.warn('Unable to parse time string from Neuralynx header: ' + time_string)
        return None
    else:
        return datetime.datetime(tmp_date[0], tmp_date[1], tmp_date[2],  # Year, month, day
                                 tmp_time[0], tmp_time[1], tmp_time[2],  # Hour, minute, second
                                 tmp_microsecond)

def check_ncs_records(records):
    # Check that all the records in the array are "similar" (have the same sampling frequency etc.
    dt = np.diff(records['TimeStamp'])
    dt = np.abs(dt - dt[0])
    if not np.all(records['ChannelNumber'] == records[0]['ChannelNumber']):
        warnings.warn('Channel number changed during record sequence')
        return False
    elif not np.all(records['SampleFreq'] == records[0]['SampleFreq']):
        warnings.warn('Sampling frequency changed during record sequence')
        return False
    elif not np.all(records['NumValidSamples'] == 512):
        warnings.warn('Invalid samples in one or more records')
        return False
    elif not np.all(dt <= 1):
        warnings.warn('Time stamp difference tolerance exceeded')
        return False
    else:
        return True

def load_ncs(file_path, load_time=True, rescale_data=True, signal_scaling=MICROVOLT_SCALING):
    # Load the given file as a Neuralynx .ncs continuous acquisition file and extract the contents
    file_path = os.path.abspath(file_path)
    with open(file_path, 'rb') as fid:
        raw_header = read_header(fid)
        records = read_records(fid, NCS_RECORD)

    header = parse_header(raw_header)
    check_ncs_records(records)

    # Reshape (and rescale, if requested) the data into a 1D array
    data = records['Samples'].ravel()
    if rescale_data:
        try:
            # ADBitVolts specifies the conversion factor between the ADC counts and volts
            data = data.astype(np.float64) * (np.float64(header['ADBitVolts']) * signal_scaling[0])
        except KeyError:
            warnings.warn('Unable to rescale data, no ADBitVolts value specified in header')
            rescale_data = False

    # Pack the extracted data in a dictionary that is passed out of the function
    ncs = dict()
    ncs['file_path'] = file_path
    ncs['raw_header'] = raw_header
    ncs['header'] = header
    ncs['data'] = data
    ncs['data_units'] = signal_scaling[1] if rescale_data else 'ADC counts'
    ncs['sampling_rate'] = records['SampleFreq'][0]
    ncs['channel_number'] = records['ChannelNumber'][0]
    ncs['timestamp'] = records['TimeStamp']

    # Calculate the sample time points (if needed)
    if load_time:
        num_samples = data.shape[0]
        times = np.interp(np.arange(num_samples), np.arange(0, num_samples, 512), records['TimeStamp']).astype(np.uint64)
        ncs['time'] = times
        ncs['time_units'] = 'µs'

    return ncs