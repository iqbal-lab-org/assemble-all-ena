import filecmp
import os
import unittest

from assemble_all_ena import sample_dir, sample_dirs, utils

modules_dir = os.path.dirname(os.path.abspath(sample_dirs.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'sample_dirs')


class TestSampleDirs(unittest.TestCase):
    def test_sample_name_to_directory(self):
        '''test sample_name_to_directory'''
        tests = [
            ('123', None),
            ('ABC', None),
            ('SAM123', os.path.join('SAM', '12', '3')),
            ('SAM1234', os.path.join('SAM', '12', '34')),
            ('SAMD1234', os.path.join('SAMD', '12', '34')),
            ('ERS1234567', os.path.join('ERS', '12', '34', '56', '7')),
        ]

        for sample_id, expected_dir in tests:
            if expected_dir is None:
                with self.assertRaises(Exception):
                    got = sample_dirs.SampleDirs.sample_name_to_directory(sample_id)
            else:
                got = sample_dirs.SampleDirs.sample_name_to_directory(sample_id)
                self.assertEqual(expected_dir, got)


    def test_tsv_for_nextflow_pipeline(self):
        '''test _tsv_for_nextflow_pipeline'''
        json_data = {
            'SAM123': {'reads': False, 'asm': False, 'annot': False, 'ignore': False},
            'SAM4567': {'reads': True, 'asm': False, 'annot': False, 'ignore': False},
            'ERS12345': {'reads': True, 'asm': True, 'annot': False, 'ignore': False},
        }

        outfile = 'tmp.sample_dirs.tsv_for_nextflow_pipeline.tsv'
        sample_dirs.SampleDirs._tsv_for_nextflow_pipeline(json_data, 'root_dir', outfile)
        expect_file = os.path.join(data_dir, 'tsv_for_nextflow_pipeline.tsv')
        self.assertTrue(filecmp.cmp(expect_file, outfile, shallow=False))
        os.unlink(outfile)


    def test_add_samples(self):
        '''test add_samples'''
        tmp_dir = 'tmp.sample_dirs.add_samples'
        utils.rmtree(tmp_dir)
        sdirs = sample_dirs.SampleDirs(tmp_dir)
        self.assertTrue(os.path.exists(sdirs.sample_data_json_file))

        new_samples = ['ABC123', 'ABC123']
        samples_file = 'tmp.new_samples'
        with open(samples_file, 'w') as f:
            print(*new_samples, sep='\n', file=f)
        with self.assertRaises(Exception):
            sdirs.add_samples(samples_file)


        expect_dict = {'ABC123': {'reads': False, 'asm': False, 'annot': False, 'ignore': False}}
        new_samples = ['ABC123']
        with open(samples_file, 'w') as f:
            print(*new_samples, sep='\n', file=f)
        sdirs.add_samples(samples_file)
        self.assertEqual(expect_dict, sdirs.sample_data)

        with self.assertRaises(Exception):
            sdirs.add_samples(samples_file)

        new_samples = ['SAMN42']
        expect_dict['SAMN42'] = {'reads': False, 'asm': False, 'annot': False, 'ignore': False}
        with open(samples_file, 'w') as f:
            print(*new_samples, sep='\n', file=f)
        sdirs.add_samples(samples_file)
        self.assertEqual(expect_dict, sdirs.sample_data)

        os.unlink(samples_file)

        sdirs = sample_dirs.SampleDirs(tmp_dir)
        self.assertEqual(expect_dict, sdirs.sample_data)
        utils.rmtree(tmp_dir)


    def test_update_sample_data(self):
        '''test update_sample_data'''
        tmp_dir = 'tmp.sample_dirs.update_sample_data'
        samples_file = 'tmp.sample_dirs.update_sample_data.new_samples'
        utils.rmtree(tmp_dir)
        sdirs = sample_dirs.SampleDirs(tmp_dir)
        self.assertTrue(os.path.exists(sdirs.sample_data_json_file))
        expect_dict = {'ABC123': {'reads': False, 'asm': False, 'annot': False, 'ignore': False}}
        new_samples = ['ABC123']
        with open(samples_file, 'w') as f:
            print(*new_samples, sep='\n', file=f)
        sdirs.add_samples(samples_file)
        self.assertEqual(expect_dict, sdirs.sample_data)
        sdir = sdirs.make_sample_dir('ABC123')
        sdir.metadata['reads_downloaded'] = True
        sdir.write_metadata_json()
        sdirs.update_sample_data()
        expect_dict['ABC123']['reads'] = True
        self.assertEqual(expect_dict, sdirs.sample_data)

        new_samples = ['ERS42', 'ERS43']
        with open(samples_file, 'w') as f:
            print(*new_samples, sep='\n', file=f)
        sdirs.add_samples(samples_file)
        sdirs.update_sample_data()
        expect_dict['ERS42'] = {'reads': False, 'asm': False, 'annot': False, 'ignore': False}
        expect_dict['ERS43'] = {'reads': False, 'asm': False, 'annot': False, 'ignore': False}
        self.assertEqual(expect_dict, sdirs.sample_data)

        sdir42 = sdirs.make_sample_dir('ERS42')
        sdir42.metadata['reads_downloaded'] = True
        sdir42.metadata['assembled'] = True
        sdir42.write_metadata_json()
        sdir43 = sdirs.make_sample_dir('ERS43')
        sdir43.metadata['reads_downloaded'] = True
        sdir43.write_metadata_json()
        with open(samples_file, 'w') as f:
            print('ERS42', file=f)
        sdirs.update_sample_data(file_of_sample_names=samples_file)
        expect_dict['ERS42'] = {'reads': True, 'asm': True, 'annot': False, 'ignore': False}
        self.assertEqual(expect_dict, sdirs.sample_data)

        sdirs = sample_dirs.SampleDirs(tmp_dir)
        self.assertEqual(expect_dict, sdirs.sample_data)
        utils.rmtree(tmp_dir)
        os.unlink(samples_file)

