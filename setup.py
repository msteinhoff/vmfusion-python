from setuptools import setup

setup(
    name='vmfusion',
    version='0.2.0',
    author='Mario Steinhoff',
    author_email='steinhoff.mario@gmail.com',
    packages=['vmfusion'],
    url='https://github.com/msteinhoff/vmfusion-python',
    license='LICENSE.txt',
    description='A python API for the VMware Fusion CLI tools.',
    long_description=open('README.md').read(),
    install_requires=[
        "pyparsing >= 2.0.1"
    ]
)
