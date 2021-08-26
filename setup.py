from distutils.core import setup

setup(
      name='toshiba-ac',
      packages=['toshiba_ac'],
      version='0.1.0',
      license='Apache License 2.0',
      description='Toshiba AC controller - allows to control Toshiba HVAC systems with WiFi',
      author='Kamil Sroka',
      author_email='kamilsroka92@gmail.com',
      url = 'https://github.com/KaSroka/Toshiba-AC-control',

      keywords = ['toshiba', 'ac', 'hvac'],
      install_requires = [
            'azure-iot-device',
            'httpx'
      ],
      classifiers = [
            'Development Status :: 3 - Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License',
            'Operating System :: OS Independent',
            'Programming Language :: Python :: 3.6',
      ],
)
