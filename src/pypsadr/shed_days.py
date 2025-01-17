from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from datetime import datetime

from .extractor import ResultsExtractor
from .shed_season import ShedSeason

import logging

logger = logging.getLogger(__name__)


class ShedDays(ResultsExtractor):
    """Shed Days just builds on ShedSeason"""

    def __init__(self, n, year=None):
        super().__init__(n, year)
        self.net_load = self.get_net_load(sorted=True)
        self.shead_season = ShedSeason(n, year)

    def extract_dataframe(self) -> pd.DataFrame:
        shed_season = (
            self.shead_season.extract_datapoint()
        )  # type tuple[datetime, datetime]
        days_in_top_100 = self._get_days_in_top_100()
        return self._date_in_season(shed_season, days_in_top_100)

    def extract_datapoint(
        self, as_df: Optional[bool] = False
    ) -> list[datetime] | pd.DataFrame:
        df = self.extract_dataframe()
        days = df["day"].unique().tolist()

        if as_df:
            logger.debug("Returning datapoint shed days dataframe")
            return pd.DataFrame(days, columns=["value"])
        else:
            return days

    def _get_days_in_top_100(self) -> pd.DataFrame:
        """Gets days in top 100 most likley days"""
        top_days = self.net_load.set_index("timestep").copy()
        top_days["day"] = top_days.index.map(lambda x: x.date())
        top_days = top_days.reset_index()
        return top_days.iloc[:100]

    @staticmethod
    def _date_in_season(
        shed_seaon: tuple[datetime, datetime], df: pd.DataFrame
    ) -> pd.DataFrame:
        """Filters out any data outside of shed season"""
        assert "day" in df.columns

        start = shed_seaon[0].date()
        end = shed_seaon[1].date()

        shed_days = df.copy()
        shed_days = shed_days[
            shed_days.day.map(lambda x: True if start <= x <= end else False)
        ]

        return shed_days

    def plot(self, save: Optional[str] = None, **kwargs) -> tuple[plt.figure, plt.axes]:
        fontsize = kwargs.get("fontsize", 12)
        figsize = kwargs.get("figsize", (20, 6))

        net_load_sorted = self.net_load
        top_100 = net_load_sorted.at[100, "Net_Load_MW"]
        peak = net_load_sorted.at[0, "Net_Load_MW"]

        net_load_unsorted = self.get_net_load(sorted=False)
        net_load_unsorted["Top 100 Net Load Hours"] = top_100

        df = net_load_unsorted.set_index("timestep")[
            ["Net_Load_MW", "Top 100 Net Load Hours"]
        ].rename(columns={"Net_Load_MW": "Net Load"})

        dates = self.shead_season.extract_datapoint()
        start_date = dates[0]
        end_date = dates[1]

        shed_days = self.net_load.iloc[0:99]
        num_shed_days = len(self.extract_datapoint())
        points_to_plot = [
            (x, y)
            for x, y in zip(
                shed_days["timestep"].to_list(), shed_days["Net_Load_MW"].to_list()
            )
        ]

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
        ax.text(
            datetime(self.year, 1, 7),
            peak - 4000,
            f"Shed Event Days = {num_shed_days}",
            fontsize=fontsize,
        )

        mid_date = start_date + ((end_date - start_date) / 2)

        ax.text(mid_date, 1500, "Demand Response Shed Season", fontsize=fontsize)
        ax.annotate(
            text="",
            xy=(start_date, 5000),
            xytext=(end_date, 5000),
            arrowprops=dict(
                arrowstyle="<|-|>",
                mutation_scale=20,
                mutation_aspect=0.75,
                color="k",
                fill=True,
                linewidth=1.25,
            ),
        )
        ax.axvline(x=start_date, color="k", linestyle="-", linewidth=3)
        ax.axvline(x=end_date, color="k", linestyle="-", linewidth=3)

        for point_x, point_y in points_to_plot:
            ax.scatter(point_x, point_y, color="k", s=5, zorder=9)

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, ax
