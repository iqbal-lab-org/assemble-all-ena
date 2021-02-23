from assemble_all_ena import sample_dirs

def run(options):
    sdirs = sample_dirs.SampleDirs(options.output_dir)
    sdirs.add_samples(options.samples_file)

