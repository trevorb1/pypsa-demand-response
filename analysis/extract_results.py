"""Extracts relevent results from all model runs

Summarizes the key results from all networks. 
This data is then used in visualizations. 
Code is quite ugly as all the path handeling, but is what it is.
"""

from pypsadr import ResultsAccessor
import pypsa

from pathlib import Path
import shutil

NETWORK_DATA = "./data/networks"
PROCESSED_DATA = "./data/processed"

def save_results(n: pypsa.Network, scenario: str) -> None:
    # create root scenario folder
    processed_data = Path(PROCESSED_DATA, scenario)
    if processed_data.exists():
        shutil.rmtree(processed_data)
    processed_data.mkdir(parents=True)

    # directories for individual results
    datapoint_path = Path(PROCESSED_DATA, scenario, "datapoint")
    dataframe_path = Path(PROCESSED_DATA, scenario, "dataframe")
    plot_path = Path(PROCESSED_DATA, scenario, "plot")

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


if __name__ == "__main__":
    network_path = Path(NETWORK_DATA)

    for method in ("static", "dynamic"):
        network_data = Path(network_path, method)
        for scenario_dir in network_data.iterdir():
            scenario = scenario_dir.stem
            if scenario_dir.is_dir():
                # check only one interconnect
                num_interconnects = sum(
                    1 for item in scenario_dir.iterdir() if item.is_dir()
                )
                assert num_interconnects == 1, (
                    f"{num_interconnects} interconnects in {scenario_dir}"
                )
                for interconnect_dir in scenario_dir.iterdir():
                    # check correct interconnect name
                    assert interconnect_dir.stem in [
                        "western",
                        "eastern",
                        "texas",
                        "usa",
                    ]
                    # check only one network file
                    network_dir = Path(interconnect_dir, "networks")
                    num_networks = sum(
                        1 for item in network_dir.iterdir() if item.is_file()
                    )
                    assert num_networks == 1, (
                        f"{num_networks} networks in {network_dir}"
                    )
                    for network in network_dir.iterdir():
                        # check correct file extension
                        assert network.suffix == ".nc"
                        # generate intermediate results
                        print(f"reading {str(network)}")
                        n = pypsa.Network(str(network))
                        save_results(n, scenario)
