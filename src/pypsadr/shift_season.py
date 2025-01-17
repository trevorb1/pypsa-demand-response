from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional
from datetime import datetime
from extractor import ResultsExtractor


class ShiftSeason(ResultsExtractor):

    def __init__(self, n, year=None):
        super().__init__(n, year)
        self.ramp_ts = self.get_daily_max_ramp()

    def extract_dataframe(self) -> pd.DataFrame:
        df = self.ramp_ts.copy()
        df = self._time_between_peaks(df)
        return self._get_season(df)

    def extract_datapoint(self, as_df: Optional[bool] = False) -> tuple[datetime, datetime] | pd.DataFrame:
        df = self.extract_dataframe()
        first_day = df.at[0, "timestep"].to_pydatetime()
        last_day = df.at[len(df) - 1, "timestep"].to_pydatetime()
        if as_df:
            df = pd.DataFrame(
                [
                    ["first_day", first_day],
                    ["last_day", last_day],
                ], 
                columns=["metric", "value"]
            )
            return df
        else:
            return (first_day, last_day)

    @staticmethod
    def _time_between_peaks(daily_ramp: pd.DataFrame) -> pd.DataFrame:
        """Gets time between top 25 loads"""

        shift_25 = daily_ramp.copy()
        shift_25 = shift_25.sort_values(
            "Absolute 3-hr Ramping", ascending=False
        ).reset_index(drop=True)
        shift_25 = shift_25.iloc[:26, :]
        shift_25 = shift_25.sort_values("timestep").reset_index(drop=True)
        diff = []
        for row in range(len(shift_25)):
            try:
                start = shift_25.loc[row, "timestep"]
                end = shift_25.loc[row + 1, "timestep"]
                diff.append(end - start)
            except KeyError:
                pass
        shift_25 = shift_25.iloc[:25]
        shift_25["diff"] = diff
        return shift_25.reset_index(drop=True)

    @staticmethod
    def _get_season(df_times: pd.DataFrame) -> pd.DataFrame:
        """Gets shortest span containing at least 20 days"""

        shift_season = df_times.copy()
        while len(shift_season) > 21:
            start_diff = abs(shift_season["diff"].iloc[0])
            end_diff = abs(shift_season["diff"].iloc[-1])
            if start_diff > end_diff:
                shift_season = shift_season.iloc[1:, :]
            else:
                shift_season = shift_season.iloc[:-1, :]
            shift_season = shift_season.reset_index(drop=True)

        return shift_season

    def plot(self, save: Optional[str] = None, **kwargs):

        fontsize = kwargs.get("fontsize", 12)
        figsize = kwargs.get("figsize", (20, 6))

        ramping = self.ramp_ts.sort_values("timestep", ascending=False).copy()
        ramping_sorted = self.ramp_ts

        peak = ramping_sorted.at[0, "Absolute 3-hr Ramping"]
        routine = ramping_sorted.at[24, "Absolute 3-hr Ramping"]

        ramping = ramping[["timestep", "Absolute 3-hr Ramping"]].copy()
        ramping["Top 25 Ramping Days"] = routine

        dates = self.extract_datapoint()
        start_date = dates[0]
        end_date = dates[1]
        mid_date = start_date + ((end_date - start_date) / 2)

        top_25 = ramping_sorted.iloc[:25]
        points_to_plot = [
            (x, y)
            for x, y in zip(
                top_25["timestep"].to_list(),
                top_25["Absolute 3-hr Ramping"].to_list(),
            )
        ]

        fig, ax = plt.subplots(figsize=figsize)
        ramping.set_index("timestep").plot(
            ax=ax, xlabel="", color=["tab:blue", "tab:red"]
        )

        ax.set_ylabel("Daily 3hr Absolute Net Load Ramping (MW)", fontsize=fontsize)
        ax.margins(x=0.01)
        ax.legend(fontsize=fontsize, loc="lower right")

        ax.text(mid_date, 22000, "Demand Response Shift Season", fontsize=fontsize)
        ax.annotate(
            text="",
            xy=(start_date, 20000),
            xytext=(end_date, 20000),
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
