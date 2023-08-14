"""
Functions to provide conciliation model. The process of matching a column is called "bucketing"
"""

from difflib import SequenceMatcher

import pandas as pd

from liquidaciones import DataType
from liquidaciones.openpyxl_helpers import df_to_excel


class Conciliation:
    _COL_CASH_BANK = "Importe"
    _COL_CASH_INCOME = "Cobrado"
    _COL_CASH_EXPENSES = "Pagos"
    _COL_BUCKET = "Bucket"
    _COL_CENTS = "value_cents"  # A column in cents to be converted to integer so calculations work well
    # Names of the sheets to read data from
    _SHEET_BNK = "banco"
    _SHEET_INC = "ingresos"
    _SHEET_EXP = "gastos"
    # Columns of the sheets to read data from
    # _COLS_BNK = ['Concepto', 'Importe', 'CALLE']
    _COLS_BNK = ['Concepto', 'Importe']
    _COLS_INC = ['Piso/Local', 'Inquilino', 'Fecha', 'Cobrado', 'Pendiente', 'finca']
    _COLS_EXP = ['CONCEPTO', 'Pagos', 'Abonos', 'finca']

    @classmethod
    @property
    def col_bucket(cls):
        return cls._COL_BUCKET

    @classmethod
    @property
    def col_cents(cls):
        return cls._COL_CENTS

    def __init__(self, filename: str = None):
        """
        Reads a filename and returns a tuple of pandas dataframes with bank data, expenses data and income data
        Args:
            filename: full name of an Excel input file

        Returns:
            None
        """
        self.df_expenses = None
        self.df_bank = None
        self.df_incomes = None
        self.dfs = dict()
        if filename:
            self.read(filename)

    def __create_cents(self, df, col_cash_orig) -> pd.DataFrame:
        """Creates a new column with the original_data cash orig converted to cents instead of euros"""
        # df.loc[:, self._COL_CENTS] = (df[col_cash_orig] * 100).round(0).astype(int)
        if self.col_cents not in df.columns:  # Don't try to replicate column
            df.insert(len(df.columns), self.col_cents, (df[col_cash_orig].astype(float) * 100).round(0).astype(int))
        return df

    def __unassigned_df(self, df):
        idx = df[self._COL_BUCKET].isna()
        return df.loc[idx]

    def set_dfs(self, df_dict: dict, read_buckets=True):
        """Set data from a dictionary of dfs indexed by data type"""
        if DataType.EXP in df_dict:
            self.df_expenses = df_dict[DataType.EXP][self._COLS_EXP]
            # If expenses sum a positive value: change sign, otherwise it won't match bank criterion
            if self.df_expenses[self._COL_CASH_EXPENSES].sum() > 0:
                self.df_expenses.loc[:, self._COL_CASH_EXPENSES] = - self.df_expenses[self._COL_CASH_EXPENSES]
            self.dfs[DataType.EXP] = self.df_expenses

        if DataType.BNK in df_dict:
            self.df_bank = df_dict[DataType.BNK][self._COLS_BNK]
            self.df_bank = self.df_bank[~self.df_bank[self._COL_CASH_BANK].isna()]  # Remove not needed nans
            self.dfs[DataType.BNK] = self.df_bank

        if DataType.INC in df_dict:
            self.df_incomes = df_dict[DataType.INC][self._COLS_INC]
            self.dfs[DataType.INC] = self.df_incomes

        # Add cents column
        if DataType.BNK in self.dfs:
            self.df_bank = self.__create_cents(self.df_bank, self._COL_CASH_BANK)
        if DataType.EXP in self.dfs:
            self.df_expenses = self.__create_cents(self.df_expenses, self._COL_CASH_EXPENSES)
        if DataType.INC in self.dfs:
            self.df_incomes = self.__create_cents(self.df_incomes, self._COL_CASH_INCOME)

        # Treat buckets. If read_buckets and all buckets found, re-read buckets, else create empty buckets
        buckets_found = (self.has_all_data and read_buckets and
                         all([(self.col_bucket in df.columns) for df in df_dict.values()]))
        for key, df in self.dfs.items():
            if self.col_bucket in df:
                if buckets_found:
                    df[self.col_bucket] = None
            else:
                df.insert(len(df.columns), self._COL_BUCKET,
                          df_dict[key][self._COL_BUCKET].astype(dtype=pd.Int64Dtype()) if buckets_found else None)
        return

    def backup_dfs(self) -> dict:
        """Returns a copy of the dict of dfs. Useful for update and tests"""
        return {k: df.copy(deep=True) for k, df in self.dfs.items()}

    def read_dfs(self, filename: str) -> dict:
        """Reads dfs and return a dict of DataFrames indexed by DataType"""
        with pd.ExcelFile(filename) as excel:
            read_dfs = {
                key: pd.read_excel(excel, sheet_name=sheet) for key, sheet in
                {
                    DataType.BNK: self._SHEET_BNK, DataType.INC: self._SHEET_INC, DataType.EXP: self._SHEET_EXP
                }.items()
            }
        return read_dfs

    def read(self, filename: str, read_buckets=True):
        """
        Reads data from an Excel workbook named filename. Data are read from self._SHEET_BNK, self._SHEET_INC and
        self._SHEET_EXP worksheets.
        Args:
            filename: name of the Excel file to read data from
            read_buckets: True (default) to read buckets from the file. False to ignore them (set all to None)

        Returns:

        """
        read_dfs = self.read_dfs(filename)
        self.set_dfs(read_dfs, read_buckets)

    def read_bank(self, bank_filename: str) -> pd.DataFrame | None:
        """Reads bank data as a df from the first sheet of the given Excel file. Returns None if file is invalid"""
        df = pd.read_excel(bank_filename, header=None)
        header_rows = (0, 7)  # Potential rows containing header data
        for header_row in header_rows:
            df_header = df.iloc[header_row, :]
            if df_header.isin(self._COLS_BNK).sum() >= (len(self._COLS_BNK) - 1):
                df_bank = df.iloc[header_row + 1:, :]
                df_bank.columns = df.iloc[header_row, :]
                df_bank = df_bank[~df_bank[self._COL_CASH_BANK].isna()]  # Remove nan values
                df_bank.index = range(df_bank.shape[0])
                df_bank = df_bank[self._COLS_BNK]
                return df_bank
        return None

    def update_dfs(self, df_dict: dict):
        # TODO: Fix the case when two (or more) rows EXACTLY EQUAL in bank and expenses, as it cannot reassign
        old_dfs = self.backup_dfs()
        self.set_dfs(df_dict, read_buckets=False)
        # Delete all buckets (needed if update of just some dfs and not all)
        for df in self.dfs.values():
            df.loc[:, self.col_bucket] = None
        # First step: merge dfs from old_dfs with the new dfs from self.dfs
        merged_dict = dict()
        for (key, df_old), (key_new, df_new) in zip(old_dfs.items(), self.dfs.items()):
            assert key == key_new
            # Remove not bucketed from old dfs
            df_old = df_old[~df_old[self.col_bucket].isna()]
            # Remove bucket column from new dfs (not needed as bucket from old_df will be used)
            df_new = df_new.drop(self.col_bucket, axis=1)
            # merge on the common columns (those available both in new and old dfs)
            common_cols = df_old.columns.intersection(df_new.columns).to_list()
            # Add indexes to columns "index_old" for df_old and "index_new" for df_new
            df_old.insert(len(df_old.columns), 'index_old', df_old.index)
            df_new.loc[:, 'index_new'] = df_new.index
            # merge on the common_cols
            merged = pd.merge(df_old, df_new, left_on=common_cols, right_on=common_cols, how="left")
            merged_dict[key] = merged
        # Now check old buckets to see if they can be applied to the new dfs. The bank is used as the master for buckets
        for bucket in old_dfs[DataType.BNK][self.col_bucket].dropna().unique():
            kwargs = dict()
            # arg_name is needed for self.bucket
            for key, arg_name in [(DataType.BNK, "idx_bank"), (DataType.EXP, "idx_expenses"),
                                  (DataType.INC, "idx_incomes")]:
                merged = merged_dict[key]
                # These are the common rows found in old_df and new_df (those in merged DataFrame)
                bucket_merged = merged[merged[self.col_bucket] == bucket]
                bucket_orig = old_dfs[key][old_dfs[key][self.col_bucket] == bucket]
                # If there are missing rows in the merge or the number of rows in the merge is different from the
                # original_data, then do not update bucket
                if bucket_merged['index_new'].isna().any() or \
                        bucket_merged.shape[0] != bucket_orig.shape[0]:
                    print(bucket)
                    # print(bucket_merged)
                    # print(bucket_orig)
                    kwargs = None
                    break  # There is some row missing, do not bucket anything
                elif bucket_merged.empty:
                    kwargs[arg_name] = None
                else:
                    kwargs[arg_name] = bucket_merged['index_new'].values
            if kwargs:
                if not (kwargs["idx_expenses"] is None and kwargs["idx_incomes"] is None):
                    self.bucket(**kwargs)
                else:
                    pass        # There is a bucket found in bank that does not appear neither in expenses nor incomes

    def update(self, filename: str):
        """
        Updates current dfs from a file. Assumes that the new file comes with no valid buckets, so it ignores any
        bucket from the new file and tries to maintain the old buckets from the dfs already in memory
        Args:
            filename: an Excel filename that is passed to 'read' function, so see 'read' function for details

        Returns:
            None
        """

        df_dict = self.read_dfs(filename)
        self.update_dfs(df_dict)

    def unassigned(self, df_type: DataType):
        return self.__unassigned_df(self.dfs[df_type])

    @property
    def unassigned_exp(self):
        return self.__unassigned_df(self.df_expenses)

    @property
    def unassigned_inc(self):
        return self.__unassigned_df(self.df_incomes)

    @property
    def unassigned_bnk(self):
        return self.__unassigned_df(self.df_bank)

    def get_next_bucket(self):
        last_bucket = self.df_bank[self._COL_BUCKET].max()
        if pd.isna(last_bucket):
            return 0
        else:
            return last_bucket + 1

    def unbucket(self, idx):
        """Unassigns a list of idx"""
        if isinstance(idx, int):
            idx = [idx]
        for df in self.df_bank, self.df_expenses, self.df_incomes:
            df.loc[df[self._COL_BUCKET].isin(idx), self._COL_BUCKET] = None

    def bucket(self, idx_bank, idx_expenses=None, idx_incomes=None):
        """Assigns to a bucket a list of rows in either expenses or income"""

        if idx_expenses is None and idx_incomes is None:
            raise ValueError("Either idx_expenses or idx_income should be provided")
        id = self.get_next_bucket()
        self.df_bank.loc[idx_bank, self._COL_BUCKET] = id
        if idx_expenses is not None:
            self.df_expenses.loc[idx_expenses, self._COL_BUCKET] = id
        elif idx_incomes is not None:
            self.df_incomes.loc[idx_incomes, self._COL_BUCKET] = id

    def clear_orphan_buckets(self) -> list:
        """
        Deletes any orphan bucket (a bucket that is not present in any other df)
        Returns:
        The list of the orphan buckets found
        """
        orphan_buckets = []
        for df0 in self.dfs.values():
            if df0 is None:
                continue
            buckets0 = set(df0[self.col_bucket].dropna().unique())
            if not buckets0:
                continue
            for df1 in self.dfs.values():
                if df1 is None or df1 is df0:
                    continue
                buckets1 = set(df1[self.col_bucket].dropna().unique())
                # Remove buckets present in buckets0 and buckets1
                buckets0 = buckets0.difference(buckets1)
            if buckets0:
                for b in buckets0:
                    orphan_buckets.append(int(b))
                    self.unbucket(int(b))
        return orphan_buckets


    def automatic_bucket_expenses(self, delta_cents: float = 1):
        """
        Buckets (assigns) automatically rows in the bank to rows in expenses, doing these steps:
            First step: assigns those rows that perfectly match (same amount)
            Second step: assigns those rows that almost perfectly match (+- delta_cents)
            Third step: to a given row in bank, assigns two consecutive rows in expenses if the sum matches
        Args:
            delta_cents: in case there is no exact match, find approximate match with this different to actual value
            in cents
        Returns:
            None
        """
        ###############################
        # Fist step: find exact match
        ###############################
        for df_type in (t for t in DataType if t != DataType.BNK):
            for idx_bnk, row in self.df_bank.iterrows():
                if not pd.isna(row[self._COL_BUCKET]):
                    continue
                target = row[self._COL_CENTS]
                found = self.unassigned(df_type)[self.unassigned(df_type)[self._COL_CENTS] == target]
                idx = None
                if found.shape[0] == 1:
                    idx = found.index.values
                # If there are more than 1 posible rows, only find the best one in the case of expenses.
                elif found.shape[0] > 1:
                    # For incomes there are too many possibilities (e.g. many tenants with the same amount)
                    if df_type == DataType.INC:
                        # print(found)
                        continue
                    elif df_type == DataType.EXP:
                        # If more than one is matched, match with the most similar one using "Concepto" column
                        matches = found['CONCEPTO'].apply(lambda x: SequenceMatcher(None, row['Concepto'].upper(),
                                                                                    x.upper()).ratio())
                        idx = matches.idxmax()
                if idx is not None:
                    if df_type == DataType.EXP:
                        self.bucket(idx_bnk, idx_expenses=idx)
                    elif df_type == DataType.INC:
                        self.bucket(idx_bnk, idx_incomes=idx)

        ########################################################
        # Second step: find approximate match (within +- delta)
        ########################################################
        for idx_bnk, row in self.df_bank.iterrows():
            if not pd.isna(row[self._COL_BUCKET]):
                continue
            target = row[self._COL_CENTS]
            # try to find those with +-delta
            max_value = target + delta_cents
            min_value = target - delta_cents
            found = self.unassigned_exp[self.unassigned_exp[self._COL_CENTS].between(min_value, max_value)]
            # print(found.shape)
            if found.shape[0] == 1:
                # print(idx_bnk, found, self.df_bank[idx_bnk, self.col_cents], self.df_expenses[idx_bnk, self.col_cents])
                self.bucket(idx_bnk, idx_expenses=found.index.values)
                continue

        ##################################################################
        # Third step: find match within two consecutive rows in expenses
        ##################################################################
        expenses = self.unassigned_exp
        idx_consecutive_exp = expenses.index[:-1][expenses.index.values[1:] - expenses.index.values[:-1] == 1]
        consecutive_exp = list([expenses.loc[[idx, idx + 1], self._COL_CENTS].sum().round(2)
                                for idx in idx_consecutive_exp])
        for idx_bnk, row in self.unassigned_bnk.iterrows():
            target = row[self._COL_CENTS]
            for idx_exp, value_exp in zip(idx_consecutive_exp, consecutive_exp):
                if pd.isna(self.df_expenses.loc[idx_exp, self._COL_BUCKET]):
                    idx_bucket = [idx_exp, idx_exp + 1]
                    col_finca = "finca"
                    if expenses.loc[idx_bucket[0], col_finca] == expenses.loc[idx_bucket[1], col_finca]:
                        if target == value_exp:
                            self.bucket(idx_bnk, idx_expenses=idx_bucket)

        return

    def _check_vs_bnk(self, other_df: pd.DataFrame):
        """
        Checks a given dataframe vs bank: finds the common ones, the ones only in bank and the ones only in other
        Args:
            other_df: the other dataframe to check against bank

        Returns:
            A tuple: both_bnk, both_other, only_bnk, only_other

        """
        bnk = self.df_bank
        bucket_bnk = bnk[self.col_bucket]
        bucket_other = other_df[self.col_bucket]
        idx_common_bnk = bucket_bnk.isin(bucket_other) & ~bucket_bnk.isna()
        idx_common_other = bucket_other.isin(bucket_bnk) & ~bucket_other.isna()  # Finds also None???
        both_bnk = bnk[idx_common_bnk]
        both_other = other_df[idx_common_other]
        only_bnk = bnk[~idx_common_bnk]
        only_other = other_df[~idx_common_other]
        return both_bnk, both_other, only_bnk, only_other

    @property
    def has_all_data(self):
        if len(self.dfs) == len(DataType):
            return True
        else:
            return False

    def check_buckets(self):
        # Check matching buckets from df1 and df2
        if not self.has_all_data:
            return None, None  # It cannot be done has it has no data
        bnk_exp, exp_bnk, bnk_without_exp, only_exp = self._check_vs_bnk(self.df_expenses)
        bnk_inc, inc_bnk, bnk_without_inc, only_inc = self._check_vs_bnk(self.df_incomes)
        if bnk_exp[self.col_bucket].isin(bnk_inc[self.col_bucket]).any():
            raise NotImplementedError("There are values both in Expenses and income")
        only_bnk = self.df_bank.loc[bnk_without_exp.index.intersection(bnk_without_inc.index), :]
        if not self.df_bank.shape[0] == (bnk_exp.shape[0] + bnk_inc.shape[0] + only_bnk.shape[0]):
            raise ValueError("Bad code: bank is not correctly split among incomes and expenses")

        retval = pd.DataFrame()
        retval.loc["banco", "solo"] = only_bnk[self.col_cents].sum() / 100
        retval.loc["gastos", "solo"] = only_exp[self.col_cents].sum() / 100
        retval.loc["ingresos", "solo"] = only_inc[self.col_cents].sum() / 100
        retval.loc["banco", "gastos"] = bnk_exp[self.col_cents].sum() / 100
        retval.loc["gastos", "gastos"] = exp_bnk[self.col_cents].sum() / 100
        retval.loc["banco", "ingresos"] = bnk_inc[self.col_cents].sum() / 100
        retval.loc["ingresos", "ingresos"] = inc_bnk[self.col_cents].sum() / 100
        retval.fillna(0, inplace=True)
        retdict = dict(only_bnk=only_bnk, only_inc=only_inc, only_exp=only_exp,
                       bnk_inc=bnk_inc, bnk_exp=bnk_exp, inc_bnk=inc_bnk, exp_bnk=exp_bnk
                       )
        return retval, retdict

    def save_as(self, filename):
        """Saves model to an Excel filename so it can be used later. Overwrites file, does not check anything"""

        summary, dict_conciliation = self.check_buckets()

        def inner_merge_no_duplicates(df1: pd.DataFrame, df2: pd.DataFrame, on: str) -> pd.DataFrame:
            """
            Returns an inner merge of the given dataframes by the given column (defaults to bucket), removing duplicated
            rows either in df1 or df2 (setting them to None) so they can be summed in a pivot table without duplicates
            Args:
                df1: first DataFrame. It must have the "on" column as last column
                df2: second DataFrame. It must have the "on" column as last column
                on: the name of the common column in df1 and df2 used for merge

            Returns:
                a pandas dataframe with the values of df1 and df2 merged using on column
            """
            retval = pd.merge(df1, df2, on=on, how="inner")
            # Now, remove duplicated values either in df1 or df2 from retval (so they sum correctly)
            col_bucket_merge = retval.columns.get_loc(on)
            cols_df1 = retval.columns[slice(None, col_bucket_merge)]  # slice for columns of df1
            cols_df2 = retval.columns[slice(col_bucket_merge + 1)]  # slice for columns of df2
            for bucket in retval[self.col_bucket].unique():
                rows_retval = retval[retval[self.col_bucket] == bucket].index
                for idx_group in rows_retval[1:]:  # Does nothing if just 1 row found
                    if (retval.loc[idx_group, cols_df1] == retval.loc[rows_retval[0], cols_df1]).all():
                        retval.loc[idx_group, cols_df1] = None
                    elif (retval.loc[idx_group, cols_df2] == retval.loc[rows_retval[0], cols_df2]).all():
                        retval.loc[idx_group, cols_df2] = None
                    pass
            return retval

        def get_conciliation_df(dict_conciliation: dict, one: str, other: str) -> pd.DataFrame:
            df1 = dict_conciliation[f"{one}_{other}"].drop(self.col_cents, axis=1)
            df2 = dict_conciliation[f"{other}_{one}"].drop(self.col_cents, axis=1)
            return inner_merge_no_duplicates(df1, df2, self.col_bucket)

        with pd.ExcelWriter(filename) as writer:
            for df, sheet_name in [
                (self.df_bank, self._SHEET_BNK), (self.df_incomes, self._SHEET_INC),
                (self.df_expenses, self._SHEET_EXP),
                (get_conciliation_df(dict_conciliation, "bnk", "exp"), f"{self._SHEET_BNK}_{self._SHEET_EXP}"),
                (get_conciliation_df(dict_conciliation, "bnk", "inc"), f"{self._SHEET_BNK}_{self._SHEET_INC}"),
            ]:
                if self.col_cents in df.columns:
                    df = df.drop(self.col_cents, axis=1)
                df_to_excel(df, writer, sheet_name)

    def main(self):
        self.automatic_bucket_expenses()
        # self.bucket_bank_expenses()
        match, match_dict = self.check_buckets()
        print(match)
        return match


if __name__ == '__main__':
    from tests.test_conciliation_model import TestConciliationUpdate

    test_filename = "../data/test_data/global_test_data.xlsx"
    conciliation = Conciliation(test_filename)
    match = conciliation.main()
    conciliation.unbucket(0)
    # match.to_excel("output.xlsx", index=False)
    # conciliation.save_as("test_output.xlsx")
    conciliation.read(TestConciliationUpdate.base_global_file)
    conciliation.update(TestConciliationUpdate.test_global_file)

    pass
