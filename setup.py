from setuptools import setup

setup(name = 'webMining',
      version = '0.1.0',
      packages = ['webMining'],
      entry_points={
          'console_scripts': [
              'webMining.__main__:main'
              ]
          },
          )
