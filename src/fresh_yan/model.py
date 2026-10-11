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

sum_pools = ["ecosystem", "biomass", "DOM"]
sum_fluxes = ["total_emission", "gross_growth", "net_emission"]


def build_model(
    model_name: str = MODEL_NAME,
    model_path: str = MODEL_PATH,
    base_year: int = BASE_YEAR,
    horizon: int = HORIZON,
    period_length: int = PERIOD_LENGTH,
    max_age: int = MAX_AGE,
) -> ws3.forest.ForestModel:
    """Build the TSA 24 ForestModel with no actions scheduled (no-harvest case).

    The Woodstock-format files for this project use stand ages in *years* (5..475),
    so no ``convert_periods_to_years`` is needed.
    """
    fm = ws3.forest.ForestModel(model_name=model_name,
                                model_path=model_path,
                                base_year=base_year,
                                horizon=horizon,
                                period_length=period_length,
                                max_age=max_age)
    fm.import_landscape_section()
    fm.import_areas_section()
    fm.import_yields_section()
    fm.import_actions_section()
    fm.import_transitions_section()
    fm.initialize_areas()
    fm.add_null_action()
    fm.reset_actions()
    fm.grow()
    return fm


def disturbance_type_mapping(fm: ws3.forest.ForestModel) -> list[dict[str, str]]:
    """CBM disturbance-type mapping used by ``to_cbm_sit`` (notebook cell 7)."""
    mapping = [
        {"user_dist_type": "harvest", "default_dist_type": "Clearcut harvesting without salvage"},
        {"user_dist_type": "fire", "default_dist_type": "Wildfire"},
    ]
    for dtype_key in fm.dtypes:
        fm.dt(dtype_key).last_pass_disturbance = (
            "fire" if dtype_key[2] == dtype_key[4] else "harvest"
        )
    return mapping


def to_cbm_sit(fm: ws3.forest.ForestModel, mapping: list[dict[str, str]] | None = None):
    """Export the model to CBM Standard Import Tool (SIT) tables."""
    if mapping is None:
        mapping = disturbance_type_mapping(fm)
    return fm.to_cbm_sit(softwood_volume_yname="swdvol",
                         hardwood_volume_yname="hwdvol",
                         admin_boundary="British Columbia",
                         eco_boundary="Montane Cordillera",
                         disturbance_type_mapping=mapping)


def load_curves(path_p: str = CURVES_P, path_f: str = CURVES_F):
    """Load the carbon yield curves (generated by the legacy curve-generation notebook)."""
    return pd.read_pickle(path_p), pd.read_pickle(path_f)
