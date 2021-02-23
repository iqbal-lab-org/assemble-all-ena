from assemble_all_ena import sample_dirs

def run(options):
    sdirs = sample_dirs.SampleDirs(options.samples_dir)
    sdirs.make_nextflow_tsv(options.outfile)

