"""Extracts relevent results from all model runs

Summarizes the key results from all networks.
This data is then used in visualizations.
Code is quite ugly as all the path handeling, but is what it is.
"""

from pypsadr import ResultsAccessor
import pypsa
import matplotlib.pyplot as plt
from pathlib import Path
import shutil

import logging

logging.basicConfig(level=logging.INFO)

DATA_DIR = "./data"

REGIONS = ["caiso", "new_england"]
SCENARIOS = ["static", "dynamic"]
BASELINES = ["lgas", "mgas", "hgas"]


def save_results(n: pypsa.Network, save_dir: Path | str) -> None:
    """Saves results to a directory"""
    if isinstance(save_dir, str):
        save_dir = Path(save_dir)

    # create root scenario folder
    save_dir.mkdir(parents=True, exist_ok=True)
    if save_dir.exists():
        shutil.rmtree(save_dir)
    save_dir.mkdir(parents=True)

    logging.info(f"Saving results to {save_dir}")

    # directories for individual results
    datapoint_path = Path(save_dir, "datapoint")
    dataframe_path = Path(save_dir, "dataframe")
    plot_path = Path(save_dir, "plot")

    datapoint_path.mkdir(parents=True)
    dataframe_path.mkdir(parents=True)
    plot_path.mkdir(parents=True)

    ra = ResultsAccessor(n)

    for result in ra:
        dp = ra.get_datapoint(result, as_df=True)
        df = ra.get_dataframe(result)
        fig, _ = ra.plot(result)

        dp.to_csv(Path(datapoint_path, f"{result}.csv"), index=False)
        df.to_csv(Path(dataframe_path, f"{result}.csv"), index=True)
        fig.savefig(Path(plot_path, f"{result}.png"), dpi=400, bbox_inches="tight")

        plt.close()


if __name__ == "__main__":
    # Process baseline data without DR
    for region in REGIONS:
        for baseline in BASELINES:
            network_dir = Path(DATA_DIR, region, "raw", baseline, "networks")
            save_dir = Path(DATA_DIR, region, "processed", baseline)
            # check only one network file
            num_networks = sum(1 for item in network_dir.iterdir() if item.is_file())
            assert num_networks == 1, f"{num_networks} networks in {network_dir}"
            # save results
            for network in network_dir.iterdir():
                n = pypsa.Network(str(network))
                save_results(n, save_dir)

    # # Process DR data
    for region in REGIONS:
        for scenario in SCENARIOS:
            scenario_dir = Path(DATA_DIR, region, "raw", scenario)
            for model_run in scenario_dir.iterdir():
                run_name = model_run.stem
                network_dir = Path(model_run, "networks")
                save_dir = Path(DATA_DIR, region, "processed", scenario, run_name)
                # check only one network file
                num_networks = sum(
                    1 for item in network_dir.iterdir() if item.is_file()
                )
                assert num_networks == 1, f"{num_networks} networks in {network_dir}"
                # save results
                for network in network_dir.iterdir():
                    n = pypsa.Network(str(network))
                    save_results(n, save_dir)
