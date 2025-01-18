from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt

from .extractor import ResultsExtractor
from .constants import CARRIER_MAP

import logging

logger = logging.getLogger(__name__)


class DemandResponse(ResultsExtractor):
    def __init__(self, n, year=None):
        super().__init__(n, year)

    def extract_dataframe(self) -> pd.DataFrame:
        dr_stores = self.n.stores[self.n.stores.carrier.str.contains("-dr")]

        if not dr_stores.empty:
            stores = dr_stores.index
            return (
                self.n.stores_t["e"][stores]
                .abs()
                .rename(columns=self.n.stores.carrier)
                .rename(columns=CARRIER_MAP)
                .T.groupby(level=0)
                .sum()
                .T.loc[self.year]
            )
        else:
            logger.info("No demand response data")
            return pd.DataFrame()

    def extract_datapoint(self, **kwargs) -> pd.DataFrame:
        df = self.extract_dataframe()
        if df.empty:
            logger.info("No demand response data")
            return pd.DataFrame(columns=["metric", "value"])
        else:
            return df.sum().to_frame(name="value").reset_index(names="metric")

    def plot(self, save=None, **kwargs) -> tuple[plt.figure, plt.axes]:
        fontsize = kwargs.get("fontsize", 12)
        figsize = kwargs.get("figsize", (20, 6))

        df = self.extract_dataframe()

        if df.empty:
            fig, ax = plt.subplots()
            if save:
                fig.savefig(save, dpi=400, bbox_inches="tight")
            return fig, ax
        else:
            df = df.resample("D").mean()

        sectors = list(set([x.split(" ")[0] for x in df.columns]))
        n_sectors = len(sectors)

        figsize = (figsize[0], figsize[1] * n_sectors)

        fig, axs = plt.subplots(n_sectors, 1, figsize=figsize)

        ax = 0

        for sector in sectors:
            slicer = [x for x in df if x.startswith(sector)]
            sector_df = df[slicer].copy()

            sector_df.plot(ax=axs[ax], title=sector)
            axs[ax].set_ylabel("MWh", fontsize=fontsize)
            axs[ax].set_xlabel("")

            ax += 1

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, axs
