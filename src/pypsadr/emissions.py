from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from .extractor import ResultsExtractor

import logging

logger = logging.getLogger(__name__)


class Emissions(ResultsExtractor):
    def __init__(self, n, year=None):
        super().__init__(n, year)
        self.emissions = self.get_emissions()

    def extract_dataframe(self) -> pd.DataFrame:
        return self.emissions

    def extract_datapoint(
        self, value: Optional[str] = None, as_df: Optional[bool] = False
    ) -> float:
        return self.emissions.sum()

    def plot(self, save: Optional[str] = None, **kwargs):
        fontsize = kwargs.get("fontsize", 12)
        figsize = kwargs.get("figsize", (20, 6))

        sectors = {
            "pwr": "Power",
            "res": "Residential",
            "com": "Commercial",
            "ind": "Industrial",
            "trn": "Transport",
        }
        figsize = (18, 8)

        fig, ax = plt.subplots(1, 1, figsize=figsize)

        df = self.extract_dataframe()
        df.index = df.index.map(lambda x: x.split(" ")[1].split("-")[0]).map(sectors)
        df = df.groupby(level=0).sum()

        df.plot(ax=ax, title="Emissions", kind="bar")
        ax.set_ylabel("(T)", fontsize=fontsize)
        ax.set_xlabel("")

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, ax
