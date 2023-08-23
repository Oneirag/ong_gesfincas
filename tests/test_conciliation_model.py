"""
Some test for conciliations
"""
import os
from unittest import TestCase, main

from src.ong_gesfincas import DataType
from src.ong_gesfincas.conciliation_model import Conciliation


class TestConciliationUpdate(TestCase):
    base_global_file = os.path.join(os.path.dirname(__file__), "../data/test_data", "global_test_data.xlsx")
    test_global_file = os.path.join(os.path.dirname(__file__), "../data/test_data",
                                    "global_test_data_changed.xlsx")
    # These are the changes made in test_global_file
    all_bad_buckets = (
        0,  # Deleted row from expenses
        1,  # Modified cash value in bank (increased 1000€)
        2,  # Deleted row from bank
        3,  # Modified cash value in expenses (increased 1000€)
        73, 74,  # These two rows are unchanged, but as they have exactly the same values, cannot bucket them
        220,  # Deleted one row from bank (there are multiple rows)
        210,  # Deleted one row from expenses (there are two rows)
    )

    def setUp(self) -> None:
        self.conciliation = Conciliation(self.base_global_file)
        self.old_dfs = self.conciliation.backup_dfs()
        self.old_bnk = self.old_dfs[DataType.BNK]

    def __test_update(self, bad_buckets: list | tuple):
        """Does the test, comparing against the old dataframes"""
        new_bnk = self.conciliation.df_bank
        old_buckets = self.old_bnk[self.conciliation.col_bucket].dropna().unique()
        # The order in bad buckets is important, as they are processed in the order they appear not in ascending order
        # Check 1: all buckets must have been reassigned unless the bad ones
        self.assertEqual(len(old_buckets),
                         len(new_bnk[self.conciliation.col_bucket].dropna().unique()) + len(bad_buckets),
                         "Number of new buckets is incorrect"
                         )

        # Check 2: Number of rows of each bucket must be the same
        for (key1, df_old), (key2, df_new) in zip(self.old_dfs.items(), self.conciliation.dfs.items()):
            self.assertEqual(key1, key2, "Keys of dataframes do not match")
            new_count = df_new[~df_new[self.conciliation.col_bucket].isna()][
                self.conciliation.col_bucket].value_counts()
            old_count = df_old[~df_old[self.conciliation.col_bucket].isin(bad_buckets) &
                               ~df_old[self.conciliation.col_bucket].isna()][
                self.conciliation.col_bucket].value_counts()
            for value_count in new_count.unique():
                self.assertEqual(len(new_count[new_count == value_count]),
                                 len(old_count[old_count == value_count]),
                                 f"The number of buckets of {value_count} elements changed for {key1.name}. "
                                 f"Totals: {len(new_count)} vs {len(old_count)}")
            self.assertTrue((new_count.values == old_count.values).all(),
                            f"Number of buckets do not match for {key1.name}")

        # Check 3: sum of old and new buckets must be the same
        for (key1, df_old), (key2, df_new) in zip(self.old_dfs.items(), self.conciliation.dfs.items()):
            self.assertEqual(key1, key2, "Keys of dataframes do not match")
            new_sum = df_new[~df_new[self.conciliation.col_bucket].isna()][self.conciliation.col_cents].sum()
            old_sum = df_old[~df_old[self.conciliation.col_bucket].isin(bad_buckets) &
                             ~df_old[self.conciliation.col_bucket].isna()][self.conciliation.col_cents].sum()
            self.assertEqual(new_sum, old_sum, f"Sums do not match for {key1.name}")

    def test_read_file_update_bank(self):
        """Tests that no matter bank is read from a file or updated, df_bank is the same (without buckets)"""
        self.conciliation.read(self.test_global_file)
        old_dfs = self.conciliation.backup_dfs()
        old_bank = old_dfs[DataType.BNK].drop(self.conciliation.col_bucket, axis=1)
        new_bank0 = self.conciliation.read_bank(self.test_global_file)
        self.conciliation.update_dfs({DataType.BNK: new_bank0})
        new_bank1 = self.conciliation.df_bank.drop(self.conciliation.col_bucket, axis=1)
        self.assertTrue(new_bank0.equals(new_bank1.drop(self.conciliation.col_cents, axis=1)),
                        "Bank data is not the same as the version read")
        # Important use of fillna, as CALLE column has many blank data
        self.assertTrue(old_bank.fillna("").equals(new_bank1.fillna("")),
                        "Bank df is not correctly updated")

    def test_update_bank_file(self):
        """Test reading all from original_data and updating bank only"""

        new_bank = self.conciliation.read_bank(self.test_global_file)
        self.conciliation.update_dfs({DataType.BNK: new_bank})
        # buckets = self.conciliation.df_bank[self.conciliation.col_bucket].unique()
        # self.conciliation.automatic_bucket_expenses()
        # new_buckets = self.conciliation.df_bank[self.conciliation.col_bucket].unique()
        # print(len(buckets), len(new_buckets))     # No change!
        bad_buckets = (
            1,  # Modified cash value in bank (increased 1000€)
            2,  # Deleted row from bank
            73, 74,  # This two rows have exactly the same values, cannot bucket them
            220,  # Deleted row from bank (there are multiple rows)
        )
        self.__test_update(bad_buckets=bad_buckets)

    def test_update_global_file(self):
        """
        Tests the update function. Reads a global file (self.base_file), then updates it with the contents of other
        global file (self.test_file) that have some "bad buckets". Checks that bad buckets are properly skipped
        """
        bad_buckets = (
            0,  # Deleted row from expenses
            1,  # Modified cash value in bank (increased 1000€)
            2,  # Deleted row from bank
            3,  # Modified cash value in expenses (increased 1000€)
            73, 74,  # This two rows have exactly the same values, cannot bucket them
            220,  # Deleted row from bank (there are multiple rows)
            210,  # Deleted row from expenses (there are two rows)
        )
        self.conciliation.update(self.test_global_file)
        self.__test_update(bad_buckets)


if __name__ == '__main__':
    main()
