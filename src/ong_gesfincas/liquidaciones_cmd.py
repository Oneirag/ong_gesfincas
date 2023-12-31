import os

import pandas as pd


def process_df(df, start_idx, end_idx, finca):
    df_res = df.iloc[slice(start_idx, end_idx), :].dropna(axis=1, how="all").dropna(axis=0, how="all")
    if df_res.shape[0] < 2:
        return None, None
    res = df_res.iloc[2:-1, :]
    res.columns = df_res.iloc[1, :]
    tipo = df_res.iloc[0, 0].strip()
    res = res.assign(finca=finca)
    return res, tipo


def read_gesfincas(gesfincas_file: str) -> tuple:
    """
    Process a gesfincas file and returns a tuple with two dataframes: one for expenses and other for incomes
    Args:
        gesfincas_file: full name of the gesfincas file

    Returns:
        a tuple with df_expenses, df_incomes
    """
    incomes = []
    expenses = []
    xls = pd.ExcelFile(gesfincas_file)
    for sheet_name in xls.sheet_names[:-1]:     # Last one is just a summary
        # print(sheet_name)
        df = pd.read_excel(xls, sheet_name=sheet_name, skiprows=7, header=None)
        finca = df.iat[0, 0]
        try:
            empty_row = df[df.isna().all(axis=1)].index[0]
        except IndexError:
            # No empty row found, only ingresos or pagos here, not both
            pass
            empty_row = df.index[-1] + 1

        finca = finca[7:].strip()

        df1, tipo1 = process_df(df, 1, empty_row, finca)
        df2, tipo2 = process_df(df, empty_row + 1, None, finca)
        for df, tipo in (df1, tipo1), (df2, tipo2):
            if tipo:
                if tipo == "DETALLE DE INGRESOS (COBRO)":
                    # If there are consecutive rows, fill them backwards
                    incomes.append(df)
                    if df.iloc[1:, :2].isna().any().any():
                        # Backfill cases where there are many nan values
                        for row in range(1, df.shape[0]):
                            if df.iloc[row, :2].isna().all():
                                df.iloc[row, :2] = df.iloc[row - 1, :2]
                            elif df.iloc[row, :2].isna().any():
                                # print(df.iloc[row-1: row+1, :2])
                                pass    # Do nothing: at least there is a non na value
                elif tipo == "DETALLE DE GASTOS (PAGOS)":
                    expenses.append(df)
    if not expenses or not incomes:
        return None, None
    df_expenses = pd.concat(expenses, ignore_index=True)
    df_incomes = pd.concat(incomes, ignore_index=True)
    return df_expenses, df_incomes


def main(in_file: str, out_file:str):
    """
    Processes a gesfincas settlement file to merge into a single file
    :param in_file: name (or full path) of the file (xlsx)
    :param out_file: name (or full path) of the output file (xlsx)
    :return:
    """
    df_gastos, df_ingresos = read_gesfincas(in_file)
    out_xls = pd.ExcelWriter(out_file)
    df_gastos.to_excel(out_xls, sheet_name="gastos", index=False)
    df_ingresos.to_excel(out_xls, sheet_name="ingresos", index=False)
    out_xls.close()


if __name__ == '__main__':

    in_file = "VERSION CASI LIQUIDACIONES.xlsx"
    out_file = "salida.xlsx"
    in_file = input(f"Elija el fichero de entrada [{in_file}]: ") or in_file
    out_file = input(f"Elija el fichero de salida [{out_file}]: ") or out_file
    if not os.path.isfile(in_file):
        raise FileNotFoundError(f"El fichero de entrada {in_file} no existe. Pruebe a indicar el path completo")
    main(in_file, out_file)

