from setuptools import setup

setup(
    name='nteu_gateway',
    version='0.1',
    description='NTEU gateway',
    url='https://github.com/Pangeamt/nteu_gateway',
    author='PangeaMT',
    author_email='a.cerda@pangeanic.es',
    license='MIT',
    packages=['nteu_gateway', 'nteu_gateway.segmenter', 'nteu_gateway.utils'],
    zip_safe=False
)
