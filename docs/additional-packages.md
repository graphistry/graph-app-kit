# Adding Custom Python Packages to graph-app-kit

## Install Custom Python Packages Locally

Install the desired custom Python packages on your localhost.  For example, if you want to include a different version of `PyGraphistry` and an additional dependency like `faker`, run the following commands in your terminal:

```bash
mamba create --yes -n myenv python=3.8
pip install pip install graphistry[all] -t /home/user/additional-python-packages
pip install faker -t /home/user/additional-python-packages
```

If the environment is airgapped, copy the packages into the folder `/home/user/additional-python-packages`.  Ensure that you use the same system architecture and Python version.

## Mount the Volume in Docker Compose

Update your Docker Compose file to mount the volume to the GAK container.  Specify the path to your local directory and the desired mount point inside the container in the environment variable `ADDITIONAL_PYTHON_PATH` (`/mnt` in this example):

```yaml
services:
  streamlit:
    ...
    volumes:
      ...
      - /home/user/additional-python-packages:/mnt:ro
    environment:
        ADDITIONAL_PYTHON_PATH: "/mnt"
    ...
```

That's it! You've successfully added custom Python packages to the graph-app-kit container.  You can now use these packages in your GAK environment for graph analytics and visualizations.
