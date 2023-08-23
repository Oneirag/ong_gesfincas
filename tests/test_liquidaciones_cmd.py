from unittest import TestCase

from ong_gesfincas import get_data_path
from ong_gesfincas.liquidaciones_cmd import read_gesfincas


class Test(TestCase):

    def setUp(self) -> None:
        self.gesfincas_file = get_data_path("original_data/liquidaciones_original.xlsx")
        self.df_expenses, self.df_incomes = read_gesfincas(self.gesfincas_file)

    def test_read_gesfincas(self):
        """Check that incomes don't have rows with all nulls (as they should be filled with previous values"""
        self.assertFalse(self.df_incomes.iloc[1:, :2].isna().all(axis=1).any(),
                        "There are incomes not properly filled")

