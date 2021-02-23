import hashlib
import os
import subprocess

import pyfastaq


def rmtree(input_dir):
    subprocess.check_output(f'rm -rf {input_dir}', shell=True)


def md5(filename):
    '''Given a file, returns a string that is the md5 sum of the file'''
    # see https://stackoverflow.com/questions/3431825/generating-an-md5-checksum-of-a-file
    hash_md5 = hashlib.md5()
    with open(filename, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def wget(url, outfile, known_md5=None):
    command = f'wget -c -q -O {outfile} {url}'
    try:
        subprocess.check_output(command, shell=True)
    except:
        raise Exception(f'Error running {command}')

    if known_md5 is not None:
        got_md5 = md5(outfile)
        if known_md5 != got_md5:
            raise Exception(f'md5 mismatch. Expected {known_md5} but got {got_md5}. command: {command}')


def touch(filename):
    with open(filename, 'a') as f:
        pass


def gzip(filename):
    command = f'gzip -9 {filename}'
    try:
        subprocess.check_output(command, shell=True)
    except:
        raise Exception(f'Error running {command}')


def add_prefix_to_seqs(infile, outfile, prefix):
    seq_reader = pyfastaq.sequences.file_reader(infile)
    f_out = pyfastaq.utils.open_file_write(outfile)
    for sequence in seq_reader:
        sequence.id = prefix + sequence.id
        print(sequence, file=f_out)
    pyfastaq.utils.close(f_out)
