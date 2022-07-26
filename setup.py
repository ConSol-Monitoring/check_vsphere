from distutils.core import setup

setup(
    name="check_vsphere",
    version="0.1",
    description="",
    author="Danijel Tasov",
    author_email="m@rbfh.de",
    install_requires = [
        "monplugin @ git+https://github.com/datamuc/py-monplugin@v0.1",
        "pyvmomi",
    ],
    packages = [
        "checkvsphere",
        "checkvsphere.vcmd",
        "checkvsphere.tools",
    ],
    entry_points = {
        "console_scripts": [
            'check_vsphere = checkvsphere.cli:main',
        ]
    }
)
