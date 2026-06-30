# HEAD OVER HEELS

**H**eliophysics **E**vent **A**nalysis & **D**etection — **O**bserving **V**ariability **E**vents **R**evealing **H**ELiospheric **E**jecta and **E**xtreme **L**ocal **S**hocks

*(or, less acronym-tortured: a fluid-level plasma analysis pipeline for detecting CME/ICME signatures in MMS in-situ data)*

---

## Overview

HEAD OVER HEELS is a Python pipeline that ingests magnetic field (FGM), ion plasma (FPI), and electric field (EDP) data from NASA's **Magnetospheric Multiscale (MMS)** mission and automatically detects the in-situ signatures of **Interplanetary Coronal Mass Ejections (ICMEs)** as they sweep past the spacecraft.

The project started as a fluid-level analysis script for shock detection in a single MMS dataset (2018-02-12) and has been restructured into a modular detection pipeline built around the physical phase structure of a real ICME event.

This is **fluid-level** (moments-based) analysis, not full kinetic/distribution-function analysis — the algorithm works with density, bulk velocity, temperature moments, and magnetic/electric field vectors rather than raw particle distribution functions.

---

## Scientific motivation

A fast ICME arriving at a spacecraft produces a well-known three-part signature in the upstream solar wind:

1. **Shock front** — a sudden, simultaneous jump in magnetic field magnitude, ion density, and a drop in bulk flow speed, occurring when the ICME's leading edge moves faster than the local fast magnetosonic speed.
2. **Sheath** — a turbulent, compressed region immediately behind the shock, marked by elevated and fluctuating magnetic field (high δB/B).
3. **Magnetic cloud** — the ICME's magnetic flux rope itself: a smooth, large-scale rotation of the field vector (commonly seen as a Bz sign change), low plasma beta, and a relative density depression compared to the sheath.

The detector implemented here is a **3-phase state machine** that walks through the time series sample by sample, testing the relevant physical condition at each phase and only transitioning forward when the conditions are sustained for a minimum duration — this guards against false positives from short-lived turbulent spikes that don't represent a genuine ICME passage.

```
SOLAR_WIND  →  SHOCK  →  SHEATH  →  MAGNETIC_CLOUD  →  (back to) SOLAR_WIND
```

Each completed pass through the state machine is logged as a structured `ICMEEvent`, recording the shock arrival time, sheath onset, cloud onset/exit, density compression ratio, Bz rotation angle, and minimum plasma beta reached inside the cloud.

---

## Data sources

| Instrument | Quantity used | Role in detection |
|---|---|---|
| **FGM** (Fluxgate Magnetometer) | \|B\|, Bx, By, Bz | Shock jump, δB/B turbulence, Bz rotation |
| **FPI** (Fast Plasma Investigation, DIS) | Ni, Vx/Vy/Vz, T_para, T_perp | Density jump/depression, velocity drop, plasma beta |
| **EDP** (Electric Double Probe) | Ex, Ey, Ez | Supplementary field context around shock crossings |

Data can be sourced two ways:

