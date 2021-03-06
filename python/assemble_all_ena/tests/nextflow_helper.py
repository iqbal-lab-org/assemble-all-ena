import shutil
import sys
import os

import assemble_all_ena



config_file = 'tmp.nextflow.config'


def clean_files():
    for filename in ['.nextflow.log', config_file]:
        try:
            os.unlink(filename)
        except:
            pass

    for directory in ['.nextflow']:
        try:
            shutil.rmtree(directory)
        except:
            pass

clean_files()


assemble_all_ena_python_modules_dir = os.path.dirname(os.path.abspath(assemble_all_ena.__file__))
assemble_all_ena_python_root = os.path.abspath(os.path.join(assemble_all_ena_python_modules_dir, os.pardir))
assemble_all_ena_repo_root = os.path.abspath(os.path.join(assemble_all_ena_python_root, os.pardir))
assemble_all_ena_scripts_dir = os.path.join(assemble_all_ena_python_root, 'scripts')
nextflow_dir = os.path.join(assemble_all_ena_repo_root, 'nextflow')
sys.path.append(assemble_all_ena_python_root)
data_root_dir = os.path.join(assemble_all_ena_python_modules_dir, 'tests', 'data')
os.environ['PATH'] = os.path.join(assemble_all_ena_scripts_dir) + ':' + os.environ['PATH']
if 'PYTHONPATH' in os.environ:
    os.environ['PYTHONPATH'] = assemble_all_ena_python_root + ':' + os.environ['PYTHONPATH']
else:
    os.environ['PYTHONPATH'] = assemble_all_ena_python_root



def write_config_file():
    with open(config_file, 'w') as f:
        print('env.PYTHONPATH = "', assemble_all_ena_python_root, ':$PYTHONPATH"', sep='', file=f)
        print('env.PATH = "', os.path.join(assemble_all_ena_scripts_dir), ':$PATH"', sep='', file=f)
