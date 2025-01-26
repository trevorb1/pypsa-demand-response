from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from datetime import datetime
from .extractor import ResultsExtractor

import logging

logger = logging.getLogger(__name__)


class Peakiness(ResultsExtractor):
    def __init__(self, n, year=None):
        super().__init__(n, year)
        self.net_load = self.get_net_load(sorted=True)

    def extract_dataframe(self) -> pd.DataFrame:
        return self.net_load.set_index("timestep")

    def extract_datapoint(
        self, value: Optional[str] = None, as_df: Optional[bool] = False
    ) -> float:
        peak_0 = self.net_load.at[0, "Net_Load_MW"]
        peak_100 = self.net_load.at[99, "Net_Load_MW"]

        peak = round(peak_0, 2)
        rountine = round(peak_100, 2)
        peakiness = round(peak_0 - peak_100, 2)

        if as_df:
            logger.debug("Returning datapoint peakiness dataframe")
            df = pd.DataFrame(
                [
                    ["peak", peak],
                    ["rountine", rountine],
                    ["peakiness", peakiness],
                ],
                columns=["metric", "value"],
            )
            return df

        if value == "peak":
            logger.debug("Returning max peak")
            return peak
        elif value == "routine":
            logger.debug("Returning rountine peak")
            return rountine
        else:
            logger.debug("Returning peakiness")
            return peakiness

    def plot(self, save: Optional[str] = None, **kwargs):
        fontsize = kwargs.get("fontsize", 12)
        figsize = kwargs.get("figsize", (20, 6))

        peak_0 = self.net_load.at[0, "Net_Load_MW"]
        peak_100 = self.net_load.at[99, "Net_Load_MW"]
        date_0 = self.net_load.at[0, "timestep"]
        # date_100 = self.net_load.at[99, "timestep"]

        load_ts = self.get_net_load(sorted=False)

        df = load_ts.set_index("timestep")[["Net_Load_MW"]].rename(
            columns={"Net_Load_MW": "Net Load"}
        )
        df["Peak Net Load"] = peak_0
        df["100th Highest Peak Load"] = peak_100

        fig, ax = plt.subplots(figsize=figsize)

        df.plot(ax=ax, xlabel="", color=["tab:blue", "tab:red", "tab:red"])

        for line in ax.lines:
            if line.get_label() == "Net Load":
                continue
            line.set_label("")

        ax.set_ylabel("Net Load", fontsize=fontsize)
        ax.margins(x=0.01)
        ax.legend(fontsize=fontsize)

        ax.annotate(
            text="",
            xy=(datetime(self.year, 2, 1), peak_0),
            xytext=(datetime(self.year, 2, 1), peak_100),
            arrowprops=dict(
                arrowstyle="<|-|>",
                mutation_scale=20,
                mutation_aspect=0.75,
                color="k",
                fill=True,
                linewidth=1.25,
            ),
        )
        ax.text(
            datetime(self.year, 2, 4), peak_0 - 3200, "Peakiness", fontsize=fontsize
        )

        ax.scatter(date_0, peak_0, color="k", s=25, zorder=9)
        ax.text(date_0, peak_0 + 2000, "Peak", fontsize=fontsize)

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, ax
