#!/bin/bash
set -ex

### Add custom conda installs here
### Note the install order:
###   - docker base conda
###   - docker base pip
###   - app conda <-- here
###   - base pip
###   - app pip
### Future versions aim to do all conda installs at the beginning


echo "=========================="
echo "="
echo "=  Conda app dependencies"
echo "="
echo "=========================="
echo ""

### Add commands here

#conda install -c conda-forge hdbscan=0.8.26

echo "**** Successfull install of conda app deps ***"