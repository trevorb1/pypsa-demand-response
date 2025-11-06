from __future__ import annotations

import pandas as pd
import matplotlib.pyplot as plt

from .extractor import ResultsExtractor
from .constants import CARRIER_MAP

import logging

logger = logging.getLogger(__name__)


class Cost(ResultsExtractor):
    def __init__(self, n, year=None):
        super().__init__(n, year)

    def extract_dataframe(self) -> pd.DataFrame:
        dfs = []
        for sector in ("res", "com", "ind", "trn"):
            dfs.append(self._get_mc_per_sector(sector))

        return pd.concat(dfs, axis=1).rename(columns=CARRIER_MAP).loc[self.year]

    def extract_datapoint(self, **kwargs) -> pd.DataFrame:
        mc = self.extract_dataframe()
        mc = mc.mean().to_frame(name="value").reset_index(names="metric")

        dr = self._get_dr_cost()

        objective = self.n.objective
        objective_adjusted = objective - dr

        obj = pd.DataFrame(
            [
                ["objective", objective],
                ["objective_adj", objective_adjusted],
            ],
            columns=["metric", "value"],
        )

        system_costs = pd.DataFrame(
            [
                ["capex", self._get_capex()],
                ["opex", self._get_opex()],
            ],
            columns=["metric", "value"],
        )

        return pd.concat([obj, mc, system_costs]).reset_index(drop=True)

    def _get_marginal_cost(self) -> pd.DataFrame:
        """Average marginal costs per carrier"""
        return (
            self.n.buses_t["marginal_price"]
            .rename(columns=self.n.buses.carrier)
            .T.groupby(level=0)
            .mean()
            .T
        )

    @staticmethod
    def _filter_carriers_in_sector(df: pd.DataFrame, sector: str) -> pd.DataFrame:
        """Filters out carriers

        Cant use load buses as transport dr is not attached directly at load
        """
        if sector in ("res", "com"):
            return df[[x for x in df if "-water-" not in x]].copy()
        elif sector in ("trn"):
            return df[["trn-elec-veh", "trn-lpg-veh"]].copy()
        else:
            return df.copy()

    def _get_mc_per_sector(self, sector: str) -> pd.DataFrame:
        """Get marginal costs in the sector"""
        df = self._get_marginal_cost()
        df = df[[x for x in df if sector in x and not x.endswith("-dr")]]
        return self._filter_carriers_in_sector(df, sector)

    def _get_dr_cost(self) -> float:
        """Gets costs incurred from demand response"""

        stores = self.n.stores[self.n.stores.index.str.endswith("-dr")]

        if stores.empty:
            return 0.0

        weights = self.n.snapshot_weightings.stores
        mc = stores.marginal_cost_storage
        e = self.n.stores_t["e"][stores.index]
        return e.mul(mc).mul(weights, axis=0).sum().sum()

    def _get_capex(self) -> float:
        """Gets capital expenditures"""

        stats = self.n.statistics()

        gens_and_links = stats.loc[(["Generator", "Link"]), :]
        return round(gens_and_links["Capital Expenditure"].fillna(0).sum().sum(), 6)

        # gens = self.n.generators.copy()
        # links = self.n.links.copy()

        # gens["p_nom_new"] = gens["p_nom_opt"] - gens["p_nom"]
        # links["p_nom_new"] = links["p_nom_opt"] - links["p_nom"]

        # gens_cost = gens["p_nom_new"].mul(gens["capital_cost"]).sum()
        # links_cost = links["p_nom_new"].mul(links["capital_cost"]).sum()

        # return round(gens_cost + links_cost, 6)

    def _get_opex(self) -> float:
        """Gets operational expenditures"""

        stats = self.n.statistics()

        gens_and_links = stats.loc[(["Generator", "Link"]), :]
        return round(gens_and_links["Operational Expenditure"].fillna(0).sum().sum(), 6)

        # opex_gens = self._get_gen_opex()

        # stores = [
        #     x for x in self.n.stores.index if x.endswith((" lpg", " coal", " oil"))
        # ]
        # marginal_cost = get_as_dense(self.n, "Store", "marginal_cost").loc[:, stores]
        # generation = self.n.stores_t["p"].loc[:, stores]
        # opex_non_gas = generation.mul(marginal_cost).sum().sum()

        # opex_gas = self._get_nat_gas_opex()

        # return round(opex_gens + opex_non_gas + opex_gas, 6)

    def plot(self, save=None, **kwargs) -> tuple[plt.figure, plt.axes]:
        fontsize = kwargs.get("fontsize", 12)
        figsize = kwargs.get("figsize", (20, 6))

        sectors = ["residential", "commercial", "industrial", "transport"]
        n_sectors = len(sectors)

        # figsize = (figsize[0], figsize[1] * n_sectors)
        figsize = (18, 18)

        df = self.extract_dataframe().resample("D").mean()

        fig, axs = plt.subplots(n_sectors, 1, figsize=figsize)

        ax = 0

        for sector in sectors:
            slicer = [x for x in df if x.startswith(f"{sector.capitalize()}")]
            sector_df = df[slicer].copy()
            sector_df["Average"] = sector_df.mean(axis=1)

            sector_df.plot(ax=axs[ax], title=f"{sector.capitalize()}")
            axs[ax].set_ylabel("($/MWh)", fontsize=fontsize)
            axs[ax].set_xlabel("")

            ###
            axs[ax].set_ylim(0, 200)
            ###

            ax += 1

        if save:
            fig.savefig(save, dpi=400, bbox_inches="tight")

        return fig, axs
