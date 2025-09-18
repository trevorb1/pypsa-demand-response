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

        service_capacity = self._get_service_capacity(df)
        transport_capacity = self._get_transport_capacity(df)
        df = pd.concat([df, service_capacity, transport_capacity])

        # demand response will have np.inf
        return df.replace(np.inf, np.nan).dropna().groupby(level=0).sum()

    def extract_datapoint(self, **kwargs) -> pd.DataFrame:
        return (
            self.extract_dataframe()
            .reset_index(names="metric")
            .rename(columns={"p_nom_opt": "value"})
            .drop(columns=["p_nom"])
        )

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
        df = self.extract_dataframe()

        slicer = [x for x in slicer if x in df.index]
        df = df.loc[slicer].sum()

        return [sector, round(df.p_nom, 1), round(df.p_nom_opt, 1)]

    def _get_service_capacity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Creates new service category which is the sum of res and com"""

        service = df[df.index.str.startswith(("Residential", "Commercial"))].copy()
        # kinda awkward since nice names have already been applied
        idx = service.index.map(lambda x: x.split(" ")[1:]).map(lambda x: " ".join(x))
        service.index = idx
        service = service.groupby(level=0).sum()
        return service.rename(index={x: f"Service {x}" for x in service.index})

    def _get_transport_capacity(self, df: pd.DataFrame) -> pd.DataFrame:
        """Creates new transport category which is the sum of electric vehicle capacity."""
        transport = df[df.index.str.startswith(("Transport Electric"))].copy()
        # kinda awkward since nice names have already been applied
        idx = transport.index.map(lambda x: x.split(" ")[:2]).map(lambda x: " ".join(x))
        transport.index = idx
        return transport.groupby(level=0).sum()

    def plot(self, save=None, **kwargs) -> tuple[plt.figure, plt.axes]:
        # fontsize = kwargs.get("fontsize", 12)

        # custom figure size
        # figsize = kwargs.get("figsize", (20, 6))
        figsize = (10, 20)

        df = self.extract_dataframe()

        sectors = ["power", "residential", "commercial", "industrial", "transport"]

        fig, axs = plt.subplots(len(sectors), 1, figsize=figsize)

        ax = 0

        for sector in sectors:
            slicer = get_sector_slicer(sector)
            slicer = [x for x in slicer if x in df.index]
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
