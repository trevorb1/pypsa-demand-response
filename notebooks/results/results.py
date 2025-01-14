"""Results processor"""

from __future__ import annotations

import pypsa
import pandas as pd
import matplotlib.pyplot as plt

from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime

NICE_NAMES = {
    "res": "Residential",
    "com": "Commercial",
    "trn": "Transportation",
    "ind": "Industrial",
}
YEAR = 2019
NETWORKS = "./data/networks/"
FONTSIZE = 12


class ResultsAccessor:

    def __init__(self, n: str):
        self.n = pypsa.Network(n)

    @staticmethod
    def _is_valid_input(input: str) -> bool:
        if input in [
            "peakiness",
            "ramping",
            "shed_season",
            "shed_days",
            "shift_season",
        ]:
            return True
        else:
            return False

    def _get_extractor(self, input: str) -> ResultsExtractor:

        assert self._is_valid_input(input)

        if input == "peakiness":
            return Peakiness(self.n)
        elif input == "ramping":
            raise NotImplementedError
        elif input == "shed_season":
            return SheadSeason(self.n)
        elif input == "shed_days":
            raise NotImplementedError
        elif input == "shift_season":
            raise NotImplementedError
        else:
            raise NotImplementedError

    def get_dataframe(self, input: str) -> pd.DataFrame:
        Accessor = self._get_extractor(input)
        return Accessor.extract_dataframe()

    def get_datapoint(self, input: str) -> pd.DataFrame:
        Accessor = self._get_extractor(input)
        return Accessor.extract_datapoint()

    def plot(self, input: str, **kwargs) -> pd.DataFrame:
        Accessor = self._get_extractor(input)
        return Accessor.plot(**kwargs)


class ResultsExtractor(ABC):

    ELEC_CARRIERS = ["res-elec", "com-elec", "ind-elec", "trn-elec-veh"]

    def __init__(self, n: pypsa.Network):
        self.n = n

    @abstractmethod
    def extract_dataframe() -> pd.DataFrame:
        pass

    @abstractmethod
    def extract_datapoint() -> int | float | tuple[datetime, datetime]:
        pass

    @abstractmethod
    def plot(**kwargs) -> tuple[plt.figure, plt.axes]:
        pass

    def get_net_load(self, sorted: Optional[bool] = True) -> pd.DataFrame:

        loads = self._get_electical_load()
        solar = self._get_renewable_generation("solar")
        wind = self._get_renewable_generation("wind")
        df = pd.concat([loads, solar, wind], axis=1)
        df["Net_Load_MW"] = round(df.Load_MW - df.Wind_MW - df.Solar_MW, 2)

        df = df.loc[YEAR].reset_index()

        if sorted:
            return df.sort_values("Net_Load_MW", ascending=False).reset_index(drop=True)
        else:
            return df

    def _get_electical_load(self) -> pd.DataFrame:
        buses = self.n.links[
            self.n.links.carrier.isin(self.ELEC_CARRIERS)
        ].bus0.unique()
        links = self.n.links[
            self.n.links.bus0.isin(buses)
            & self.n.links.carrier.str.startswith(("res", "com", "ind", "trn"))
        ]
        return self.n.links_t["p0"][links.index].sum(axis=1).to_frame(name="Load_MW")

    def _get_renewable_generation(self, carrier: Optional[str] = None) -> pd.DataFrame:
        if carrier == "solar":
            gens = self.n.generators[self.n.generators.carrier.isin(["solar"])]
            name = "Solar_MW"
        elif carrier == "wind":
            gens = self.n.generators[
                self.n.generators.carrier.isin(["onwind", "offwind_floating"])
            ]
            name = "Wind_MW"
        else:
            gens = self.n.generators[
                self.n.generators.carrier.isin(["onwind", "offwind_floating", "solar"])
            ]
            name = "Renewable_MW"
        return self.n.generators_t["p"][gens.index].sum(axis=1).to_frame(name=name)


