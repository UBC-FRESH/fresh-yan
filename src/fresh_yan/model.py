"""TSA 24 model construction and carbon yield-curve helpers.

Parameters and the pool/flux definitions follow ``generate_c_curves_tsa24.ipynb`` in the
legacy ``msc_walter_yan`` repository.
"""

from __future__ import annotations

import pandas as pd
import ws3.forest

# --- Model parameters ---
BASE_YEAR = 2020
HORIZON = 20
PERIOD_LENGTH = 10
MAX_AGE = 1000
MODEL_NAME = "tsa24"
MODEL_PATH = "data/woodstock_model_files_tsa24"
CURVES_P = "curves/c_curves_p.pkl"
CURVES_F = "curves/c_curves_f.pkl"

# --- Carbon pools ---
biomass_pools = [
    "SoftwoodMerch", "SoftwoodFoliage", "SoftwoodOther", "SoftwoodCoarseRoots",
    "SoftwoodFineRoots", "HardwoodMerch", "HardwoodFoliage", "HardwoodOther",
    "HardwoodCoarseRoots", "HardwoodFineRoots",
]
dom_pools = [
    "AboveGroundVeryFastSoil", "BelowGroundVeryFastSoil", "AboveGroundFastSoil",
    "BelowGroundFastSoil", "MediumSoil", "AboveGroundSlowSoil", "BelowGroundSlowSoil",
    "SoftwoodStemSnag", "SoftwoodBranchSnag", "HardwoodStemSnag", "HardwoodBranchSnag",
]
emissions_pools = ["CO2", "CH4", "CO", "NO2"]
products_pools = ["Products"]
ecosystem_pools = biomass_pools + dom_pools
all_pools = biomass_pools + dom_pools + emissions_pools + products_pools

# --- Carbon fluxes ---
annual_process_fluxes = [
    "DecayDOMCO2Emission",
    "DeltaBiomass_AG",
    "DeltaBiomass_BG",
    "TurnoverMerchLitterInput",
    "TurnoverFolLitterInput",
    "TurnoverOthLitterInput",
    "TurnoverCoarseLitterInput",
    "TurnoverFineLitterInput",
    "DecayVFastAGToAir",
    "DecayVFastBGToAir",
    "DecayFastAGToAir",
    "DecayFastBGToAir",
    "DecayMediumToAir",
    "DecaySlowAGToAir",
    "DecaySlowBGToAir",
    "DecaySWStemSnagToAir",
    "DecaySWBranchSnagToAir",
    "DecayHWStemSnagToAir",
    "DecayHWBranchSnagToAir",
]

npp_fluxes = ["DeltaBiomass_AG", "DeltaBiomass_BG"]

decay_emissions_fluxes = [
    "DecayVFastAGToAir",
    "DecayVFastBGToAir",
    "DecayFastAGToAir",
    "DecayFastBGToAir",
    "DecayMediumToAir",
    "DecaySlowAGToAir",
    "DecaySlowBGToAir",
    "DecaySWStemSnagToAir",
    "DecaySWBranchSnagToAir",
    "DecayHWStemSnagToAir",
    "DecayHWBranchSnagToAir",
]

disturbance_production_fluxes = [
    "DisturbanceSoftProduction",
    "DisturbanceHardProduction",
    "DisturbanceDOMProduction",
]

disturbance_emissions_fluxes = [
    "DisturbanceMerchToAir",
    "DisturbanceFolToAir",
    "DisturbanceOthToAir",
    "DisturbanceCoarseToAir",
    "DisturbanceFineToAir",
    "DisturbanceVFastAGToAir",
    "DisturbanceVFastBGToAir",
    "DisturbanceFastAGToAir",
    "DisturbanceFastBGToAir",
    "DisturbanceMediumToAir",
    "DisturbanceSlowAGToAir",
    "DisturbanceSlowBGToAir",
    "DisturbanceSWStemSnagToAir",
    "DisturbanceSWBranchSnagToAir",
    "DisturbanceHWStemSnagToAir",
    "DisturbanceHWBranchSnagToAir",
]

