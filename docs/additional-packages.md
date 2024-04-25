# Adding Custom Python Packages to graph-app-kit

## Install Custom Python Packages Locally

Install the desired custom Python packages on your localhost.  For example, if you want to include a different version of `PyGraphistry` and an additional dependency like `faker`, run the following commands in your terminal:

```bash
pip install pip install graphistry[all]
pip install faker
```

Graph-app-kit dependency errors on `pip install` are normal and can be safely ignored.

If the environment is airgapped, copy the packages into the path `./data/py_envs/gak` from the root directory of the Graphistry install.  Ensure that you use the same system architecture and Python version.
