from distutils.core import setup

setup(
    name="check_vsphere",
    version="0.1",
    description="",
    author="Danijel Tasov",
    author_email="m@rbfh.de",
    install_requires = [
        "monplugin @ https://github.com/datamuc/py-monplugin/archive/refs/tags/v0.1.zip",
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
    },
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
    ],
)
