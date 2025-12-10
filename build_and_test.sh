#!/usr/bin/env bash
python3 -m pip install --upgrade pip setuptools wheel cython
python3 setup.py build_ext --inplace
python3 -c "import bitmask_cy; print('built', bitmask_cy)"
