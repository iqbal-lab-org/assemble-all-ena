import json
import logging
import os
import re

from assemble_all_ena import sample_dir

sample_regex = re.compile('^(?P<prefix>[^0-9]+)(?P<numbers>[0-9]+)$')


class SampleDirs:
    def __init__(self, directory):
        self.root_dir = os.path.abspath(directory)
        if not os.path.exists(self.root_dir):
            os.mkdir(self.root_dir)
        self.sample_data_json_file = os.path.join(self.root_dir, 'samples.json')
        if os.path.exists(self.sample_data_json_file):
            with open(self.sample_data_json_file) as f:
                self.sample_data = json.load(f)
        else:
            self.sample_data = {}
            with open(self.sample_data_json_file, 'w') as f:
                json.dump(self.sample_data, f, indent=2)


    @classmethod
    def sample_name_to_directory(cls, sample_id):
        match = sample_regex.search(sample_id)
        if match is None:
            raise Exception(f'No match for regex for sample {sample_id}')

        directories = []
        numbers = match.group('numbers')
        for i in range(0, len(numbers), 2):
            directories.append(numbers[i:i+2])

        return os.path.join(match.group('prefix'), *directories)


    def make_sample_dir(self, sample_id):
        directory = SampleDirs.sample_name_to_directory(sample_id)
        return sample_dir.SampleDir(os.path.join(self.root_dir, directory), sample_id=sample_id)


    @classmethod
    def _tsv_for_nextflow_pipeline(cls, sample_data, root_dir, outfile):
        with open(outfile, 'w') as f:
            print('sample_id', 'directory', sep='\t', file=f)
            for sample, sample_dict in sample_data.items():
                if not sample_dict['asm'] and not sample_dict['ignore']:
                    this_sample_dir = os.path.join(root_dir, SampleDirs.sample_name_to_directory(sample))
                    print(sample, this_sample_dir, sep='\t', file=f)


    def make_nextflow_tsv(self, outfile):
        SampleDirs._tsv_for_nextflow_pipeline(self.sample_data, self.root_dir, outfile)


    def backup_write_sample_data_json(self):
        # Backup existing json file just in case, instead of
        # overwriting existing file
        if os.path.exists(self.sample_data_json_file):
            os.rename(self.sample_data_json_file, f'{self.sample_data_json_file}.bak')
        with open(self.sample_data_json_file, 'w') as f:
            json.dump(self.sample_data, f, indent=2)


    def add_samples(self, file_of_sample_names):
        with open(file_of_sample_names) as f:
            new_samples_list = [x.rstrip() for x in f]

        new_samples = set(new_samples_list)
        if len(new_samples) != len(new_samples_list):
            raise Exception('Duplicated input sample names. Cannot continue')

        dup_samples = set()
        for s in new_samples:
            if s in self.sample_data:
                dup_samples.add(s)

        if len(dup_samples):
            raise Exception('Sample(s) in input are already used. Cannot continue\n' + '\n'.join(sorted(list(dup_samples))))

        for sample_id in new_samples:
            assert sample_id not in self.sample_data
            sd = self.make_sample_dir(sample_id)
            self.sample_data[sample_id] = {'reads': False, 'asm': False, 'annot': False, 'ignore': False}

        self.backup_write_sample_data_json()


    def update_sample_data(self, file_of_sample_names=None):
        logging.info('Running update_sample_data')
        if file_of_sample_names is None:
            sample_names_to_update = self.sample_data.keys()
        else:
            with open(file_of_sample_names) as f:
                sample_names_to_update = [x.rstrip() for x in f]

        for sample_id in sample_names_to_update:
            logging.info(f'Updating sample_id {sample_id}')
            if sample_id not in self.sample_data:
                raise Exception(f'Cannot update sample {sample_id} because not found!')

            sdir = self.make_sample_dir(sample_id)
            self.sample_data[sample_id] = {
                'reads': sdir.metadata['reads_downloaded'],
                'asm': sdir.metadata['assembled'],
                'annot':  sdir.metadata['annotated'],
                'ignore':  sdir.metadata['ignore'],
            }

        logging.info('Backing up and writing new data json file')
        self.backup_write_sample_data_json()
        logging.info('Finished running update_sample_data')
