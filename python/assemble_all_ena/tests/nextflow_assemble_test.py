import glob
from operator import itemgetter
import json
import os
import sys
import shutil
import subprocess
import unittest

from assemble_all_ena import sample_dirs, utils

sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
import nextflow_helper
data_dir = os.path.join(nextflow_helper.data_root_dir, 'nextflow_assemble')
modules_dir = os.path.dirname(os.path.abspath(sample_dirs.__file__))


class TestNextflowAssemble(unittest.TestCase):
    def test_nextflow_assemble(self):
        '''test nextflow_assemble'''
        nextflow_helper.write_config_file()
        input_dir = 'tmp.nextflow_assemble.dir'
        utils.rmtree(input_dir)
        samples = ['ERS1', 'ERS2', 'ERS3']
        samples_file = 'tmp.nextflow_assemble.samples'
        with open(samples_file, 'w') as f:
            print(*samples, sep='\n', file=f)

        sdirs = sample_dirs.SampleDirs(input_dir)
        sdirs.add_samples(samples_file)
        os.unlink(samples_file)

        nextflow_file = os.path.join(nextflow_helper.nextflow_dir, 'assemble.nf')
        work_dir = 'tmp.nextflow_assemble.work'
        outdir = 'tmp.nextflow_assemble.out'

        command = ' '.join([
            'nextflow run',
            '--input_dir', input_dir,
            '--testing',
            '--shovill_tempdir /foo/bar',
            '-c', nextflow_helper.config_file,
            '-w ', work_dir,
            nextflow_file,
        ])

        try:
            completed_process = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        except subprocess.CalledProcessError as e:
            print('Error running nextflow\nCommand: ', command)
            print('Output:', e.stdout.decode(), sep='\n')
            print('\n____________________________________\n')
            self.assertTrue(False)

        expected_json = {
            "ERS3": {
                "reads": False,
                "asm": True,
                "annot": False,
                "ignore": False
                },
            "ERS1": {
                "reads": False,
                "asm": True,
                "annot": False,
                "ignore": False
                },
            "ERS2": {
                "reads": False,
                "asm": True,
                "annot": False,
                "ignore": False
                }
        }

        self.maxDiff = None

        sdirs = sample_dirs.SampleDirs(input_dir)
        self.assertEqual(expected_json, sdirs.sample_data)
        utils.rmtree(input_dir)
        utils.rmtree(work_dir)
        nextflow_helper.clean_files()