class Peakiness(ResultsExtractor):

    def __init__(self, n):
        super().__init__(n)
        self.net_load = self.get_net_load(sorted=True)

    def extract_dataframe(self):
        return self.net_load

    def extract_datapoint(self):
        peak_0 = self.net_load.at[0, "Net_Load_MW"]
        peak_100 = self.net_load.at[99, "Net_Load_MW"]
        return round(peak_0 - peak_100, 2)

    def plot(self, save: Optional[str] = None, **kwargs):

        peak_0 = self.net_load.at[0, "Net_Load_MW"]
        peak_100 = self.net_load.at[99, "Net_Load_MW"]
        date_0 = self.net_load.at[0, "timestep"]
        date_100 = self.net_load.at[99, "timestep"]

        load_ts = self.get_net_load(sorted=False)

        df = load_ts.set_index("timestep")[["Net_Load_MW"]].rename(
            columns={"Net_Load_MW": "Net Load"}
        )
        df["Peak Net Load"] = peak_0
        df["100th Highest Peak Load"] = peak_100

        fig, ax = plt.subplots(figsize=(20, 6))

        df.plot(ax=ax, xlabel="", color=["tab:blue", "tab:red", "tab:red"])

        for line in ax.lines:
            if line.get_label() == "Net Load":
                continue
            line.set_label("")

        ax.set_ylabel("Net Load", fontsize=FONTSIZE)
        ax.margins(x=0.01)
        ax.legend(fontsize=FONTSIZE)
        # ax.set_ylim((0, peak_0 + 5000))

        # ax.text(datetime.datetime(YEAR,1,1), 38000, "100th Highest Peak Net Load", fontsize=15)
        # ax.text(datetime.datetime(YEAR,1,1), 49000, "Peak Net Load", fontsize=15)

        ax.annotate(
            text="",
            xy=(datetime(YEAR, 2, 1), peak_0),
            xytext=(datetime(YEAR, 2, 1), peak_100),
            arrowprops=dict(
                arrowstyle="<|-|>",
                mutation_scale=20,
                mutation_aspect=0.75,
                color="k",
                fill=True,
                linewidth=1.25,
            ),
        )
        ax.text(datetime(YEAR, 2, 4), peak_0 - 3200, "Peakiness", fontsize=FONTSIZE)

        ax.scatter(date_0, peak_0, color="k", s=25, zorder=9)
        ax.text(date_0, peak_0 + 2000, "Peak", fontsize=FONTSIZE)

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, ax


class SheadSeason(ResultsExtractor):

    def __init__(self, n):
        super().__init__(n)
        self.net_load = self.get_net_load(sorted=True)

    def extract_dataframe(self) -> pd.DataFrame:
        df = self.net_load.copy()
        df = self._time_between_peaks(df)
        return self._get_season(df)

    def extract_datapoint(self) -> tuple[datetime, datetime]:
        df = self.extract_dataframe()
        first_day = df.at[0, "timestep"]
        last_day = df.at[len(df) - 1, "timestep"]
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

        while len(load_shortest) > 80:
            start_diff = load_shortest["diff"].iloc[0]
            end_diff = load_shortest["diff"].iloc[-1]
            if start_diff > end_diff:
                load_shortest = load_shortest.iloc[1:, :]
            else:
                load_shortest = load_shortest.iloc[:-1, :]
            load_shortest = load_shortest.reset_index(drop=True)

        return load_shortest

    def plot(self, save: Optional[str] = None, **kwargs) -> tuple[plt.figure, plt.axes]:

        net_load_sorted = self.net_load
        top_100 = net_load_sorted.at[100, "Net_Load_MW"]

        net_load_unsorted = self.get_net_load(sorted=False)
        net_load_unsorted["Top 100 Net Load Hours"] = top_100

        df = net_load_unsorted.set_index("timestep")[
            ["Net_Load_MW", "Top 100 Net Load Hours"]
        ].rename(columns={"Net_Load_MW": "Net Load"})

        dates = self.extract_datapoint()

        fig, ax = plt.subplots(figsize=(20, 6))
        df.plot(ax=ax, xlabel="", color=["tab:blue", "tab:red"])
        ax.set_ylabel("Net Load (MW)", fontsize=FONTSIZE)
        ax.margins(x=0.01)
        ax.legend(fontsize=FONTSIZE)
        ax.text(
            datetime(YEAR, 1, 7),
            top_100 + 2000,
            "Highest Probability Demand Response Events",
            fontsize=FONTSIZE,
        )

        mid_date = dates[0] + ((dates[1] - dates[0]) / 2)

        ax.text(mid_date, 1500, "Demand Response Shed Season", fontsize=13)
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


if __name__ == "__main__":

    network = "elec_s70_c4m_ec_lv1.0_3h_E-G.nc"

    ra = ResultsAccessor(NETWORKS + network)

    # print(ra.get_datapoint("shed_season"))
    ra.plot("shed_season", save="test.png")
