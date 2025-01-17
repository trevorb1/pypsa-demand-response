from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from datetime import datetime
from .extractor import ResultsExtractor

import logging

logger = logging.getLogger(__name__)


class Ramping(ResultsExtractor):
    def __init__(self, n, year=None):
        super().__init__(n, year)
        self.ramp_ts = self.get_daily_max_ramp()

    def extract_dataframe(self) -> pd.DataFrame:
        return self.ramp_ts.copy()

    def extract_datapoint(
        self, value: Optional[str] = None, as_df: Optional[bool] = False
    ) -> float:
        peak_0 = self.ramp_ts.at[0, "Absolute 3-hr Ramping"]
        peak_25 = self.ramp_ts.at[24, "Absolute 3-hr Ramping"]

        peak = round(peak_0, 2)
        rountine = round(peak_25, 2)
        extreme = round(peak_0 - peak_25, 2)

        if as_df:
            logger.debug("Returning datapoint ramping dataframe")
            df = pd.DataFrame(
                [
                    ["peak", peak],
                    ["rountine", rountine],
                    ["peakiness", extreme],
                ],
                columns=["metric", "value"],
            )
            return df

        if value == "peak":
            return peak
        elif value == "routine":
            return rountine
        else:  # extreme
            return extreme

    def plot(self, save: Optional[str] = None, **kwargs):
        fontsize = kwargs.get("fontsize", 12)
        figsize = kwargs.get("figsize", (20, 6))

        ramp_daily_ts = self.ramp_ts.sort_values(by="timestep").copy()
        ramp_max = ramp_daily_ts.at[0, "Absolute 3-hr Ramping"]
        ramp_rountine = ramp_daily_ts.at[24, "Absolute 3-hr Ramping"]

        ramp_max_day = ramp_daily_ts.at[0, "timestep"]
        ramp_rountine_day = ramp_daily_ts.at[24, "timestep"]

        ramp_daily_ts = ramp_daily_ts.set_index("timestep")[["Absolute 3-hr Ramping"]]
        ramp_daily_ts["Peak Ramping"] = ramp_max
        ramp_daily_ts["Routine Ramping"] = ramp_rountine

        fig, ax = plt.subplots(figsize=figsize)
        ramp_daily_ts.plot(
            ax=ax, xlabel="", color=["tab:blue", "tab:red", "tab:red"], legend=False
        )
        ax.set_ylabel(
            "Daily Maximum 3hr Absolute Net Load Ramping (MW)", fontsize=fontsize
        )
        ax.margins(x=0.01)
        # ax.legend(fontsize=15)
        # ax.set_ylim((0, ramp_max + 2000))
        ax.text(
            ramp_rountine_day,
            ramp_rountine + 1000,
            "Routine Ramping",
            fontsize=fontsize,
        )
        ax.text(ramp_max_day, ramp_max + 1000, "Peak Daily Ramp", fontsize=fontsize)
        ax.text(
            datetime(self.year, 1, 7),
            ramp_rountine + 500,
            "Extreme Ramping",
            fontsize=fontsize,
        )

        ax.scatter(ramp_max_day, ramp_max, color="k", s=25, zorder=9)
        ax.scatter(ramp_rountine_day, ramp_rountine, color="k", s=25, zorder=9)

        ax.annotate(
            text="",
            xy=(datetime(self.year, 1, 7), ramp_rountine),
            xytext=(datetime(self.year, 1, 7), (ramp_rountine - 2000)),
            arrowprops=dict(
                arrowstyle="-|>",
                mutation_scale=20,
                mutation_aspect=0.75,
                color="k",
                fill=True,
                linewidth=1.25,
            ),
        )

        ax.annotate(
            text="",
            xy=(datetime(self.year, 1, 7), ramp_max),
            xytext=(datetime(self.year, 1, 7), (ramp_max + 2000)),
            arrowprops=dict(
                arrowstyle="-|>",
                mutation_scale=20,
                mutation_aspect=0.75,
                color="k",
                fill=True,
                linewidth=1.25,
            ),
        )

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, ax
