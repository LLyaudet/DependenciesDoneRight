import builtins

old_import = builtins.__import__
last_path = None
versioned_packages = {}
default_dependencies_versions = {}
custom_dependencies_versions = {}
# inspect = None
sys = None
importlib = None
Path = None


def new_import(name, globals=None, locals=None, fromlist=(), level=0):
    # Avoid loops if you're in the interactive interpreter.
    # Use it with bash: export PYTHONSTARTUP=this_script.py
    if name in ("posix", "readline"):
        # This "if" can be removed otherwise.
        return
    if name.startswith("_"):
        return old_import(name, globals, locals, fromlist, level)
    if name in ("importlib","importlib.util","json","sys"):
        # Needed shortcuts
        return old_import(name, globals, locals, fromlist, level)
    if name in (
        "abc",
        "ast",
        "builtins",
        "codecs",
        "collections",
        "collections.abc",
        "contextlib",
        "copyreg",
        "decoder",
        "dis",
        "encoder",
        "enum",
        "errno",
        "fnmatch",
        "functools",
        "genericpath",
        "glob",
        "grp",
        "importlib.machinery",
        # "inspect",
        "io",
        "itertools",
        "keyword",
        "linecache",
        "nt",
        "ntpath",
        "opcode",
        "operator",
        "os",
        "pathlib",
        "posixpath",
        "pwd",
        "re",
        "reprlib",
        "stat",
        "textwrap",
        "token",
        "tokenize",
        "traceback",
        "types",
        "warnings",
        "weakref",
    ):
        # Other shortcuts to decrease prints to analyse for debug.
        # You can comment out this if and it should work.
        return old_import(name, globals, locals, fromlist, level)
    """
    print(f"Importing {name}")
    print(f"with globals {globals}")
    print(f"with locals {locals}")
    print(f"with fromlist {fromlist}")
    """
    sys_modules_name = name
    modules_names = name.split(".")
    root_name = modules_names[0]
    root_sys_name = root_name
    version = None
    if root_name in versioned_packages:
        # print(f"{root_name} in versioned_packages")
        current_package = globals["__package__"]
        current_version = None
        if hasattr(globals["__spec__"], "__version__"):
            current_version = globals["__spec__"].__version__
            if current_package == root_name:
                version = current_version
        if version is None:
            if current_version is None:
                origin = f"{current_package}"
            else:
                origin = f"{current_package}/{current_version}"
            versions = custom_dependencies_versions.get(origin,{})
            version = versions.get(root_name)
            if version is None:
                versions = default_dependencies_versions.get(
                    origin,{}
                )
                version = versions.get(root_name)
        """
        frame2 = inspect.currentframe()
        print(frame2.f_globals['__name__'])
        print(frame2.f_globals['__package__'])
        frame1 = frame2.f_back
        print(frame1.f_globals['__name__'])
        print(frame1.f_globals['__package__'])
        # frame0 = frame1.f_back
        # print(frame0.f_globals['__name__'])
        # print(frame0.f_globals['__package__'])
        """
        if version is None:
            version = versioned_packages[root_name]
            # print(f"default version = {version}")
        root_sys_name = f"{root_name}/{version}"
        modules_names[0] = root_sys_name
        sys_modules_name = ".".join(modules_names)
    if sys_modules_name in sys.modules:
        return sys.modules[sys_modules_name]
    if name == sys_modules_name:
        return old_import(name, globals, locals, fromlist, level)
    """
    print(f"Importing {name}")
    print(f"with globals {globals}")
    print(f"with locals {locals}")
    print(f"with fromlist {fromlist}")
    """
    file_path = f"{last_path}/{root_sys_name}/__init__.py"
    if root_sys_name not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            root_name, file_path
        )
        spec.__version__ = version
        module = importlib.util.module_from_spec(spec)
        sys.modules[root_sys_name] = module
        spec.loader.exec_module(module)
    root_module = sys.modules[root_sys_name]

    parent_name = root_name
    parent_sys_name = root_sys_name
    parent_module = root_module
    module = None
    for i in range(1, len(modules_names)):
        child_name = modules_names[i]
        current_name = f"{parent_name}.{child_name}"
        current_sys_name = f"{parent_sys_name}.{child_name}"
        if current_sys_name in sys.modules:
            module = sys.modules[current_sys_name]
            parent_name = current_name
            parent_sys_name = current_sys_name
            parent_module = module
            continue
        submodule_search_locations = (
            parent_module.__spec__.submodule_search_locations
        )
        """
        Doesn't work:
        spec = importlib.util.spec_from_file_location(
            current_name,
            file_path,
            submodule_search_locations=submodule_search_locations,
        )
        """
        # print(submodule_search_locations)
        spec = None
        for location in submodule_search_locations:
            file_path1 = Path(f"{location}/{child_name}/__init__.py")
            file_path2 = Path(f"{location}/{child_name}.py")
            if file_path1.is_file():
                spec = importlib.util.spec_from_file_location(
                    current_name, file_path1
                )
                break
            elif file_path2.is_file():
                spec = importlib.util.spec_from_file_location(
                    current_name, file_path2
                )
                break
        if spec is None:
            msg = f'No module named {current_name!r}2'
            raise ModuleNotFoundError(msg, name=current_name)
        spec.__version__ = version
        module = importlib.util.module_from_spec(spec)
        sys.modules[current_sys_name] = module
        setattr(parent_module, child_name, module)
        # print(module)
        spec.loader.exec_module(module)
        parent_name = current_name
        parent_sys_name = current_sys_name
        parent_module = module
    if fromlist:
        output_module = module
    else:
        output_module = root_module
    return output_module


builtins.__import__ = new_import

import sys
import importlib.util
# import inspect
import json
from pathlib import Path
# This part should be improved, but remember it is just a POC.
# POC: no customisation on a path element basis
# We take the venv path:
last_path = sys.path[-1]
try:
    with open(f"{last_path}/versioned_packages.json", 'r') as file:
        versioned_packages = json.load(file)
except FileNotFoundError:
    print(f"No {last_path}/versioned_packages.json")
try:
    with open(
        f"{last_path}/default_dependencies_versions.json", 'r'
    ) as file:
        default_dependencies_versions = json.load(file)
except FileNotFoundError:
    print(f"No {last_path}/default_dependencies_versions.json")
try:
    with open(
        f"{last_path}/custom_dependencies_versions.json", 'r'
    ) as file:
        custom_dependencies_versions = json.load(file)
except FileNotFoundError:
    print(f"No {last_path}/custom_dependencies_versions.json")
print(versioned_packages)
print(default_dependencies_versions)
print(custom_dependencies_versions)

import d_d_r_unversioned_A
# import d_d_r_versioned_A

d_d_r_unversioned_A.wat()
# d_d_r_versioned_A.wat()