all_fluxes = [
    "DisturbanceCO2Production",
    "DisturbanceCH4Production",
    "DisturbanceCOProduction",
    "DisturbanceBioCO2Emission",
    "DisturbanceBioCH4Emission",
    "DisturbanceBioCOEmission",
    "DecayDOMCO2Emission",
    "DisturbanceSoftProduction",
    "DisturbanceHardProduction",
    "DisturbanceDOMProduction",
    "DeltaBiomass_AG",
    "DeltaBiomass_BG",
    "TurnoverMerchLitterInput",
    "TurnoverFolLitterInput",
    "TurnoverOthLitterInput",
    "TurnoverCoarseLitterInput",
    "TurnoverFineLitterInput",
    "DecayVFastAGToAir",
    "DecayVFastBGToAir",
    "DecayFastAGToAir",
    "DecayFastBGToAir",
    "DecayMediumToAir",
    "DecaySlowAGToAir",
    "DecaySlowBGToAir",
    "DecaySWStemSnagToAir",
    "DecaySWBranchSnagToAir",
    "DecayHWStemSnagToAir",
    "DecayHWBranchSnagToAir",
    "DisturbanceMerchToAir",
    "DisturbanceFolToAir",
    "DisturbanceOthToAir",
    "DisturbanceCoarseToAir",
    "DisturbanceFineToAir",
    "DisturbanceDOMCO2Emission",
    "DisturbanceDOMCH4Emission",
    "DisturbanceDOMCOEmission",
    "DisturbanceMerchLitterInput",
    "DisturbanceFolLitterInput",
    "DisturbanceOthLitterInput",
    "DisturbanceCoarseLitterInput",
    "DisturbanceFineLitterInput",
    "DisturbanceVFastAGToAir",
    "DisturbanceVFastBGToAir",
    "DisturbanceFastAGToAir",
    "DisturbanceFastBGToAir",
    "DisturbanceMediumToAir",
    "DisturbanceSlowAGToAir",
    "DisturbanceSlowBGToAir",
    "DisturbanceSWStemSnagToAir",
    "DisturbanceSWBranchSnagToAir",
    "DisturbanceHWStemSnagToAir",
    "DisturbanceHWBranchSnagToAir",
]

grossgrowth_ag = [
    "DeltaBiomass_AG",
    "TurnoverMerchLitterInput",
    "TurnoverFolLitterInput",
    "TurnoverOthLitterInput",
]

grossgrowth_bg = [
    "DeltaBiomass_BG",
    "TurnoverCoarseLitterInput",
    "TurnoverFineLitterInput",
]

product_flux = [
    "DisturbanceSoftProduction",
    "DisturbanceHardProduction",
    "DisturbanceDOMProduction",
]

# --- Sum indicators used by the ws3 carbon yield curves ---
total_emission = decay_emissions_fluxes + disturbance_emissions_fluxes
gross_growth = grossgrowth_ag + grossgrowth_bg

sum_pools = ["ecosystem", "biomass", "DOM", "merch"]
sum_fluxes = ["total_emission", "gross_growth", "net_emission"]


def build_model(
    model_name: str = MODEL_NAME,
    model_path: str = MODEL_PATH,
    base_year: int = BASE_YEAR,
    horizon: int = HORIZON,
    period_length: int = PERIOD_LENGTH,
    max_age: int = MAX_AGE,
    section_units: str = "years",
) -> ws3.forest.ForestModel:
    """Build a forest-estate model with no actions scheduled (no-harvest case).

    Defaults are the TSA 24 model; other management units pass their own section stem
    and directory (see :func:`model_paths`).  ``section_units`` selects the Woodstock
    time-unit contract of the section files: ``"years"`` for the legacy TSA 24 files
    (ages 5..475 in years), or ``"periods"`` for femic ``export ws3-sections`` exports
    (``.are`` ages and ``.act`` timing are period indices; ws3 multiplies them by the
    period length on import).
    """
    if section_units not in ("years", "periods"):
        raise ValueError(f"section_units must be 'years' or 'periods', got '{section_units}'")
    convert = period_length if section_units == "periods" else None
    fm = ws3.forest.ForestModel(model_name=model_name,
                                model_path=model_path,
                                base_year=base_year,
                                horizon=horizon,
                                period_length=period_length,
                                max_age=max_age)
    fm.import_landscape_section()
    fm.import_areas_section(convert_periods_to_years=convert)
    fm.import_yields_section(convert_periods_to_years=convert)
    fm.import_actions_section(convert_periods_to_years=convert)
    fm.import_transitions_section(convert_periods_to_years=convert)
    fm.initialize_areas()
    fm.add_null_action()
    fm.reset_actions()
    fm.grow()
    return fm


