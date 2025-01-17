from constants import CARRIER_MAP


def get_sector_slicer(sector: str):
    if sector == "power":
        return _filter_pwr()
    elif sector == "residential":
        return _filter_res()
    elif sector == "commercial":
        return _filter_com()
    elif sector == "transport":
        return _filter_trn()
    elif sector == "industrial":
        return _filter_ind()
    else:
        raise ValueError


def _filter_res():
    exclusions = ["res-elec", "res-total-elec"]
    cars = [
        y
        for x, y in CARRIER_MAP.items()
        if x.startswith("res") and x not in exclusions and not x.endswith("-dr")
    ]
    return list(set(cars))


def _filter_com():
    exclusions = ["com-elec", "com-total-elec"]
    cars = [
        y
        for x, y in CARRIER_MAP.items()
        if x.startswith("com") and x not in exclusions and not x.endswith("-dr")
    ]
    return list(set(cars))


def _filter_ind():
    exclusions = ["ind-elec"]
    cars = [
        y
        for x, y in CARRIER_MAP.items()
        if x.startswith("ind") and x not in exclusions and not x.endswith("-dr")
    ]
    return list(set(cars))


def _filter_trn():
    cars = [CARRIER_MAP[x] for x in ["trn-elec-veh", "trn-lpg-veh"]]
    return list(set(cars))


def _filter_pwr():
    cars = [
        CARRIER_MAP[x]
        for x in [
            "biomass",
            "CCGT",
            "CCGT-95CCS",
            "coal",
            "geothermal",
            "hydro",
            "nuclear",
            "offwind_floating",
            "OCGT",
            "onwind",
            "solar",
            "waste",
            "oil",
        ]
    ]
    return list(set(cars))
