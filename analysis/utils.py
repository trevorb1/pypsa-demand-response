"""Utility functions and constants for analysis"""

import pandas as pd
from pathlib import Path
from typing import Optional

# scenario naming conventions (DO NOT CHANGE)
SECTORS = ["e", "t", "et"]
DR_PRICES = ["high", "mid", "low", "vlow"]
NG_PRICES = ["lgas", "mgas", "hgas"]
REGIONS = ["caiso", "new_england", "caiso_cc"]
METHODS = ["static", "dynamic"]
ERS = ["er0", "er5", "er10"]

# Plot fomatting (DO NOT CHANGE)
SECTOR_NICE_NAMES = {"e": "Electrical", "t": "Thermal", "et": "Electrical\nand Thermal"}
DR_PRICE_NICE_NAMES = {"vlow": "Very\nLow", "low": "Low", "mid": "Mid", "high": "High"}
NAT_GAS_NICE_NAMES = {
    "hgas": "High Nat. Gas Cost",
    "mgas": "Mid Nat. Gas Cost",
    "lgas": "Low Nat. Gas Cost",
}
ER_NICE_NAMES = {"er0": "ER0", "er5": "ER5", "er10": "ER10"}

# Path handling (DO NOT CHANGE)
DATA_DIR = Path("..", "data")


def get_scenario_name(
    scenario: str, sector: Optional[str] = None, dr_price: Optional[str] = None
) -> str:
    """Get the scenario name for a given NG price, sector, and DR price"""
    if scenario.startswith("er"):
        dimension = "er"
    elif scenario.endswith("gas"):
        dimension = "ng"
    else:
        raise ValueError(f"Invalid scenario: {scenario}")

    if dimension == "er":
        assert scenario in ERS, f"Invalid ER: {scenario}. Expected one of {ERS}"
    elif dimension == "ng":
        assert scenario in NG_PRICES, (
            f"Invalid NG price: {scenario}. Expected one of {NG_PRICES}"
        )
    else:
        raise ValueError(f"Invalid scenario: {scenario}")

    if not (sector or dr_price):
        return scenario
    assert sector and dr_price, "Sector and DR price must be provided"
    assert sector in SECTORS, f"Invalid sector: {sector}. Expected one of {SECTORS}"
    assert dr_price in DR_PRICES, (
        f"Invalid DR price: {dr_price}. Expected one of {DR_PRICES}"
    )
    return f"{sector}-{dr_price}-{scenario}"


def get_datapoint(
    region: str,
    scenario: str,
    result: str,
    method: Optional[str] = None,
    sector: Optional[str] = None,
    dr_price: Optional[str] = None,
) -> pd.DataFrame:
    """Get the datapoint for a given NG price, sector, and DR price"""
    assert region in REGIONS, f"Invalid region: {region}. Expected one of {REGIONS}"
    scenario = get_scenario_name(scenario, sector, dr_price)

    if method:
        assert method in METHODS, f"Invalid method: {method}. Expected one of {METHODS}"
        assert sector and dr_price, "Sector and DR price must be provided"
        p = Path(
            DATA_DIR,
            region,
            "processed",
            method,
            scenario,
            "datapoint",
            f"{result}.csv",
        )
    else:
        p = Path(DATA_DIR, region, "processed", scenario, "datapoint", f"{result}.csv")

    assert p.exists(), (
        f"Data point not found for:\nRegion={region}\nScenario={scenario}\nSector={sector}\nDr_Price={dr_price}\nMethod={method}\nResult={result}"
    )

    return pd.read_csv(p, index_col=0)


def get_dataframe(
    region: str,
    scenario: str,
    result: str,
    method: Optional[str] = None,
    sector: Optional[str] = None,
    dr_price: Optional[str] = None,
) -> pd.DataFrame:
    """Get the dataframe for a given NG price, sector, and DR price"""
    assert region in REGIONS, f"Invalid region: {region}. Expected one of {REGIONS}"
    scenario = get_scenario_name(scenario, sector, dr_price)

    if method:
        assert method in METHODS, f"Invalid method: {method}. Expected one of {METHODS}"
        assert sector and dr_price, "Sector and DR price must be provided"
        p = Path(
            DATA_DIR,
            region,
            "processed",
            method,
            scenario,
            "dataframe",
            f"{result}.csv",
        )
    else:
        p = Path(DATA_DIR, region, "processed", scenario, "dataframe", f"{result}.csv")

    assert p.exists(), (
        f"Dataframe not found for:\nRegion={region}\nScenario={scenario}\nSector={sector}\nDr_Price={dr_price}\nMethod={method}\nResult={result}"
    )

    return pd.read_csv(p, index_col=0)
