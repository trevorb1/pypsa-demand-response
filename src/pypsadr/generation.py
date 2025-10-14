from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from .extractor import ResultsExtractor
from .utils import get_sector_slicer
from .constants import (
    CARRIER_MAP,
)

import logging

logger = logging.getLogger(__name__)


class Generation(ResultsExtractor):
    def __init__(self, n, year=None):
        super().__init__(n, year)

    def extract_dataframe(self) -> pd.DataFrame:
        dfs = []

        for c in ["Generator", "Link"]:
            dfs.append(self._get_generation(c))

        df = pd.concat(dfs, axis=1).dropna()
        # demand response will have np.inf
        return df.replace(np.inf, np.nan).T.groupby(level=0).sum().T

    def extract_datapoint(self, **kwargs) -> pd.DataFrame:
        return (
            self.extract_dataframe()
            .sum()
            .reset_index(name="value")
            .rename(columns={"index": "metric"})
        )

    def _get_generation(self, component: str) -> pd.DataFrame:
        for x in self.n.iterate_components([component]):
            static = x.static
            dynamic = x.dynamic

        if component == "Generator":
            df = dynamic["p"]
        elif component == "Link":
            df = dynamic["p1"].mul(-1)

        carriers = static.carrier.to_dict()

        return (
            df.rename(columns=carriers)
            .rename(columns=CARRIER_MAP)
            .T.groupby(level=0)
            .sum()
            .T
        )

    def plot(self, save=None, **kwargs) -> tuple[plt.figure, plt.axes]:
        # fontsize = kwargs.get("fontsize", 12)

        # custom figure size
        # figsize = kwargs.get("figsize", (20, 6))
        figsize = (10, 20)

        df = self.extract_datapoint().set_index("metric")

        sectors = ["power"]

        fig, axs = plt.subplots(len(sectors), 1, figsize=figsize)

        ax = 0

        for sector in sectors:
            slicer = get_sector_slicer(sector)
            slicer = [x for x in slicer if x in df.index]
            sector_df = df.loc[slicer]

            if len(sectors) > 1:
                sector_df.plot(kind="barh", ax=axs[ax], title=f"{sector.capitalize()} (MW)")
            else:
                sector_df.plot(kind="barh", ax=axs, title=f"{sector.capitalize()} (MW)")

            ax += 1

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, axs
