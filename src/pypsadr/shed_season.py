from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from datetime import datetime

from .extractor import ResultsExtractor

import logging

logger = logging.getLogger(__name__)


class ShedSeason(ResultsExtractor):
    def __init__(self, n, year=None):
        super().__init__(n, year)
        self.net_load = self.get_net_load(sorted=True)

    def extract_dataframe(self) -> pd.DataFrame:
        df = self.net_load.copy()
        df = self._time_between_peaks(df)
        return self._get_season(df)

    def extract_datapoint(
        self, as_df: Optional[bool] = False
    ) -> tuple[datetime, datetime] | pd.DataFrame:
        df = self.extract_dataframe()
        first_day = df.at[0, "timestep"].to_pydatetime()
        last_day = df.at[len(df) - 1, "timestep"].to_pydatetime()
        if as_df:
            logger.debug("Returning datapoint shed season dataframe")
            df = pd.DataFrame(
                [
                    ["first_day", first_day],
                    ["last_day", last_day],
                ],
                columns=["metric", "value"],
            )
            return df
        else:
            return (first_day, last_day)

    @staticmethod
    def _time_between_peaks(net_load: pd.DataFrame) -> pd.DataFrame:
        """Gets time between top 100 loads"""

        df = net_load.copy()

        df_times = df.iloc[:101, :].copy()  # keep end point
        df_times = df_times.sort_values("timestep").reset_index(drop=True)

        diff = []
        for row in range(len(df_times)):
            try:
                start = df_times.loc[row, "timestep"]
                end = df_times.loc[row + 1, "timestep"]
                diff.append(end - start)
            except KeyError:
                pass
        df_times = df_times.iloc[:100, :]  # remove end point
        df_times["diff"] = diff

        df_times["Top 100 Net-Load Hours"] = net_load.at[99, "Net_Load_MW"]

        return df_times

    @staticmethod
    def _get_season(df_times: pd.DataFrame) -> pd.DataFrame:
        """Gets chortest span containing at least 80 days"""

        load_shortest = df_times.copy()

        while len(load_shortest) > 81:
            start_diff = abs(load_shortest["diff"].iloc[0])
            end_diff = abs(load_shortest["diff"].iloc[-1])
            if start_diff > end_diff:
                load_shortest = load_shortest.iloc[1:, :]
            else:
                load_shortest = load_shortest.iloc[:-1, :]
            load_shortest = load_shortest.reset_index(drop=True)

        return load_shortest

    def plot(self, save: Optional[str] = None, **kwargs) -> tuple[plt.figure, plt.axes]:
        fontsize = kwargs.get("fontsize", 12)
        figsize = kwargs.get("figsize", (20, 6))

        net_load_sorted = self.net_load
        top_100 = net_load_sorted.at[100, "Net_Load_MW"]

        net_load_unsorted = self.get_net_load(sorted=False)
        net_load_unsorted["Top 100 Net Load Hours"] = top_100

        df = net_load_unsorted.set_index("timestep")[
            ["Net_Load_MW", "Top 100 Net Load Hours"]
        ].rename(columns={"Net_Load_MW": "Net Load"})

        dates = self.extract_datapoint()

        fig, ax = plt.subplots(figsize=figsize)
        df.plot(ax=ax, xlabel="", color=["tab:blue", "tab:red"])
        ax.set_ylabel("Net Load (MW)", fontsize=fontsize)
        ax.margins(x=0.01)
        ax.legend(fontsize=fontsize)
        # ax.text(
        #     datetime(self.year, 1, 7),
        #     top_100 + 2000,
        #     "Highest Probability Demand Response Events",
        #     fontsize=fontsize,
        # )

        mid_date = dates[0] + ((dates[1] - dates[0]) / 2)

        ax.text(mid_date, 6500, "Demand Response Shed Season", fontsize=fontsize)
        ax.annotate(
            text="",
            xy=(dates[0], 5000),
            xytext=(dates[1], 5000),
            arrowprops=dict(
                arrowstyle="<|-|>",
                mutation_scale=20,
                mutation_aspect=0.75,
                color="k",
                fill=True,
                linewidth=1.25,
            ),
        )
        ax.axvline(x=dates[0], color="k", linestyle="-", linewidth=3)
        ax.axvline(x=dates[1], color="k", linestyle="-", linewidth=3)

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, ax