- **Local CDF files** (via SpacePy) — for working with data already downloaded from the [MMS Science Data Center](https://lasp.colorado.edu/mms/sdc/public/).
- **Direct download via PySPEDAS** — auto-fetches the relevant time range from the SDC. *(Currently has a known dependency conflict — see [Known Issues](#known-issues) below.)*

---

## Pipeline architecture

```
head_over_heels.py
│
├── Config            — all thresholds, file paths, and physical constants in one place
├── DataLoader         — reads FGM/FPI/EDP from local CDF or PySPEDAS
├── Preprocessor       — smoothing, rolling baselines, plasma beta, Alfvén speed
├── Diagnostics        — bundles all derived physical quantities for the detector
├── ICMEDetector        — the 3-phase state machine; outputs a list of ICMEEvent
├── ICMEEvent           — structured record of one detected event's timing & parameters
├── Plotter            — multi-panel summary figure with phase-shaded backgrounds
└── main()              — orchestrates load → preprocess → detect → report → plot
```

**Design principle:** every threshold the detector relies on lives in `Config`, separated from the detection logic itself. This keeps the physics legible — anyone reviewing the code can see exactly what numeric criteria define a "shock," "sheath," or "cloud" without digging through the state machine.

### Key physical quantities computed

- **δB/B** — relative magnetic field fluctuation against a local rolling baseline (not a global daily mean, which would be biased by the event itself)
- **Plasma β** — thermal-to-magnetic pressure ratio, β = nkT / (B²/2μ₀), the canonical magnetic cloud identifier
- **Alfvén speed** — Va = B / √(μ₀ρ), used as physical context for the shock/sheath transition
- **Compression ratio** — Ni(downstream) / Ni(upstream), logged per event

---

## Current status

- [x] Modular pipeline structure (Config / Loader / Preprocessor / Diagnostics / Detector / Plotter)
- [x] 3-phase ICME state machine with minimum-duration guards against false positives
- [x] Plasma beta and Alfvén speed diagnostics
- [x] Multi-panel summary plot with phase-shaded backgrounds
- [x] Local CDF loading path (SpacePy) — functional
- [ ] PySPEDAS remote-download path — blocked by a `pytplot`/`bokeh`/`numpy` version conflict in the current environment (see below)
- [ ] Threshold tuning against the 2018-02-12 MMS dataset
- [ ] Validation against the [Richardson & Cane ICME catalog](http://www.srl.caltech.edu/ACE/ASC/DATA/level3/icmetable2.htm) and/or the [NASA Wind ICME catalog](https://wind.nasa.gov/ICMEindex.php)
- [ ] Cross-correlation with OMNIWeb Dst/SYM-H index to confirm geomagnetic storm context
- [ ] Multi-event batch processing across several MMS orbits

---

## Known issues

**PySPEDAS / pytplot / bokeh dependency conflict.** The `pytplot` package (a dependency of PySPEDAS's plotting utilities) currently breaks under `bokeh>=3.0` (API restructuring removed `bokeh.plotting.figure.Figure`), and downgrading to `bokeh==2.4.3` instead breaks under `numpy>=2.0` (which removed `np.bool8`). Until this three-way conflict is resolved upstream, **`Config.USE_PYSPEDAS` should be set to `False`** and data should be loaded from local CDFs via the SpacePy path, which has no such conflicts.

---

## Requirements

```
numpy
matplotlib
spacepy
pyspedas      # only required if USE_PYSPEDAS = True; see Known Issues
```

## Usage

1. Download the relevant MMS CDF files (FGM survey, FPI fast DIS moments, EDP fast DCE) for your time window of interest from the [MMS SDC](https://lasp.colorado.edu/mms/sdc/public/).
2. Set the file paths and detection thresholds in `Config`.
3. Run:

```bash
python head_over_heels.py
```

This produces:
- A console event report (timestamps, compression ratio, Bz rotation, minimum beta) for each detected ICME
- `head_over_heels_summary.png` — 6-panel overview with phase-shaded state machine output
- `head_over_heels_EDP.png` — supplementary electric field figure

---

## Background & references

The detection logic draws on the standard in-situ ICME signature literature, and the threshold design was informed by comparison against:

- The PySPEDAS / `mms-examples` ecosystem for MMS data handling conventions
- The Richardson & Cane and NASA Wind ICME catalogs, used as ground-truth event lists for future validation
- OMNIWeb / Dst-SYM-H index data, intended as an external cross-check linking in-situ detections to geomagnetic storm activity

---

## Author

Ana — M.Sc. in Nanotechnology Engineering (COPPE/UFRJ), background in computational nanomaterials modeling (DFT/FEM) and CubeSat payload work at Minerva Aerospace/UFRJ. This project is part of an ongoing transition toward space plasma physics and instrumentation work.
