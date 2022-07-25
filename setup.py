from distutils.core import setup

setup(
    name="check_vsphere",
    version="0.1",
    description="",
    author="Danijel Tasov",
    author_email="m@rbfh.de",
    requires = [
        "monplugin",
    ],
    packages = [
        "checkvsphere",
        "checkvsphere.vcmd",
        "checkvsphere.tools"
    ],
    entry_points = {
        "console_scripts": [
            'check_vsphere = checkvsphere.cli:main',
        ]
    }
)
