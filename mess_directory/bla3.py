import builtins

old_import = builtins.__import__

def new_import(name, *args, **kwargs):
    # Avoid loops if you're in the interactive interpreter.
    # Use it with bash: export PYTHONSTARTUP=this_script.py
    if name in ("posix", "readline"):
        return
    print(f"Importing {name}")
    return old_import(name, *args, **kwargs)

builtins.__import__ = new_import

import json

