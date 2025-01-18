from __future__ import annotations

import pypsa
import pandas as pd
import matplotlib.pyplot as plt
from typing import Any, Optional

from pypsadr.extractor import ResultsExtractor
from pypsadr.peakiness import Peakiness
from pypsadr.shed_season import ShedSeason
from pypsadr.shed_days import ShedDays
from pypsadr.ramping import Ramping
from pypsadr.shift_season import ShiftSeason
from pypsadr.capacity import Capacity
from pypsadr.cost import Cost
from pypsadr.demand_response import DemandResponse

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(
    filename="pypsadr.log",
    encoding="utf-8",
    level=logging.DEBUG,
    filemode="w",
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.getLogger("pypsa").setLevel(logging.INFO)

NICE_NAMES = {
    "res": "Residential",
    "com": "Commercial",
    "trn": "Transportation",
    "ind": "Industrial",
}
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
        # ems metrics
        "capacity",
        "cost",
        "dr",
    ]

    def __init__(self, n: pypsa.Network, year: Optional[int] = None):
        self.n = n
        if year:
            self.year = year
        else:
            self.year = self.n.investment_periods[0]
        logger.info(f"Network {n} initialized to year {self.year}")

    def __iter__(self):
        for x in self.available_results:
            yield x

    def _is_valid_input(self, input: str) -> None:
        if input not in self.available_results:
            raise ValueError(
                f"{input} is not valid. Accepted inputs are {self.available_results}"
            )

    def _get_extractor(self, input: str) -> ResultsExtractor:
        self._is_valid_input(input)

        if input == "peakiness":
            return Peakiness(self.n, self.year)
        elif input == "ramping":
            return Ramping(self.n, self.year)
        elif input == "shed_season":
            return ShedSeason(self.n, self.year)
        elif input == "shed_days":
            return ShedDays(self.n, self.year)
        elif input == "shift_season":
            return ShiftSeason(self.n, self.year)
        elif input == "capacity":
            return Capacity(self.n)
        elif input == "cost":
            return Cost(self.n, self.year)
        elif input == "dr":
            return DemandResponse(self.n, self.year)
        else:
            raise NotImplementedError

    def get_dataframe(self, input: str) -> pd.DataFrame:
        extractor = self._get_extractor(input)
        return extractor.extract_dataframe()

    def get_datapoint(self, input: str, as_df: Optional[bool] = False) -> Any:
        logger.debug(f"Datapoint arguments are: input={input} | as_df={as_df}")

        extractor = self._get_extractor(input)
        return extractor.extract_datapoint(as_df=as_df)

    def plot(self, input: str, **kwargs) -> tuple[plt.figure, plt.axes]:
        extractor = self._get_extractor(input)

        fontsize = kwargs.get("fontsize", FONTSIZE)
        figsize = kwargs.get("figsize", FIGSIZE)

        return extractor.plot(figsize=figsize, fontsize=fontsize, **kwargs)


if __name__ == "__main__":
    network = "er20/western/networks/elec_s70_c4m_ec_lv1.0_1h-TCT_E-G.nc"

    n = pypsa.Network()

    ra = ResultsAccessor(NETWORKS + network)

    ra.get_datapoint("capacity", as_df=True)
    # ra.plot("cost", save="test.png")
