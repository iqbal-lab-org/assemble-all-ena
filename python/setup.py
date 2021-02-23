import glob
from setuptools import setup, find_packages


setup(
    name='assemble_all_ena',
    version='0.0.1',
    description='Assemble all samples in ENA',
    packages = find_packages(),
    package_data={'assemble_all_ena': ['data/*']},
    author='Martin Hunt;Grace Blackwell',
    author_email='mhunt@ebi.ac.uk',
    #url='https://github.com/iqbal-lab-org/tb-amr-benchmarking',
    scripts=glob.glob('scripts/*'),
    test_suite='nose.collector',
    tests_require=['nose >= 1.3'],
    install_requires=[
        'requests', 
        'pyfastaq',
    ],
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Scientific/Engineering :: Bio-Informatics',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
    ],
)

