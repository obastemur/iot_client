#!/bin/bash

rm -rf build/ dist/ src/iotc/iotc_device.egg-info

TEST=""
if [[ $1 == 'test' ]]; then
  TEST="-r testpypi"
fi

python setup.py sdist bdist_wheel
python3 setup.py sdist bdist_wheel
twine upload dist/* $TEST