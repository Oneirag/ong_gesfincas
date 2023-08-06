import os
from tkinter import *
from tkinter import messagebox, filedialog

import numpy as np
import pandas as pd
from pandastable import TableModel

from liquidaciones import DataType
from liquidaciones.conciliation_model import Conciliation
from liquidaciones.conciliation_pandastable import ConciliationTable
from liquidaciones.liquidaciones_cmd import read_gesfincas


def ask_excel_filename(**kwargs):
    """Calls filedialog.askopenfilename for Excel files. Accepts kwargs to pass to askopenfilename"""
    file_path = filedialog.askopenfilename(defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")], **kwargs)
    return file_path


def check_missing_data(f):
    """Decorator that checks if all data is available (bank, incomes and expenses) before executing a command.
    If any is missing gives an informative message and cancels execution"""

    def wrapper(*args):
        self = args[0]
        if self.conciliation.has_all_data:
            return f(*args)
        else:
            messagebox.showinfo(message="Faltan datos para ejecutar la acción")

    return wrapper


class ConciliationApp(Frame):
    """Main window for conciliation of bank, expenses and income data"""

    # Values for self.var_show
    _show_all = ""
    _show_assigned = "asignados"
    _show_unassigned = "no asignados"
    # Color of the rows of the bucketed values
    _color_bucketed = "lightgreen"

    def __init__(self, filename, parent=None):
        self.conciliation = Conciliation(filename)
        # self.conciliation.automatic_bucket_expenses()
        self.parent = parent
        Frame.__init__(self)

        self.main = self.master
        # self.main.geometry('1000x800+200+100')
        self.main.state('zoomed')  # Maximizes window

        # self.main.title('Table app')
        self.main.title('Punteo de banco y datos de gesfincas')

        fr_btn = Frame(self.main)
        fr_btn.pack(fill=X, expand=1)
        b = 0  # Column in the grid
        ###################
        # Radiobuttons to filter by a certain data table
        ###################
        self.lbl_show = Label(fr_btn, text="Mostrar:")
        self.lbl_show.grid(row=0, column=b)
        self.var_show = StringVar(value="")
        self.radbtn_show = []
        for text, data_type in [("Todos", self._show_all), ("Asignados", self._show_assigned),
                                ("No asignados", self._show_unassigned), ]:
            b += 1
            radio_button_show = Radiobutton(fr_btn, variable=self.var_show, text=text,
                                            command=self.handle_filter_unassigned, value=data_type,
                                            tristatevalue="other")
            self.radbtn_show.append(radio_button_show)
            radio_button_show.grid(row=0, column=b)

        ###################
        # Radiobuttons to show all, bucketed or unbucketed
        ###################
        b += 1
        self.lbl_filter = Label(fr_btn, text="Filtrar por:")
        self.lbl_filter.grid(row=0, column=b)
        self.var_filter_by = StringVar(value="")
        self.radbtn_filter_by = []
        for text, data_type in [("Ninguno", ""), ("Banco", DataType.BNK.name), ("Gastos", DataType.EXP.name),
                                ("Ingresos", DataType.INC.name)]:
            b += 1
            radio_button_filter_by = Radiobutton(fr_btn, variable=self.var_filter_by, text=text,
                                                 command=self.handle_filter_by, value=data_type,
                                                 tristatevalue="other")
            self.radbtn_filter_by.append(radio_button_filter_by)
            radio_button_filter_by.grid(row=0, column=b)
        #########################################################
        # Buttons to assign bank vs incomes or bank vs expenses
        #########################################################
        b += 1
        self.chk_bnk_exp = Button(fr_btn, text="Asignar Gastos y Banco", command=self.handle_bucket_bnk_exp)
        self.chk_bnk_exp.grid(row=0, column=b)
        b += 1
        self.chk_bnk_exp = Button(fr_btn, text="Asignar Ingresos y Banco", command=self.handle_bucket_bnk_inc)
        self.chk_bnk_exp.grid(row=0, column=b)
        b += 1
        ###################################
        # Button to delete selected match
        ###################################
        self.chk_bnk_exp = Button(fr_btn, text="Borrar asignacion banco", command=self.handle_del_bucket_bnk)
        self.chk_bnk_exp.grid(row=0, column=b)
        ###################################
        # Label for current match summary
        ###################################
        self.lbl_summary = Label(fr_btn, text="<summary>", )
        self.lbl_summary.grid(row=1, columnspan=b, sticky="W")
        ###################################
        # Tables (bank, expenses, incomes)
        ###################################
        self.tables = {k: None for k in DataType}
        self.table_frames = {k: None for k in DataType}
        self.create_tables()

        self.summary_refresh()
        self.redraw_all_tables()
        self.create_menu()
        return

    def create_tables(self):
        """Creates tables (or deletes them if found)"""
        # First step: delete all frames
        for k, f in self.table_frames.items():
            if not f is None:
                for s in f.grid_slaves():
                    s.destroy()
                self.tables[k] = None
                f.destroy()
                self.table_frames[k] = None

        # Second step: create Tables
        for row, data_type in enumerate(DataType):
            self.table_frames[data_type] = f = Frame(self.main)
            f.pack(fill=X, expand=1)
            if (df := self.conciliation.dfs.get(data_type, None)) is not None:
                table = ConciliationTable(f, dataframe=df, showstatusbar=True)
                table.editable = False
                table.show()
                table.clearFormatting()
                table.autoResizeColumns()
                self.tables[data_type] = table
            else:
                lbl = Label(f, text=f"Por favor, cargue datos de {data_type.value} para mostrar los valores")
                lbl.pack()

    def create_menu(self):
        main_menu = Menu(self)
        self.main.config(menu=main_menu)

        file_menu = Menu(main_menu, tearoff=False)
        main_menu.add_cascade(label="Archivo", menu=file_menu)

        load_menu = Menu(file_menu, tearoff=False)
        file_menu.add_cascade(label="Cargar datos nuevos", menu=load_menu)
        load_menu.add_command(label="Fichero de gesfincas", command=lambda: self.handle_gesfincas(update=False))
        load_menu.add_command(label="Extracto del banco", command=lambda: self.handle_bank_data(update=False))
        load_menu.add_command(label="Excel completo", command=lambda: self.handle_read_excel(update=False))
        file_menu.add_separator()

        update_menu = Menu(file_menu, tearoff=False)
        file_menu.add_cascade(label="Actualizar con datos nuevos", menu=load_menu)
        update_menu.add_command(label="Fichero de gesfincas", command=lambda: self.handle_gesfincas(update=True))
        update_menu.add_command(label="Extracto del banco", command=lambda: self.handle_bank_data(update=True))
        update_menu.add_command(label="Excel completo", command=lambda: self.handle_read_excel(update=True))
        file_menu.add_separator()

        file_menu.add_command(label="Guardar Excel completo", command=self.handle_save_to_excel)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.exit_application)

        # bucket_menu = MenuTooltip(main_menu)
        bucket_menu = Menu(main_menu, tearoff=False)

        bucket_menu.add_command(label="Conciliar automáticamente", command=self.handle_auto_conciliation,
                                # tooltip="\tIntenta puntea automáticamente los datos que no estén ya punteados"
                                )

        bucket_menu.add_command(label="Borrar punteos huérfanos", command=self.handle_remove_orphan,
                                # tooltip="\tElimina los punteos que no están en más de una tabla"
                                )
        main_menu.add_cascade(label="Conciliar", menu=bucket_menu)

        # view_menu = Menu(main_menu, tearoff=False)
        # view_menu.add_command(label="Redibujar las tablas", command=self.redraw_all_tables)
        # main_menu.add_cascade(label="Vista (pruebas)", menu=view_menu)

    def load_or_update(self, df_dict: dict, update: bool):
        """
        Loads or updates a dict of dataframes indexed by DataType. Checks for previous data
        Args:
            df_dict: a dict of dataframes indexed by DataType
            update: True if data is meant to be updated, False if data should be overwritten

        Returns:
            None
        """
        # Reset index
        for df in df_dict.values():
            df.index = range(df.shape[0])
        # Check if there was previous data
        previous_data = any(self.conciliation.dfs.get(key) is not None for key in df_dict.keys())
        previous_data_str = ", ".join(k.value for k in df_dict.keys())

        if update:
            if previous_data:
                self.conciliation.update_dfs(df_dict)
            else:
                messagebox.showinfo(message=f"No hay datos de {previous_data_str}, se cargarán nuevos sin actualizar")
            self.conciliation.set_dfs(df_dict, read_buckets=False)
        else:
            if previous_data:
                if not messagebox.askyesno(message=f"Hay cargados datos de {previous_data_str}. "
                                                   f"¿Desea sobreescribirlos y perder el punteo previo?"):
                    print("salir sin hacer nada")
                    return
            self.conciliation.set_dfs(df_dict, read_buckets=False)
        self.create_tables()
        self.redraw_all_tables()

    def handle_bank_data(self, update=False):
        bank_file = ask_excel_filename()
        if bank_file:
            df_bank = self.conciliation.read_bank(bank_file)
            if df_bank is None:
                messagebox.showerror(message="El fichero seleccionado no tiene datos del banco en su primera hoja")
            else:
                df_dict = {DataType.BNK: df_bank}
                self.load_or_update(df_dict, update)
        pass

    def handle_gesfincas(self, update=False):
        gesfincas_file = ask_excel_filename()
        if gesfincas_file:
            df_expenses, df_incomes = read_gesfincas(gesfincas_file)
            if df_expenses is None or df_incomes is None:
                messagebox.showerror(message="El fichero seleccionado no tiene datos de gesfincas")
                return
            # Now set both df to current conciliation
            dict_df = {DataType.INC: df_incomes, DataType.EXP: df_expenses}
            self.load_or_update(dict_df, update)

    @check_missing_data
    def handle_remove_orphan(self):
        self.conciliation.clear_orphan_buckets()
        self.redraw_all_tables()
        self.summary_refresh()

    @check_missing_data
    def handle_auto_conciliation(self):
        old_conciliation = {key: df[~df[self.conciliation.col_bucket].isna()].shape[0]
                            for key, df in self.conciliation.dfs.items()}
        self.conciliation.automatic_bucket_expenses()
        new_conciliation = {key: df[~df[self.conciliation.col_bucket].isna()].shape[0]
                            for key, df in self.conciliation.dfs.items()}
        self.redraw_all_tables()
        self.summary_refresh()
        message = "\n".join([f"Filas punteadas de {key1.value}: {value1} ({value1 - value2} nuevas)"
                             for (key1, value1), (key2, value2) in zip(new_conciliation.items(),
                                                                       old_conciliation.items())])
        messagebox.showinfo("Nuevo punteo", message)

    def handle_read_excel(self, update=False):
        file_path = ask_excel_filename()
        existing_data = self.conciliation.has_all_data
        if file_path:
            if update:
                if existing_data:
                    self.conciliation.read(file_path)
                else:
                    self.conciliation.update(file_path)
            else:
                if existing_data:
                    if not messagebox.askyesno(message="Ya hay datos cargados. ¿Desea continuar y perder los cambios?"):
                        return
                self.conciliation.read(file_path)
        self.create_tables()
        for key, table in self.tables.items():
            if table is not None:
                table.updateModel(TableModel(self.conciliation.dfs[key]))
                # table.clearFormatting()
                # table.redraw()
        self.redraw_all_tables(auto_resize_cols=True)
        self.summary_refresh()

    @check_missing_data
    def handle_save_to_excel(self):
        file_path = filedialog.asksaveasfilename(confirmoverwrite=False,  # It will be confirmed later
                                                 defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx")])

        if not file_path:
            return

        if os.path.exists(file_path):
            response = messagebox.askyesno("Warning", "El fichero ya existe, Desea sobreescribirlo?")
            if not response:
                return
        self.conciliation.save_as(file_path)
        messagebox.showinfo("Guardado", f"El fichero {file_path} ha sido guardado con éxito.")

    def exit_application(self):
        if messagebox.askyesno(message="¿Desea salir (los cambios no se guardarán)?"):
            self.quit()

    def summary_refresh(self):
        """Refreshes summary label with current selection"""

        def frmt(value):
            return format(value, ",.2f") + "€"

        def sum_cts(df) -> float:
            return df[self.conciliation.col_cents].sum() / 100

        def sum_cts_str(df) -> str:
            return frmt(sum_cts(df))

        summary_df, summary_dict = self.conciliation.check_buckets()
        if summary_df is not None:
            txt = "Sin asignar: banco {only_bnk} gastos {only_exp} ingresos {only_inc}".format(
                only_bnk=sum_cts_str(summary_dict["only_bnk"]), only_exp=sum_cts_str(summary_dict["only_exp"]),
                only_inc=sum_cts_str(summary_dict["only_inc"])
            )
            # Calculate unmatch
            dif_bnk_exp = frmt(sum_cts(summary_dict['bnk_exp']) - sum_cts(summary_dict['exp_bnk']))
            dif_bnk_inc = frmt(sum_cts(summary_dict['bnk_inc']) - sum_cts(summary_dict['inc_bnk']))

            txt += "\tAsignado: banco/ingresos {bnk_inc} (descuadre {dif_bnk_inc}) banco/gastos {bnk_exp} (descuadre {dif_bnk_exp})".format(
                bnk_inc=sum_cts_str(summary_dict["bnk_inc"]), dif_bnk_inc=dif_bnk_inc,
                bnk_exp=sum_cts_str(summary_dict["bnk_exp"]), dif_bnk_exp=dif_bnk_exp
            )
        else:
            txt = "No hay datos"
        self.lbl_summary.config(text=txt)

    @check_missing_data
    def handle_del_bucket_bnk(self):
        """Removes buckets from the current selection of bank data"""
        tbl_bnk = self.tables[DataType.BNK]
        buckets = tbl_bnk.getSelectedRowData()[self.conciliation.col_bucket].dropna()
        if not buckets.empty:
            if messagebox.askyesno(message="¿Desea borrar las asignaciones marcadas?"):
                self.conciliation.unbucket(buckets.values)
                self.summary_refresh()
                self.redraw_all_tables()
        else:
            messagebox.showinfo(message="No se han marcado filas asignadas en el banco")

    def _bucket_bnk_df(self, datatype_other, other_name):
        """
        Buckets selected rows of bank against selected rows of either expenses or incomes
        Args:
            datatype_other: the dataType of the other table
            other_name: either "expenses" or "incomes"

        Returns:
            None
        """
        if not self.conciliation.has_all_data:
            return
        table_other = self.tables[datatype_other]
        table_bnk = self.tables[DataType.BNK]
        sum_bnk = sum_other = None
        if ~(bnk := table_bnk.get_selected_or_all()).empty:
            sum_bnk = bnk[self.conciliation.col_cents].sum()
        if ~(other := table_other.get_selected_or_all()).empty:
            sum_other = other[self.conciliation.col_cents].sum()

        if ~bnk[self.conciliation.col_bucket].isna().all() or ~other[self.conciliation.col_bucket].isna().all():
            if not messagebox.askyesno(message=f"Las filas seleccionadas ya están asigandas. "
                                               f"Borre la asignación antes"):
                return
        if sum_other != sum_bnk or (sum_other is None and sum_bnk is None):
            if not messagebox.askyesno(message=f"Las cantidades no coinciden: "
                                               f"{sum_bnk / 100:.2f}€ vs {sum_other / 100:.2f}. "
                                               f"¿Aún asi desea puntearlos juntos?"):
                return

        self.conciliation.bucket(bnk.index, **{f"idx_{other_name}": other.index})
        self.summary_refresh()
        table_bnk.selectNone()
        table_other.selectNone()
        self.redraw_all_tables()
        self.tables[DataType.BNK].focus()
        self.var_filter_by.set("")

    @check_missing_data
    def handle_bucket_bnk_inc(self):
        """Tries to match the select rows in bank and expenses"""
        self._bucket_bnk_df(DataType.INC, "incomes")
        return

    @check_missing_data
    def handle_bucket_bnk_exp(self):
        """Tries to match the select rows in bank and expenses"""
        self._bucket_bnk_df(DataType.EXP, "expenses")
        return

    @check_missing_data
    def handle_filter_unassigned(self):
        self.redraw_all_tables()

    def redraw_all_tables(self, dict_dfs=None, auto_resize_cols=False):
        """
        Redraw all tables. Checks the status of self.filter_df to display all rows or just unassigned ones
        Args:
            dict_dfs: a dict of dfs to assign to the tables (for applying filters), indexed by DataType
            auto_resize_cols: if true, force autoresize columns (only when reading/updating data)
        Returns:
            None
        """
        dict_dfs = dict_dfs or {}
        for data_type in DataType:
            df = dict_dfs.get(data_type, self.conciliation.dfs.get(data_type, None))
            tbl = self.tables.get(data_type, None)
            if df is not None and tbl is not None:
                var_show = self.var_show.get()
                if var_show == self._show_unassigned:
                    df_paint = df[df[self.conciliation.col_bucket].isna()]
                elif var_show == self._show_assigned:
                    df_paint = df[~df[self.conciliation.col_bucket].isna()]
                else:
                    df_paint = df
                # Align left ("e") numeric dtypes and also bucket column
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col].dtype):
                        tbl.columnformats['alignment'][col] = "e"
                    # elif df[col].apply(lambda x: isinstance(x, str)).all():     # All column is text...
                    #     tbl.columnwidths[col] = max(tbl.columnwidths[col], df[col].str.len().max())
                tbl.columnformats['alignment'][self.conciliation.col_bucket] = "e"
                if auto_resize_cols:
                    tbl.autoResizeColumns()
                tbl.set_df_redraw(df_paint)
                # Change color of the lines bucketed and reset color for the rest
                colored = np.argwhere(~df_paint[self.conciliation.col_bucket].isna()).flatten().tolist()
                not_colored = np.argwhere(df_paint[self.conciliation.col_bucket].isna()).flatten().tolist()
                tbl.setRowColors(colored, clr=self._color_bucketed, cols="all")
                tbl.setRowColors(not_colored, clr="", cols="all")   # Clear colors
                # tbl.redraw()
                # tbl.model.df = df_paint
                # tbl.redraw()

    def filter_sum_df(self, data_type: DataType):
        """
        Filter other tables using the sum of a given data
        Args:
            data_type: a DataType to inform whether the sum will use bank, incomes or expenses data
        Returns:
            None
        """
        if data_type is None:
            self.redraw_all_tables()
            return
        sum_tbl = self.tables[data_type].getSelectedRowData()[self.conciliation.col_cents].sum()
        # filter rows to match sum of selected rows of given data_type
        offset = 2
        # dfs = [df[df[self.conciliation.col_cents] == sum_tbl] if key != data_type else
        #        self.tables[data_type].getSelectedRowData()
        #        for key, df in self.conciliation.dfs.items()]
        dfs = {key: df[df[self.conciliation.col_cents].between(sum_tbl - offset, sum_tbl + offset)] if key != data_type else
               self.tables[data_type].getSelectedRowData()
               for key, df in self.conciliation.dfs.items()}
        self.redraw_all_tables(dict_dfs=dfs)

    @check_missing_data
    def handle_filter_by(self):
        """Shows other rows that match the current selected rows, driven by the variable included in the radio button"""
        data_type = self.var_filter_by.get()
        data_type = DataType[data_type] if data_type else None
        if data_type and self.tables[data_type].model.getRowCount() > 0:
            if ~(filter_df := self.tables[data_type].get_selected_or_all()).empty:
                buckets = filter_df[self.conciliation.col_bucket]
                # print(buckets)
                if not buckets.isna().all() and buckets.isna().any():
                    # Mix of assigned and not assigned -> cancel
                    messagebox.showerror(message="Hay mezcla de filas asignadas y sin asignar, por favor elija otras")
                    self.var_filter_by.set("")
                    return
                elif buckets.isna().all():
                    self.filter_sum_df(data_type)
                    return
                else:
                    # Only assigned -> filter rows to match the assigned bank selected rows
                    dfs = {key: df[df[self.conciliation.col_bucket].isin(buckets.values)]
                           for key, df in self.conciliation.dfs.items()}
                    self.redraw_all_tables(dict_dfs=dfs)
        else:
            self.redraw_all_tables()


def main(initial_filename=None):
    app = ConciliationApp(initial_filename)
    app.mainloop()


if __name__ == '__main__':
    main(None)
