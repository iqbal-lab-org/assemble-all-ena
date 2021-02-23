from assemble_all_ena import sample_dirs

def run(options):
    dirs = sample_dirs.SampleDirs(options.sample_dir)
    dirs.update_sample_data()
