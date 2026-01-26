from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt

from .extractor import ResultsExtractor

import logging

logger = logging.getLogger(__name__)


class NetLoad(ResultsExtractor):
    def __init__(self, n, year=None):
        super().__init__(n, year)
        self.net_load = self.get_net_load(sorted=False)
        
    def extract_dataframe(self) -> pd.DataFrame:
        return self.net_load

    def extract_datapoint(self, **kwargs) -> pd.DataFrame:
        total_net_load = self.net_load.drop(columns=["timestep"]).sum()
        return total_net_load.to_frame(name="value").reset_index(names="metric")

    def plot(self, save=None, **kwargs) -> tuple[plt.figure, plt.axes]:
        
        figsize = (10, 6)
        
        net_load = self.net_load.set_index("timestep")["Net_Load_MW"]
        sorted_net_load = net_load.reset_index(drop=True).sort_values(ascending=False).reset_index(drop=True)
        
        fig, ax = plt.subplots(figsize=figsize, nrows=2, ncols=1)
        
        net_load.plot(ax=ax[0], xlabel="", ylabel="Net Load (MW)")
        sorted_net_load.plot(ax=ax[1])
        
        ax[0].set_title("Net Load")
        ax[0].set_ylabel("Net Load (MW)")
        ax[0].set_xlabel("Time")
        
        ax[1].set_title("Net Load Duration Curve")
        ax[1].set_ylabel("Net Load (MW)")
        ax[1].set_xlabel("Hour of Year")
        
        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")
        return fig, ax