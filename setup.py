from setuptools import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='ong_gesfincas',
    version='0.0.1',
    packages=['liquidaciones'],
    url='www.neirapinuela.es',
    license='',
    author='Oscar Neira',
    author_email='oneirag@yahoo.es',
    description='Macro simple que fusiona en dos tablas (una para ingresos y otra para gastos) todas las liquidaciones de varias fincas de gesfincas',
    scripts=['liquidaciones/liquidaciones'],
    install_requires=required,
)
