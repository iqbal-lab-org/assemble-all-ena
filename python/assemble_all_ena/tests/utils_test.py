import filecmp
import json
import os
import shutil
import unittest

from assemble_all_ena import utils

modules_dir = os.path.dirname(os.path.abspath(utils.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'utils')


class TestUtils(unittest.TestCase):
    def test_add_prefix_to_seqs(self):
        '''test add_prefix_to_seqs'''
        infile = os.path.join(data_dir, 'add_prefix_to_seqs.in.fa')
        expect_outfile = os.path.join(data_dir, 'add_prefix_to_seqs.out.fa')
        tmp_out = 'tmp.add_prefix_to_seqs.fa'
        utils.add_prefix_to_seqs(infile, tmp_out, 'PREFIX.')
        self.assertTrue(filecmp.cmp(expect_outfile, tmp_out, shallow=False))
        os.unlink(tmp_out)

