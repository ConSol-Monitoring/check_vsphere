.PHONY: all clean test

all:
	mkdir zip
	find checkvsphere -type f | cpio -vmdup zip
	mv zip/checkvsphere/cli.py zip/__main__.py
	( cd zip && zip -9 ../check_vsphere.zip $$( find . -name \*.py -print ) )
	{ echo '#!/usr/bin/env python3' ; cat check_vsphere.zip ; } > check_vsphere
	chmod a+rx check_vsphere
	rm -rf check_vsphere.zip zip

clean:
	rm -rf check_vsphere zip check_vsphere.zip build check_vsphere.egg-info
