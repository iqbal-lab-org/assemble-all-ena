import filecmp
import json
import os
import shutil
import unittest
from unittest import mock

from assemble_all_ena import sample_dir, utils

modules_dir = os.path.dirname(os.path.abspath(sample_dir.__file__))
data_dir = os.path.join(modules_dir, 'tests', 'data', 'sample_dir')


class TestSampleDir(unittest.TestCase):
    def test_init_and_write_metadata_json(self):
        '''test init and write_metadata_json'''
        tmp_dir = 'tmp.sample_dir.init_and_write_metadata_json'
        utils.rmtree(tmp_dir)
        self.assertFalse(os.path.exists(tmp_dir))
        with self.assertRaises(AssertionError):
            sd = sample_dir.SampleDir(tmp_dir)
        sd = sample_dir.SampleDir(tmp_dir, 'sample_id')
        self.assertTrue(os.path.exists(tmp_dir))
        with open(os.path.join(tmp_dir, 'metadata.json')) as f:
            expected_json = json.load(f)

        self.assertEqual(expected_json, sd.metadata)
        sd.metadata['foo'] = 'bar'
        sd.write_metadata_json()
        expected_json['foo'] = 'bar'
        with open(os.path.join(tmp_dir, 'metadata.json')) as f:
            updated_json = json.load(f)
        self.assertEqual(updated_json, sd.metadata)
        utils.rmtree(tmp_dir)


    def test_ignore_metadata(self):
        '''test ignore_metadata'''
        metadata = {}
        self.assertFalse(sample_dir.SampleDir.ignore_metadata(metadata))
        metadata['instrument_platform'] = 'ILLUMINA'
        self.assertFalse(sample_dir.SampleDir.ignore_metadata(metadata))
        metadata['instrument_platform'] = 'PACBIO_SMRT'
        self.assertTrue(sample_dir.SampleDir.ignore_metadata(metadata))
        metadata['instrument_platform'] = 'OXFORD_NANOPORE'
        self.assertTrue(sample_dir.SampleDir.ignore_metadata(metadata))
        metadata['instrument_platform'] = 'ILLUMINA'
        self.assertFalse(sample_dir.SampleDir.ignore_metadata(metadata))
        metadata['library_source'] = 'GENOMIC'
        self.assertFalse(sample_dir.SampleDir.ignore_metadata(metadata))
        metadata['library_source'] = 'METAGENOMIC'
        self.assertTrue(sample_dir.SampleDir.ignore_metadata(metadata))
        metadata['library_source'] = 'TRANSCRIPTOMIC'
        self.assertTrue(sample_dir.SampleDir.ignore_metadata(metadata))
        

    def test_get_ena_metadata_and_download_reads(self):
        '''test get_ena_metadata_and_download_reads'''
        tmp_dir = 'tmp.sample_dir.get_ena_metadata_and_download_reads'
        utils.rmtree(tmp_dir)
        self.assertFalse(os.path.exists(tmp_dir))
        sd = sample_dir.SampleDir(tmp_dir, 'sample_id')
        fq1_1 = os.path.join(data_dir, 'get_ena_metadata_and_download_reads.1_1.fastq.gz')
        fq1_2 = os.path.join(data_dir, 'get_ena_metadata_and_download_reads.1_2.fastq.gz')
        fq2_1 = os.path.join(data_dir, 'get_ena_metadata_and_download_reads.2_1.fastq.gz')
        fq2_2 = os.path.join(data_dir, 'get_ena_metadata_and_download_reads.2_2.fastq.gz')
        md51_1 = '5c9da3ff0f327bb4274ceafb99c3cb7e'
        md51_2 = 'c49ce7e3c516df226c0076ff700ee61e'
        md52_1 = 'cfcb910a051e95ab4df7d9bed952cd89'
        md52_2 = '2759494b541c7f26627ae21bff58c97b'
        md51 = 'd5724c937aacdf83119f16a2bd91b8a4'
        md52 = '8e3cec37b8f139744486e5653b2f906e'

        ena_metadata = [
                {'sample_accession': 's1', 'secondary_sample_accession': 's2', 'fastq_ftp': 'file1;file2'},
                {'sample_accession': '', 'secondary_sample_accession': 's2', 'fastq_ftp': 'file1;file2'},
                {'sample_accession': 'sample_id', 'secondary_sample_accession': 's2', 'fastq_ftp': f'{fq1_1};{fq1_2}', 'fastq_md5': f'{md51_1};{md51_2}'},
                {'sample_accession': 's3', 'secondary_sample_accession': 'sample_id', 'fastq_ftp': f'{fq2_1};{fq2_2}', 'fastq_md5': f'{md52_1};{md52_2}'},
        ]

        def mock_wget(infile, outfile, known_md5=None):
            shutil.copyfile(infile, outfile)
            got_md5 = utils.md5(outfile)
            assert known_md5 == got_md5

        with mock.patch.object(sample_dir.SampleDir, 'get_ena_metadata', return_value=ena_metadata), mock.patch.object(utils, 'wget', side_effect=mock_wget):
            sd.get_ena_metadata_and_download_reads()

        sd = sample_dir.SampleDir(tmp_dir)
        self.assertTrue(sd.metadata['reads_downloaded'])
        self.assertTrue(os.path.exists(sd.reads_fwd))
        self.assertTrue(os.path.exists(sd.reads_rev))
        self.assertTrue(os.path.exists(sd.reads_downloaded_done_file))
        utils.rmtree(tmp_dir)


    def test_assemble(self):
        '''test assemble'''
        test_dir = 'tmp.sample_dir.assemble'
        utils.rmtree(test_dir)
        sdir = sample_dir.SampleDir(test_dir, sample_id='ABC123')
        with self.assertRaises(Exception):
            sdir.assemble()

        sdir.metadata['reads_downloaded'] = True
        sdir.assemble(testing=True)

        expected_files = [
            'ABC123.contigs.fa.gz',
            'contigs.gfa.gz',
            'shovill.corrections',
            'shovill.log',
            'spades.fasta.gz',
        ]
        for filename in expected_files:
            self.assertTrue(os.path.exists(os.path.join(sdir.assembly_dir, filename)))

        utils.rmtree(test_dir)
