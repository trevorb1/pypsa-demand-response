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
            raise NotImplementedError
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
    def extract_datapoint() -> float:
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
        self.df = self.get_net_load(sorted=True)

    def extract_dataframe(self):
        return self.df

    def extract_datapoint(self):
        peak_0 = self.df.at[0, "Net_Load_MW"]
        peak_100 = self.df.at[99, "Net_Load_MW"]
        return round(peak_0 - peak_100, 2)

    def plot(self, save: Optional[str] = None, **kwargs):

        peak_0 = self.df.at[0, "Net_Load_MW"]
        peak_100 = self.df.at[99, "Net_Load_MW"]
        date_0 = self.df.at[0, "timestep"]
        date_100 = self.df.at[99, "timestep"]

        net_load = self.get_net_load(sorted=False)

        df = net_load[["Net_Load_MW"]].rename(columns={"Net_Load_MW": "Net Load"})
        df["Peak Net Load"] = peak_0
        df["100th Highest Peak Load"] = peak_100

        fig, ax = plt.subplots(figsize=(20, 6))

        df.plot(ax=ax, xlabel="", color=["tab:blue", "tab:red", "tab:red"])

        for line in ax.lines:
            if line.get_label() == "Net Load":
                continue
            line.set_label("")

        ax.set_ylabel("Net Load", fontsize=12)
        ax.margins(x=0.01)
        ax.legend(fontsize=15)
        ax.set_ylim((0, peak_0 + 5000))

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
        ax.text(datetime(YEAR, 2, 4), peak_0 - 3200, "Peakiness", fontsize=15)

        # ax.plot(date_0, peak_0, "o", color="k", markersize=5)
        # ax.text(date_0, peak_0 + 2000, "Peak", fontsize=15)

        if save:
            fig.savefig(save, dpi=400)

        return fig, ax


if __name__ == "__main__":

    network = "elec_s70_c4m_ec_lv1.0_3h_E-G.nc"

    ra = ResultsAccessor(NETWORKS + network)

    ra.plot("peakiness", save="test.png")
