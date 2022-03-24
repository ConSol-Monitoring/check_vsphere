.PHONY: all clean

all:
	zip -9 check_pyvmomi.zip $$( find . -name \*.py )
	{ echo '#!/usr/bin/env python3' ; cat check_pyvmomi.zip ; } > check_pyvmomi
	chmod a+rx check_pyvmomi
	rm -f check_pyvmomi.zip

clean:
	rm -f check_pyvmomi
