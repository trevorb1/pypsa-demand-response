# Multi-Sector Demand Response
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv) 
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14775955.svg)](https://doi.org/10.5281/zenodo.14775955)


## Introduction

This is the companion repository for the paper "Evaluating the Effectivness of Multi-Sector Demand Response".

## Data Availability 

All data generated for this study is from [PyPSA-USA](https://github.com/PyPSA/pypsa-usa/tree/master) and archived on [Zenodo](https://zenodo.org/records/14775955). 

## Running Instructions

Download and unzip Zenodo data and copy into `data/<region>/raw`. **Warning:** This is roughly 94GB of uncompressed data for all the network data! Once copied, run the data extraction script with the following command to populate the `data/<region>/processed` directory with summary results.

```
$ uv run analysis/extract_results.py 
```

Next, any notebook in the `analysis/` directory can be run to replicate results. 

## Result Viewing

As it takes a while to read in each netowork to process results, all summarized data and figures are given in the Zenodo deposits under the folder `data/<region>/processed`
