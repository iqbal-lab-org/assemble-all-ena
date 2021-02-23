import csv
import json
import logging
import os
import requests
import shutil
import subprocess

from assemble_all_ena import utils


class SampleDir:
    def __init__(self, directory, sample_id=None):
        self.directory = os.path.abspath(directory)
        self.metadata_json_file = os.path.join(self.directory, 'metadata.json')
        self.assembly_dir = os.path.join(self.directory, 'Assembly')
        self.reads_fwd = os.path.join(self.directory, 'reads_1.fastq.gz')
        self.reads_rev = os.path.join(self.directory, 'reads_2.fastq.gz')
        self.reads_downloaded_done_file = os.path.join(self.directory, 'reads_downloaded_done')

        if os.path.exists(self.metadata_json_file):
            with open(self.metadata_json_file) as f:
                self.metadata = json.load(f)
        else:
            assert sample_id is not None
            self.metadata = {
                'sample_id': sample_id,
                'run_ids': None,
                'ignore': False,
                'reads_downloaded': False,
                'assembled': False,
                'assembly_notes': '',
                'ena_metadata': [],
                'annotated': False,
            }
            self.setup()


    def write_metadata_json(self):
        with open(self.metadata_json_file, 'w') as f:
            json.dump(self.metadata, f, indent=4, sort_keys=True)


    def setup(self):
        if not os.path.exists(self.directory):
            try:
                os.makedirs(self.directory)
            except:
                raise Exception(f'Error mkdir {self.directory}')

        self.write_metadata_json()


    @classmethod
    def get_ena_metadata(cls, sample_id):
        url = 'http://www.ebi.ac.uk/ena/data/warehouse/filereport?'
        data = {'accession': sample_id, 'result': 'read_run', 'download': 'txt'}

        try:
            r = requests.get(url, data)
        except:
            raise Exception('Error querying ENA to get run from sample ' + sample_id)

        if r.status_code != requests.codes.ok:
            raise Exception('Error requesting data. Error code: ' + str(r.status_code) + '\n' + r.url)

        lines = r.text.rstrip().split('\n')
        reader = csv.DictReader(lines, delimiter='\t')
        data = [dict(x) for x in reader]
        return data


    @classmethod
    def ignore_metadata(cls, metadata):
        to_exclude = {
            'instrument_platform': {'PACBIO_SMRT', 'OXFORD_NANOPORE'},
            'library_source': {'METAGENOMIC', 'TRANSCRIPTOMIC'},
        }

        for key, set_to_exclude in to_exclude.items():
            try:
                value = metadata[key]
            except:
                continue
            
            if value in set_to_exclude:
                return True

        return False


    def get_ena_metadata_and_download_reads(self, nextflow_test=False):
        if self.metadata['reads_downloaded']:
            return

        sample_id = self.metadata['sample_id']
        assert sample_id is not None
        if nextflow_test:
            utils.touch(self.reads_fwd)
            utils.touch(self.reads_rev)
            self.metadata['reads_downloaded'] = True
            self.metadata['ena_metadata'] = {'nextflow_test': True}
            self.write_metadata_json()
            utils.touch(self.reads_downloaded_done_file)
            return

        ena_metadata = SampleDir.get_ena_metadata(sample_id)
        ena_metadata = [x for x in ena_metadata if sample_id in [x['sample_accession'], x['secondary_sample_accession']] and x['sample_accession'] != '' and x['secondary_sample_accession'] != '']
        self.metadata['ena_metadata'] = ena_metadata

        ena_metadata = [x for x in ena_metadata if not SampleDir.ignore_metadata(x)]

        if len(ena_metadata) == 0:
            self.metadata['ignore'] = True
            self.write_metadata_json()
            return
        
        fwd_reads = []
        rev_reads = []
        md5sums = {}
        for run in ena_metadata:
            reads = run['fastq_ftp'].split(';')
            md5s = run['fastq_md5'].split(';')

            for read, md5 in zip(reads, md5s):
                if read.endswith('_1.fastq.gz'):
                    fwd_reads.append(read)
                    md5sums[read] = md5
                elif read.endswith('_2.fastq.gz'):
                    rev_reads.append(read)
                    md5sums[read] = md5

        assert len(fwd_reads) == len(rev_reads)
        assert len(md5sums) == len(fwd_reads) + len(rev_reads)
        if len(fwd_reads) == 0:
            self.metadata['ignore'] = True
            self.write_metadata_json()
            return

        outfiles = [self.reads_fwd, self.reads_rev]
        for file_list, final_outfile in zip([fwd_reads, rev_reads], outfiles):
            files_to_cat = []
            for url in file_list:
                basename = os.path.basename(url)
                outfile = os.path.join(self.directory, f'tmp.{basename}')
                utils.wget(url, outfile, known_md5=md5sums[url])
                files_to_cat.append(outfile)
            if len(files_to_cat) > 1:
                command = 'cat ' + ' '.join(files_to_cat) + ' > '  + final_outfile
                subprocess.check_output(command, shell=True)
                for f in files_to_cat:
                    os.unlink(f)
            else:
                os.rename(files_to_cat[0], final_outfile)

        self.metadata['reads_downloaded'] = True
        self.write_metadata_json()
        utils.touch(self.reads_downloaded_done_file)


    def assemble(self, force=False, testing=False, testing_fail=False, temp_dir=None, working_dir=None):
        if not self.metadata['reads_downloaded']:
            raise Exception(f'Cannot assemble {self.sample_id} because reads not downloaded')
        if self.metadata['assembled']:
            if not force:
                raise Exception(f'Sample {self.sample_id} already assembled')
            else:
                utils.rmtree(self.assembly_dir)


        assembly_ok = False
        if working_dir is None:
            shovill_outdir = self.assembly_dir
        else:
            assert os.path.exists(working_dir)
            print('Working_dir:', working_dir)
            shovill_outdir = os.path.join(os.path.abspath(working_dir), 'Shovill.out')

        if testing:
            modules_dir = os.path.dirname(os.path.realpath(__file__))
            data_dir = os.path.join(modules_dir, 'data')
            shutil.copytree(os.path.join(data_dir, 'test_shovill_outdir'), shovill_outdir)
            assembly_ok = True
        elif testing_fail:
            pass
        else:
            command = f'shovill --outdir {shovill_outdir} --R1 {self.reads_fwd} --R2 {self.reads_rev} --cpus 1'
            if temp_dir is not None and len(temp_dir) > 0:
                command += f' --tmpdir {temp_dir}'
            completed_process = subprocess.run(command, shell=True)
            assembly_ok = completed_process.returncode == 0

        if working_dir is not None:
            cmd = f'rsync -a {shovill_outdir}/ {self.assembly_dir}'
            print(cmd)
            subprocess.run(cmd, shell=True, check=True)
            subprocess.run(cmd, shell=True, check=True)
            subprocess.run(f'rm -rf {shovill_outdir}', shell=True, check=True)
            
        if assembly_ok:
            contigs_fa_gz = os.path.join(self.assembly_dir, f'{self.metadata["sample_id"]}.contigs.fa.gz')
            utils.add_prefix_to_seqs(os.path.join(self.assembly_dir, 'contigs.fa'), contigs_fa_gz, self.metadata['sample_id'] + '.')
            os.unlink(os.path.join(self.assembly_dir, 'contigs.fa'))

            to_gzip = ['contigs.gfa', 'spades.fasta']
            for filename in to_gzip:
                utils.gzip(os.path.join(self.assembly_dir, filename))

            self.metadata['assembled'] = True
            self.metadata['reads_downloaded'] = False
            try:
                os.unlink(self.reads_fwd)
                os.unlink(self.reads_rev)
                os.unlink(self.reads_downloaded_done_file)
            except:
                pass
        else:
            self.metadata['ignore'] = True
            self.metadata['assembly_notes'] = 'Shovill fail'

        self.write_metadata_json()

