from enum import Enum
from importlib import resources


def get_data_path(filename: str) -> str:
    """
    Returns full path for a given data filename that is packed with
    Args:
        filename: name of the file (required). It can contain subdirectories

    Returns:
        the full path of the file

    """
    return resources.files("ong_gesfincas.data").joinpath(filename).as_posix()


class DataType(Enum):
    BNK = "banco"
    EXP = "gastos"
    INC = "ingresos"
