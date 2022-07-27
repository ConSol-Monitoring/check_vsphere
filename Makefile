.PHONY: all clean test

all: check_vsphere_bundle check_vsphere

check_vsphere_bundle:
	pip install --no-compile --target allinone .
	mv allinone/bin/check_vsphere allinone/__main__.py
	python -m zipapp  -c -p '/usr/bin/env python3' allinone
	rm -rf allinone
	mv allinone.pyz check_vsphere_bundle

check_vsphere:
	python setup.py build
	mv build/lib/checkvsphere/cli.py build/lib/__main__.py
	( cd build/lib; python -m zipapp -c --output ../../check_vsphere -p '/usr/bin/env python3' . )
	rm -rf build

clean:
	rm -rf build allinone check_vsphere_bundle check_vsphere zip check_vsphere.zip build check_vsphere.egg-info
