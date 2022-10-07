from setuptools import setup

setup(
   name='parageom',
   version='1.0',
   description='parablade to geomTurbo file interface',
   author='Jean Fesquet',
   author_email='',
   packages=['parageom'],
   install_requires=['numpy','matplotlib','parablade', 'geomdl'],
)