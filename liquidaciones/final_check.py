import pandas as pd

test_filename = "/Users/oneirag/Library/CloudStorage/OneDrive-Bibliotecascompartidas:onedrive/Documents/Evi/20230711_Punteo/BORRADOR LIQUIDACIONES JU_procesado.xlsx"



def process_file(filename: str):
    excel = pd.ExcelFile(test_filename)
    df_gastos = pd.read_excel(excel, "gastos")
    df_banco = pd.read_excel(excel, "banco")
    df_ingresos = pd.read_excel(excel, "ingresos")

    df_res = df_banco.merge(df_gastos, left_on="id", right_on="id", how="outer", suffixes=("_banco", "_gastos"))
    # df_res = df_res.merge(df_ingresos, left_on="id", right_on="id", how="outer", suffixes=("_banco", "_ingresos"))

    key_columns = ("Concepto", "Importe"), ("CONCEPTO", "Pagos"), #("Piso/Local", "Cobrado"
    # for idx, group in df_res.groupby("id"):
    #     for i in range(1, group.shape[0]):
    #         for config_duplicated in key_columns:
    #             if (group.at[group.index[0], config_duplicated[0]] == group.at[group.index[i], config_duplicated[0]]
    #                     and group.at[group.index[0], config_duplicated[1]] == group.at[group.index[i], config_duplicated[1]]):
    #                 group.at[group.index[i], config_duplicated[1]] = 0

    with pd.ExcelWriter(filename,mode='a', if_sheet_exists="replace") as writer:
        df_res.to_excel(writer, sheet_name='salida')
    return df_res


if __name__ == '__main__':
    process_file(test_filename)
    print("done!")
