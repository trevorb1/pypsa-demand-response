from __future__ import annotations

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from .extractor import ResultsExtractor
from .utils import get_sector_slicer
from .constants import (
    CARRIER_MAP,
)


class Capacity(ResultsExtractor):

    def __init__(self, n, year=None):
        super().__init__(n, year)

    def extract_dataframe(self) -> pd.DataFrame:

        dfs = []

        for c in ["Generator", "Link"]:
            installed = self._get_installed_capacity(c)
            optimal = self._get_optimial_capacity(c)
            dfs.append(installed.join(optimal, how="outer").fillna(0))

        df = pd.concat(dfs).dropna()

        # demand response will have np.inf
        return df.replace(np.inf, np.nan).dropna().groupby(level=0).sum()

    def extract_datapoint(self, **kwargs) -> pd.DataFrame:

        data = []

        for sector in ("power", "residential", "commercial", "transport", "industrial"):
            data.append(self._get_sector_capacity(sector))

        return pd.DataFrame(data, columns=["sector", "p_nom", "p_nom_opt"])

    def _get_installed_capacity(self, component: str) -> pd.DataFrame:

        for x in self.n.iterate_components([component]):
            df = x.df

        return (
            df["p_nom"]
            .rename(index=df.carrier)
            .rename(index=CARRIER_MAP)
            .groupby(level=0)
            .sum()
            .to_frame("p_nom")
        )

    def _get_optimial_capacity(self, component: str) -> pd.DataFrame:

        for x in self.n.iterate_components([component]):
            df = x.df

        return (
            df["p_nom_opt"]
            .rename(index=df.carrier)
            .rename(index=CARRIER_MAP)
            .groupby(level=0)
            .sum()
            .to_frame("p_nom_opt")
        )

    def _get_sector_capacity(self, sector: str) -> list[str | float]:

        slicer = get_sector_slicer(sector)

        df = self.extract_dataframe().loc[slicer].sum()

        return [sector, round(df.p_nom, 1), round(df.p_nom_opt, 1)]

    def plot(self, save=None, **kwargs) -> tuple[plt.figure, plt.axes]:

        fontsize = kwargs.get("fontsize", 12)

        # custom figure size
        # figsize = kwargs.get("figsize", (20, 6))
        figsize = (10, 20)

        df = self.extract_dataframe()

        sectors = ["power", "residential", "commercial", "industrial", "transport"]

        fig, axs = plt.subplots(len(sectors), 1, figsize=figsize)

        ax = 0

        for sector in sectors:

            slicer = get_sector_slicer(sector)
            sector_df = df.loc[slicer]

            name_map = {
                x: x.replace(f"{sector.capitalize()} ", "") for x in sector_df.index
            }
            sector_df = sector_df.rename(index=name_map)

            sector_df.plot(kind="barh", ax=axs[ax], title=f"{sector.capitalize()} (MW)")

            ax += 1

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, axs
