
from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Any
import matplotlib.pyplot as plt
import pypsa

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
    def extract_datapoint() -> Any:
        pass

    @abstractmethod
    def plot(
        save: Optional[str] = None, **kwargs
    ) -> tuple[plt.figure, plt.axes]:
        pass

    def get_net_load(self, sorted: Optional[bool] = True) -> pd.DataFrame:

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