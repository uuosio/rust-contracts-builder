
import os
import shutil
import setuptools
# from skbuild import setup
from distutils.core import setup

from distutils.sysconfig import get_python_lib
import glob

# if os.path.exists('pysrc/tinygo'):
#     shutil.rmtree('pysrc/tinygo')
# shutil.copytree('tinygo/build/release/tinygo', 'pysrc/tinygo')

release_files = []
for root, dirs, files in os.walk("pysrc/templates"):
    for f in files:
        release_files.append(os.path.join(root.replace('pysrc/', ''), f))    

# print(release_files)

setup(
    name="rust-contracts-builder",
    version="0.2.1",
    description="Rust Contracts Builder",
    author='The UUOSIO Team',
    license="Apache 2.0",
    url="https://github.com/uuosio/rust-contracts-builder",
    packages=['rust_contracts_builder'],
    package_dir={'rust_contracts_builder': 'pysrc'},
    package_data={
        'rust_contracts_builder': release_files,
    },
    setup_requires=['wheel'],
    install_requires=[
        'toml>=0.10.2'
    ],
)