def model_paths(tsa: str = MODEL_NAME, model_name: str | None = None,
                model_path: str | None = None) -> tuple[str, str]:
    """Resolve ``(model_name, model_path)`` for a management unit.

    The defaults reproduce the TSA 24 layout (``data/woodstock_model_files_tsa24``);
    other TSAs follow the femic section-export naming (``tsa<code>.{lan,are,yld,act,trn}``),
    so ``model_name`` defaults to the TSA label and ``model_path`` to
    ``data/woodstock_model_files_<tsa>``.
    """
    return model_name or tsa, model_path or f"data/woodstock_model_files_{tsa}"


def curves_dir_for(tsa: str = MODEL_NAME, curves_dir: str | None = None) -> str:
    """Resolve the curve directory (legacy ``curves`` for TSA 24; ``curves/<tsa>`` otherwise)."""
    return curves_dir or ("curves" if tsa == MODEL_NAME else f"curves/{tsa}")


def record_dir_for(tsa: str = MODEL_NAME, folder: str = "",
                   out_dir: str | None = None) -> str:
    """Resolve a record directory.

    TSA 24 keeps the legacy layout (``folder`` as given); other TSAs nest under
    ``results/<tsa>/<record>``.  An explicit ``out_dir`` always wins.
    """
    if out_dir:
        return out_dir
    if tsa == MODEL_NAME:
        return folder
    return f"results/{tsa}/{folder.rsplit('/', 1)[-1]}"


def disturbance_type_mapping(fm: ws3.forest.ForestModel,
                             harvest_acode: str = "harvest") -> list[dict[str, str]]:
    """CBM disturbance-type mapping used by ``to_cbm_sit`` (notebook cell 7).

    ``harvest_acode`` names the stand-replacing action in the model: ``"harvest"`` for
    the legacy TSA 24 sections, ``"cc"`` for the femic ``ws3-sections`` exports.
    """
    mapping = [
        {"user_dist_type": harvest_acode,
         "default_dist_type": "Clearcut harvesting without salvage"},
        {"user_dist_type": "fire", "default_dist_type": "Wildfire"},
    ]
    for dtype_key in fm.dtypes:
        fm.dt(dtype_key).last_pass_disturbance = (
            "fire" if dtype_key[2] == dtype_key[4] else harvest_acode
        )
    return mapping


def to_cbm_sit(fm: ws3.forest.ForestModel, mapping: list[dict[str, str]] | None = None):
    """Export the model to CBM Standard Import Tool (SIT) tables.

    libCBM requires non-negative yield values, but ws3's SIT conversion can emit tiny
    negative floating-point artifacts where a curve reaches exactly zero (the TSA 41
    export hits -8.9e-16 and fails libCBM's parser).  Artifacts with magnitude below
    the tolerance are clamped to 0; genuinely negative yields raise ``ValueError``.
    """
    if mapping is None:
        mapping = disturbance_type_mapping(fm)
    sit_config, sit_tables = fm.to_cbm_sit(
        softwood_volume_yname="swdvol",
        hardwood_volume_yname="hwdvol",
        admin_boundary="British Columbia",
        eco_boundary="Montane Cordillera",
        disturbance_type_mapping=mapping,
    )
    yld = sit_tables.get("sit_yield")
    if yld is not None:
        vcols = [c for c in yld.columns if c.startswith("v") and c[1:].isdigit()]
        if vcols:
            worst = float(yld[vcols].min().min())
            if worst < 0.0:
                if worst < -1e-9:
                    raise ValueError(
                        f"sit_yield contains negative values (min {worst:g}); "
                        "refusing to clamp")
                n = int((yld[vcols] < 0).to_numpy().sum())
                yld[vcols] = yld[vcols].clip(lower=0.0)
                print(f"to_cbm_sit: clamped {n} tiny negative yield value(s) to 0 "
                      f"(min {worst:g})", flush=True)
    return sit_config, sit_tables


def load_curves(path_p: str = CURVES_P, path_f: str = CURVES_F):
    """Load the carbon yield curves (generated by the legacy curve-generation notebook)."""
    return pd.read_pickle(path_p), pd.read_pickle(path_f)
