from __future__ import annotations

import pypsa
import pandas as pd
import matplotlib.pyplot as plt
from typing import Any

from extractor import ResultsExtractor
from peakiness import Peakiness
from shed_season import ShedSeason
from shed_days import ShedDays
from ramping import Ramping
from shift_season import ShiftSeason
from capacity import Capacity
from cost import Cost

NICE_NAMES = {
    "res": "Residential",
    "com": "Commercial",
    "trn": "Transportation",
    "ind": "Industrial",
}
YEAR = 2019
NETWORKS = "./data/networks/"
FONTSIZE = 12
FIGSIZE = (20, 6)


class ResultsAccessor:

    available_results = [
        # dr specific metrics
        "peakiness",
        "ramping",
        "shed_season",
        "shed_days",
        "shift_season",
        "shift_days",
        # ems metrics
        "capacity",
        "cost",
        "dr"
    ]

    def __init__(self, n: str):
        self.n = pypsa.Network(n)

    def __iter__(self):
        return self.available_results

    def _is_valid_input(self, input: str) -> bool:
        if input in self.available_results:
            return True
        else:
            print(f"{input} is not valid. Accepted inputs are {self.available_results}")
            return False

    def _get_extractor(self, input: str) -> ResultsExtractor:

        assert self._is_valid_input(input)

        if input == "peakiness":
            return Peakiness(self.n, YEAR)
        elif input == "ramping":
            return Ramping(self.n, YEAR)
        elif input == "shed_season":
            return ShedSeason(self.n, YEAR)
        elif input == "shed_days":
            return ShedDays(self.n, YEAR)
        elif input == "shift_season":
            return ShiftSeason(self.n, YEAR)
        elif input == "capacity":
            return Capacity(self.n)
        elif input == "cost":
            return Cost(self.n, YEAR)
        elif input == "dr":
            return DemandResponse(self.n, YEAR)
        else:
            raise NotImplementedError

    def get_dataframe(self, input: str) -> pd.DataFrame:
        extractor = self._get_extractor(input)
        return extractor.extract_dataframe()

    def get_datapoint(self, input: str) -> Any:
        extractor = self._get_extractor(input)
        return extractor.extract_datapoint()

    def plot(self, input: str, **kwargs) -> tuple[plt.figure, plt.axes]:
        extractor = self._get_extractor(input)

        fontsize = kwargs.get("fontsize", FONTSIZE)
        figsize = kwargs.get("figsize", FIGSIZE)

        return extractor.plot(figsize=figsize, fontsize=fontsize, **kwargs)


if __name__ == "__main__":

    network = "elec_s70_c4m_ec_lv1.0_3h_E-G.nc"

    ra = ResultsAccessor(NETWORKS + network)

    # print(ra.get_datapoint("cost"))
    ra.plot("cost", save="test.png")
