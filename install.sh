pip uninstall -y tilemap

python setup.py sdist bdist_wheel
pip install --force-reinstall  ./dist/tilemap-1.1.0-py3-none-any.whl

rm -r ./build ./dist ./tilemap.egg-info