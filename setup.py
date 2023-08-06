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
    description=('Macro para procesar ficheros de gesfincas (fusionando los datos de varias fincas que vienen en hojas '
                 'separadas en dos hojas, una para ingresos y otra para gastos) y otra macro que crea una ventana con '
                 'la que puntear los datos del banco contra los datos anteriores'),
    entry_points={
            'console_scripts': [
                'liquidaciones=liquidaciones.liquidaciones_gui:main',
                'punteo=liquidaciones.conciliation_gui:main',
            ],
        },
    install_requires=required,
)
