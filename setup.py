# -*- coding:utf-8 -*-

from setuptools import setup, find_packages


setup(name='aplinux.distribution',
      version='1.0.dev1',
      description='APLinux package focusing on the distribution of aplinux in a given environment',
      long_description = open('README.rst').read(),
      classifiers=['Programming Language :: Python'],
      keywords='',
      author='Adam & Paul Pty Ltd',
      author_email='tech@adamandpaul.biz',
      url='https://adamandpaul.biz',
      license='gpl',
      packages=find_packages(),
      namespace_packages=['aplinux'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',

          # Other deps
          'apache-libcloud',
          'paramiko',
          'fabric',
          'retry',
          'scp',

      ],
      entry_points="""
      [console_scripts]
      #aplinux-distribution = aplinux.distribution.main:main
      """,
      )
