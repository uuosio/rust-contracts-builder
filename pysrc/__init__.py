import os
import sys
import subprocess
import shlex
import platform
import tempfile
import toml
import shutil
import argparse

__version__ = "0.1.5"

src_dir = os.path.dirname(__file__)
cur_dir = os.path.abspath(os.curdir)


#https://stackabuse.com/how-to-print-colored-text-in-python/
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[1;30;43m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

def find_target_dir(lib_name):
    parent_dir = os.path.dirname(cur_dir)
    base_name = os.path.basename(cur_dir)
    parent_toml_file = os.path.join(parent_dir, 'Cargo.toml')
    if not os.path.exists(parent_toml_file):
        return os.path.join(cur_dir, 'target')
    with open(parent_toml_file, 'r') as f:
        cargo_toml = toml.loads(f.read())
        if 'workspace' in cargo_toml:
            if 'members' in cargo_toml['workspace']:
                members = cargo_toml['workspace']['members']
                for member in members:
                    if base_name == member:
                        return os.path.join(parent_dir, 'target', lib_name)
    return os.path.join(cur_dir, 'target')

def run_builder():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subparser')

    init = subparsers.add_parser('init')
    init.add_argument('project_name')

    build = subparsers.add_parser('build')
    build.add_argument(
        '-d', '--debug', action='store_true', help='set to true to enable debug build')
    build.add_argument(
        '-s', '--stack-size', default=8192, help='configure stack size')

    result = parser.parse_args()
    if not result:
        parser.print_usage()
        sys.exit(-1)

    if result.subparser == "init":
        project_name = result.project_name
        with open(f'{src_dir}/templates/init/_Cargo.toml', 'r') as f:
            cargo_toml = f.read().replace('{{name}}', project_name)

        files = {}
        for file_name in ['_Cargo.toml', '.gitignore', 'build.sh', 'lib.rs', 'test.py', 'test.sh']:
            with open(f'{src_dir}/templates/init/{file_name}', 'r') as f:
                if file_name == '_Cargo.toml':
                    file_name = 'Cargo.toml'
                files[file_name] = f.read().replace('{{name}}', project_name)
        os.mkdir(project_name)
        for file in files:
            with open(f'{project_name}/{file}', 'w') as f:
                f.write(files[file])
    elif result.subparser == "build":
        if result.debug:
            build_mode = ''
        else:
            build_mode = '--release'
        if not os.path.exists('Cargo.toml'):
            print(f'{FAIL}: Cargo.toml not found in current directory!')
            sys.exit(-1)

        with open('Cargo.toml', 'r') as f:
            project = toml.loads(f.read())
            if not 'package' in project:
                print(f'{FAIL} package section not found in Cargo.toml file!')
                sys.exit(-1)
            package_name = project['package']['name']
            if not 'lib' in project:
                print(f'{FAIL} not lib section found in Cargo.toml file!')
                sys.exit(-1)
            lib_name = project['lib']['name']
        target_dir = find_target_dir(lib_name)
        os.environ['RUSTFLAGS'] = f'-C link-arg=-zstack-size={result.stack_size} -Clinker-plugin-lto'
        cmd = f'cargo +nightly build --target=wasm32-wasi --target-dir={target_dir} -Zbuild-std --no-default-features {build_mode} -Zbuild-std-features=panic_immediate_abort'
        cmd = shlex.split(cmd)
        subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)

        if shutil.which('wasm-opt'):
            cmd = f'wasm-opt {target_dir}/wasm32-wasi/release/{lib_name}.wasm -Oz -o {target_dir}/{lib_name}.wasm'
            cmd = shlex.split(cmd)
            subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        else:
            shutil.copy(f'{target_dir}/wasm32-wasi/release/{lib_name}.wasm', f'{target_dir}/{lib_name}.wasm')
            print(f'''{WARNING}
wasm-opt not found! Make sure the binary is in your PATH environment.
We use this tool to optimize the size of your contract's Wasm binary.
wasm-opt is part of the binaryen package. You can find detailed
installation instructions on https://github.com/WebAssembly/binaryen#tools.
There are ready-to-install packages for many platforms:
* Debian/Ubuntu: apt-get install binaryen
* Homebrew: brew install binaryen
* Arch Linux: pacman -S binaryen
* Windows: binary releases at https://github.com/WebAssembly/binaryen/releases''')

        try:
            temp_dir = tempfile.mkdtemp()
            with open(f'{src_dir}/templates/abigen/Cargo.toml', 'r') as f:
                cargo_toml = f.read()
                path_name = os.path.abspath(os.curdir)
                cargo_toml = cargo_toml.format(package_name=package_name, path_name=path_name)
                with open(f'{temp_dir}/Cargo.toml', 'w') as f:
                    f.write(cargo_toml)

            with open(f'{src_dir}/templates/abigen/main.rs', 'r') as f:
                main_rs = f.read()
                main_rs = main_rs.format(lib_name=lib_name, target=f'{target_dir}')
                with open(f'{temp_dir}/main.rs', 'w') as f:
                    f.write(main_rs)

            del os.environ['RUSTFLAGS']
            cmd = f'cargo run --package abi-gen --manifest-path={temp_dir}/Cargo.toml --target-dir={target_dir} --release'
            cmd = shlex.split(cmd)
            subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stderr)
        finally:
            shutil.rmtree(temp_dir)
    else:
        parser.print_usage()

if __name__ == '__main__':
    run_builder()
