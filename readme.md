# Introducción

El objetivo es cuadrar un extracto bancario con los datos contables de gesfincas.

Para eso el programa tiene dos funcionalidades:

- Procesa el fichero de salida de gesfincas en formato excel, con una hoja por finca, en un único libro que tiene una hoja con todos los ingresos y otra con todos los gastos.
- Lee los datos del banco y de la contabilidad y permite cuadrar línea a línea los datos. Para ello crea tablas para el banco, los ingresos y los gastos y crea un número llamado `bucket` que los relaciona entre sí permitiendo unirlos.

Tiene una interfaz hecha con `tkinter`.

## Instalación

En una instalación de python, instalar con pip:

`pip install git+https://github.com/Oneirag/ong_gesfincas.git`

## Uso

### Liquidaciones

Ejecutar el comando `liquidaciones`. Se abre la ventana del programa:

![ventana.png](imgs%2Fventana_liquidaciones.png)

Marcar `Seleccionar y procesar fichero...` y el programa generará un fichero de salida 
en el mismo directorio del fichero seleccionado con el subfijo `_procesado`

### Punteo

Ejecutar el comando `punteo`. Se abre la ventana del programa de punteo:
![ventana_punteo.png](imgs%2Fventana_punteo.png)

#### Cargar datos
Los datos se cargan usando el menú `Archivo`->`cargar datos nuevos`. 
Si se cargan datos nuevos y ya hay datos cargados anteriormente, **se borran todos los punteos que se hubieran hecho**
![punteo_cargar_datos.png](imgs%2Fpunteo_cargar_datos.png)
Hay tres opciones:
- Cargar datos de extracto del banco: Lee un extracto bancario (del banco santander), capturando las columnas Concepto e Importe
- Cargar datos de gesfincas: realiza el mismo proceso que el comando de liquidaciones. Parte de un fichero de gesfincas con datos de una finca en cada hoja y los unifica en ingresos y gastos
- Cargar excel completo: carga un fichero ya procesado por el programa que contiene en un unico excel los datos de banco, ingresos y gastos

