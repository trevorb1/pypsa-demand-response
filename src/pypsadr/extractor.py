from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Any
import matplotlib.pyplot as plt
import pypsa

import logging

logger = logging.getLogger(__name__)


class ResultsExtractor(ABC):
    ELEC_CARRIERS = ["res-elec", "com-elec", "ind-elec", "trn-elec-veh"]

    def __init__(self, n: pypsa.Network, year: Optional[int] = None):
        self.n = n
        self._year = year

    @property
    def year(self):
        return self._year

    @abstractmethod
    def extract_dataframe() -> pd.DataFrame:
        pass

    @abstractmethod
    def extract_datapoint(as_df: Optional[bool] = False) -> Any:
        """Return as df for standardized output"""
        pass

    @abstractmethod
    def plot(save: Optional[str] = None, **kwargs) -> tuple[plt.figure, plt.axes]:
        pass

    def get_net_load(self, sorted: Optional[bool] = True) -> pd.DataFrame:
        """Gets base net load dataframe"""

        loads = self._get_electical_load()
        solar = self._get_renewable_generation("solar")
        wind = self._get_renewable_generation("wind")
        df = pd.concat([loads, solar, wind], axis=1)
        df["Net_Load_MW"] = round(df.Load_MW - df.Wind_MW - df.Solar_MW, 2)

        df = df.loc[self.year].reset_index()

        if sorted:
            return df.sort_values("Net_Load_MW", ascending=False).reset_index(drop=True)
        else:
            return df

    def get_ramping(self) -> pd.DataFrame:
        """Gets base ramping dataframe"""

        net_load = self.get_net_load(sorted=False)

        ramp = (
            net_load[["timestep", "Net_Load_MW"]]
            .set_index("timestep")
            .rename(columns={"Net_Load_MW": "Absolute 3-hr Ramping"})
            .copy()
        )
        ramp = ramp.diff(periods=3)
        ramp["Absolute 3-hr Ramping"] = ramp["Absolute 3-hr Ramping"].abs()
        ramp["Net Load"] = net_load.set_index("timestep")["Net_Load_MW"]
        return ramp.dropna().reset_index(drop=False)

    def get_daily_max_ramp(self) -> pd.DataFrame:
        """Gets maximum ramping for each day in the year"""

        ramp = self.get_ramping()
        max_ramp = ramp.sort_values(by=["Absolute 3-hr Ramping"], ascending=False)
        max_ramp["day"] = max_ramp["timestep"].map(lambda x: f"{x.month}-{x.day}")
        return max_ramp.drop_duplicates("day").reset_index(drop=True)

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

    def get_emissions(self) -> pd.DataFrame:
        """Gets emissions dataframe"""
        stores = self.n.stores[self.n.stores.carrier.str.contains("co2")]
        stores_t = self.n.stores_t["e"][stores.index]
        return stores_t.max(axis=0).to_frame(name="Emissions_CO2_MT")
