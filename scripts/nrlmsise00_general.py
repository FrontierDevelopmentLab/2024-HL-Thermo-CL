from nrlmsise00 import msise_flat
import os
import numpy as np
import datetime
import argparse

class Unbuffered:
    def __init__(self, stream, logfile):
        self.stream = stream
        self.logfile = logfile

    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
        self.logfile.write(data)    # Write the data of stdout here to a text file as well
        self.logfile.flush()

    def flush(self):
        self.stream.flush()
        self.logfile.flush()

def compute_density(inputs):
    date,  alt, latitude, longitude, f107A, f107, ap = inputs
    return msise_flat(date, alt, latitude, longitude, f107A, f107, ap)[:,5]*1e3



def create_groups(N, group_size=100):
    groups = []
    for i in range(0, N + 1, group_size):
        group = list(range(i, min(i + group_size, N )))
        groups.append(np.array(group))
    return groups

def valid_date(s):
    try:
        return datetime.datetime.strptime(s, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        raise argparse.ArgumentTypeError(f'Not a valid date: {s}. Expecting YYYYMMDDHHMMSS.')
    