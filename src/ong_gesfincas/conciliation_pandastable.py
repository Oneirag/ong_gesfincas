"""
Extends pandas table to have a custom toolbar (that sum selected value in cents)
"""
from tkinter import Label

import pandas as pd

from pandastable import Table
from src.ong_gesfincas.conciliation_model import Conciliation


class ConciliationTable(Table):
    def __init__(self, parent=None, **kwargs):
        # Force not to show status bar
        kwargs['showstatusbar'] = False
        Table.__init__(self, parent, **kwargs)
        self.statusbar = None

    def show(self, callback=None):
        """Adds a status bar for summarizing"""
        Table.show(self, callback)
        # Add a simple status bar
        self.statusbar = Label(self.parentframe, text="")
        self.statusbar.grid(row=3, column=0, columnspan=2, sticky='ew')

    def __redraw_statusbar(self):
        if hasattr(self, "statusbar"):
            try:
                rows = self.getSelectedRowData()
                # print(rows)
            except:
                rows = pd.DataFrame()
            if not rows.empty:
                total = rows[Conciliation.col_cents].sum() / 100
                text = f"Suma de la selección: {total:,.2f}€"
            else:
                text = "Nada seleccionado"
            self.statusbar.config(text=text)

    def redraw(self, event=None, callback=None):
        self.columnwidths[Conciliation.col_cents] = 0       # Hide value cents column
        Table.redraw(self, event=event, callback=callback)
        self.__redraw_statusbar()

    def handle_left_click(self, event):
        """Example - override left click"""
        Table.handle_left_click(self, event)
        self.__redraw_statusbar()
        return

    def handle_left_release(self, event):
        Table.handle_left_release(self, event)
        self.__redraw_statusbar()

    def handle_mouse_drag(self, event):
        super().handle_mouse_drag(event)
        self.__redraw_statusbar()

    def handle_left_ctrl_click(self, event):
        Table.handle_left_ctrl_click(self, event)
        self.__redraw_statusbar()

    def handle_left_shift_click(self, event):
        Table.handle_left_shift_click(self, event)
        self.__redraw_statusbar()

    # def mouse_wheel(self, event):
    #     """Handle mouse wheel scroll for windows and mac (darwin)"""
    #
    #     if event.num == 5 or event.delta == -120 or (self.ostyp == "darwin" and event.delta == -1):
    #         event.widget.yview_scroll(1, UNITS)
    #         self.rowheader.yview_scroll(1, UNITS)
    #     if event.num == 4 or event.delta == 120 or (self.ostyp == "darwin" and event.delta == 1):
    #         if self.canvasy(0) < 0:
    #             return
    #         event.widget.yview_scroll(-1, UNITS)
    #         self.rowheader.yview_scroll(-1, UNITS)
    #     self.redrawVisible()
    #     return

    def get_selected_or_all(self):
        """Gets selected rows if any row is selected, else get all rows"""
        if self.model.df.empty:
            return self.model.df  # If nothing to select...return emtpy dataframe
        try:
            selected = self.getSelectedRowData()
            return selected
        except Exception as e:
            return self.model.df

    def set_df_redraw(self, new_df: pd.DataFrame):
        """
        Sets a new DataFrame for current table. Changes model accordingly and tries to fix selected rows
        to match previous selection
        Args:
            new_df: A pandas dataframe
        Returns:
            None
        """
        if new_df.empty:
            self.selectNone()
            self.model.df = new_df
        else:
            old_selection = self.get_selected_or_all()
            self.model.df = new_df
            new_selection = new_df.index.intersection(old_selection.index)
            if new_selection.empty:
                self.selectNone()
            else:
                # Turn indexes into row positions
                row_positions = [new_df.index.get_loc(idx) for idx in new_selection]
                # print(old_selection.index, "->", new_selection, "->", row_positions)
                self.selectNone()
                self.redraw()
                self.movetoSelection(row_positions[0])
                self.setSelectedRows(row_positions)
        self.redraw()

    def set_defaults(self):
        """Modified to make maxcellwidth wider"""
        Table.set_defaults(self)
        self.maxcellwidth = 600  # Concepto column is too wide, so allow wider columns
        self.thousandseparator = ","  # Default thousand separator... does not work :(
