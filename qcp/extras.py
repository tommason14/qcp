#!/usr/bin/env python3

from general import find_files
from pprint import noFiles
from utils import (get_files, 
                   read_file, 
                   write_csv_from_nested,
                   search_dict_recursively)

# decorator for the csv function to print data before writing
# no capability to change original function
# - used in too many places, lots of work to change
def print_data(f):
    def inner(*args, **kwargs):
        # know we have a col_names list
        # find max lengh of filepath for pretty printing
        data = []
        max_filename_length = 0
        max_root_length = 0
        for a in args:
            if isinstance(a, list):
                for line in a:
                    data.append(line)
                    config, root, iteration, wavelength, intensity = line
                    if len(config) > max_filename_length:
                        max_filename_length = len(config)
                    if len(root) > max_root_length:
                        max_root_length = len(root)
        # add some padding
        config_length = max_filename_length + 4
        root_length = max_root_length + 4
        boxsize = config_length + root_length + 9 + 15 + 15 + 14 # 12 is space between each column 
        print('+' +  '-' * boxsize + '+')
        print("| {:^{}} | {:^{}} | {:^{}} | {:^{}}| {:^{}} |".format('Config', config_length, 'Root', root_length, 'Iteration', 9, 'Wavelength (nm)', 16, 'Intensity (au)', 15))
        print('|' + '-' * boxsize + '|')
        
        for line in data: 
            config, root, iteration, wavelength, intensity = line
            print("| {:^{}} | {:^{}} | {:^{}} | {:^{}}| {:^{}} |".format(config, config_length, root, root_length, iteration, 9, wavelength, 16, intensity, 15))
        print('+' +  '-' * boxsize + '+')
        return f(*args, **kwargs)
    return inner


def is_gaussian(file):
    """Returns True if file is a Gaussian output"""
    for line in read_file(file):
        if 'Gaussian' in line:
            return True
    return False


def is_fluorescence(file):
    """
    Assuming a time-dependent DFT calculation for fluorescence.
    Returns True if yes
    """
    for line in read_file(file):
        if 'TD=' in line:
            return True
    return False


def get_fluorescence_logs():
    files = get_files('.', ('log', 'out'))
    # remove f- files from qcp results output
    for file in files:
        if 'f-' in file:
            files.remove(file)

    # path = '.'
    # level = False # all levels
    # level = input('Number of subdirs [0-9]: ')
    # file_pattern = ['.log', '.out'] 
    # files        = find_files(path, level, file_pattern)
    # if len(files) == 0:
    #     noFiles()
    # for path, file in files:   
    #     print(path, file)
    return files


def user_choice():
    print('Return all peaks or only intense peaks?')
    print('1. All')
    print('2. Only intense peaks')
    choice = input('Choice: [1] ')
    if choice == '1':
        cutoff = 0
    elif choice == '2':
        cutoff = input('Collect peaks with intensity above which value? [0.1] ')
        if cutoff is not "":
            try:
                cutoff = float(cutoff)
            except:
                print('Incorrect value passed, assuming 0.1 is the cutoff')
                cutoff = 0.1
        else:
            cutoff = 0.1

    return cutoff


def update_dict_with_name(file, d):
    file = file.replace('./', '')
    *path, f = file.split('/')
    f = f.split('.')[0] # lose file extension
    filepath = path + [f]
    name = None 
    # if uv_vis or uv-vis in path, take the preceeding values
    for ind, val in enumerate(filepath):
        if ('uv_vis' in val or 'uv-vis' in val) and 'init' not in val:
            name = '/'.join(filepath[:ind])
    if name is None:
        name = '/'.join(filepath) 
    if name not in d:
        d[name] = {}
    return d, name


def find_root(file, d, name):
    root = None
    for line in read_file(file):
        if 'root=' or 'root =' in line:
            line = line.split()
            for i, val in enumerate(line):
                if 'root=' in val:
                    root = val.split('=')[-1][:-1]
    if root is None: # keep track of lines
        root = 'initial_spectra'
    d[name][root] = {}
    d[name][root]['peaks'] = {}
    return d, root

def reassign_root_of_initial_spectra(d, name, root, iteration, intensity, wavelength, number, cutoff):
    """
    If the file being searched is run to find the 
    roots to take forward, need to know the roots!
    
    This function reassigns the value in the 'root'
    column to reflect this
    """
    if 'initial_spectra' in d[name]:
        d[name].pop(root)
    new_key = f'initial spectra: root {number + 1}' 
    if new_key not in d[name]:
        d[name][new_key] = {}
        d[name][new_key]['peaks'] = {}
        if iteration not in d[name][new_key]['peaks']:
            d[name][new_key]['peaks'][iteration] = []
    if intensity > cutoff:
        d[name][new_key]['peaks'][iteration].append((wavelength, intensity))
    return d

def find_spectral_data(file, d, name, root, cutoff):
    iteration = 0   
    # faster to collect lines first and parse after, probably
    lines = [line for line in read_file(file) if 'Excited State' in line]        
    for number, line in enumerate(lines):
        intensity = None
        wavelength = None
        if ' 1: ' in line: #space important, or 11: could be picked up
            iteration += 1
            d[name][root]['peaks'][iteration] = []
        line = line.split()
        for index, item in enumerate(line):
            if 'nm' in item:
                wavelength = float(line[index - 1])
            if 'f=' in item:
                intensity = float(item.split('=')[1])
        if root == 'initial_spectra':
            d = reassign_root_of_initial_spectra(d, name, root, iteration, intensity, wavelength, number, cutoff)
        else:
            if intensity > cutoff:
                d[name][root]['peaks'][iteration].append((wavelength, intensity))
    return d

def grep_data(cutoff, files):
    """Return a dictionary of data in the form
    
    data = {
        config : {
            root : {
                peaks: { 
                    iter1: [(wavelength_1, intensity_1),
                            (wavelength_2, intensity_2)],
                    iter2: [(wavelength_1, intensity_1),
                            (wavelength_2, intensity_2)],
                   }
                 }
           }
    """
    res = {}
    for file in files:
        if is_gaussian(file) and is_fluorescence(file):
            res, name = update_dict_with_name(file, res)
            res, root = find_root(file, res, name)
            res = find_spectral_data(file, res, name, root, cutoff)   
    return res


def transform(res):
    """ Transforms dictionary to a list of lists """
    flattened = []
    for name in sorted(res):
        for root in res[name]:
            for iteration in res[name][root]['peaks']:
                for peak in res[name][root]['peaks'][iteration]:
                    wave, intensity = peak
                    flattened.append([name, root, iteration, wave, intensity])
    return flattened

def get_fluorescence_data():
    write_data = print_data(write_csv_from_nested)
    files = get_fluorescence_logs()
    cutoff = user_choice()
    data = grep_data(cutoff, files)
    data = transform(data)
    write_data(data, col_names = ['config', 'root', 'iteration', 'wavelength (nm)', 'intensity (a.u.)'])

if __name__ == '__main__':
    main()
