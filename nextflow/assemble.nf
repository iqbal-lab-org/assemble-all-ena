params.help = false
params.input_dir = ""
params.max_forks_ena_download = 10
params.testing = false
params.shovill_tempdir = ""


if (params.help){
    log.info"""
        Add help message
        Required options:
            --input_dir input samples dir
        Other options:
            --max_forks_ena_download
                max number of downloads in parallel from ENA
            --shovill_tempdir
                absolute path to temp dir used by
                shovill (using its --tempdir option)
    """.stripIndent()

    exit 0
}



if (params.testing) {
    testing_string = "--testing"
    python_test_string = "True"
}
else {
    testing_string = ""
    python_test_string = "False"
}

input_dir = file(params.input_dir).toAbsolutePath()

if (!input_dir.exists()){
    exit 1, "Input dir file not found: ${params.input_dir} -- aborting"
}



process make_jobs_tsv {
    memory '2 GB'

    output:
    file jobs_tsv into jobs_tsv_channel

    """
    assemble_all_ena make_nextflow_tsv ${input_dir} jobs_tsv
    """
}






jobs_tsv_channel.splitCsv(header:true, sep:'\t').set{tsv_lines}


process download_from_ena {
    maxForks params.max_forks_ena_download
    memory '0.5 GB'
    errorStrategy {task.attempt < 2 ? 'retry' : 'ignore'}
    maxRetries 2
    time "3h"

    input:
    val fields from tsv_lines


    output:
    val fields into assemble_input

    """
    #!/usr/bin/env python3
    from assemble_all_ena import sample_dir, utils
    sdir = sample_dir.SampleDir('${fields.directory}')
    sdir.get_ena_metadata_and_download_reads(nextflow_test=${python_test_string}, use_fire=${use_fire_string})
    """
}


process assemble {
    memory {params.testing ? '100 MB' : '33 GB'}
    errorStrategy {task.attempt < 1 ? 'retry' : 'ignore'}
    maxRetries 1
    time "24h"

    input:
    val fields from assemble_input

    output:
    val(42) into update_main_json_channel


    """
    #!/usr/bin/env python3
    import os
    cwd = os.getcwd()
    from assemble_all_ena import sample_dir, utils
    sdir = sample_dir.SampleDir('${fields.directory}')
    sdir.assemble(testing=${python_test_string}, temp_dir='${params.shovill_tempdir}', working_dir=cwd)
    utils.touch('assembly_done')
    """
}


process update_main_json {
    memory {params.testing ? '100 MB' : '5 GB'}

    input:
    val(foo) from update_main_json_channel.collect()

    output:
    file update_done

    """
    #!/usr/bin/env python3
    from assemble_all_ena import sample_dirs, utils
    dirs = sample_dirs.SampleDirs('${input_dir}')
    dirs.update_sample_data()
    utils.touch('update_done')
    """
}

