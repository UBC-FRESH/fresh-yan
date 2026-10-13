"""Legacy (superseded) harvested wood product (HWP) carbon accounting helpers.

Superseded by the corrected accounting in :mod:`fresh_yan.accounting` (stock-difference
ecosystem term, curve-derived product inflows, exact per-period survival). Retained for
reference only; nothing in this package imports this module.

Historical description: net system carbon stock / emission coefficient functions and
trackers (HWP first-order decay with half-lives, displacement factors), extracted from
``msc_walter_yan/util.py`` so this package is self-contained.

Conventions
-----------
The published trade-off and sensitivity experiments were produced under ws3 <= 1.0.4,
where ``inventory()`` reported start-of-period values. From ws3 1.0.5, inventory is
reported at the end of the period, and the original ``fm.inventory(..., age=...)`` calls
in these functions silently return zero. The coefficient functions and trackers below
therefore compute the start-of-period values directly (``_legacy_inventory_*``) so the
published experiments reproduce on current ws3 (verified against ws3 1.0.0; see
``planning/manuscript-handoff.md``).
"""

from __future__ import annotations

import math

import matplotlib.pyplot as plt
import pandas as pd


def _legacy_inventory_lookup(fm, period, dtype_key, age, yname):
    """Start-of-period inventory value for one stand: ``area(period, age) * curve(age)``.

    Reproduces the pre-ws3-1.0.5 semantics of
    ``fm.inventory(period, yname, age=age, dtype_keys=[dtype_key])`` (see module
    docstring).
    """
    dt = fm.dt(dtype_key)
    if dt is None:
        return 0.0
    ycomp = dt.ycomp(yname)
    if not ycomp or age not in dt._areas[period]:
        return 0.0
    return dt.area(period, age) * ycomp[age]


def _legacy_inventory_total(fm, period, yname):
    """Landscape total start-of-period inventory value (pre-ws3-1.0.5 semantics)."""
    total = 0.0
    for dt in fm.dtypes.values():
        ycomp = dt.ycomp(yname)
        if not ycomp:
            continue
        total += sum(dt.area(period, age) * ycomp[age] for age in dt._areas[period])
    return total


def cmp_c_cs(fm, path, expr, yname, half_life_solid_wood, half_life_paper, proportion_solid_wood, mask=None):
    """
    Compile objective function coefficient for total system carbon stock indicators (given ForestModel instance,
    leaf-to-root-node path, and expression to evaluate).
    """

    result = 0.

    # Calculate decay rates based on half-lives
    k_solid_wood = math.log(2) / half_life_solid_wood  # Decay rate for solid wood products (30-year half-life)
    k_paper = math.log(2) / half_life_paper  # Decay rate for paper (2-year half-life)

    # Define the allocation distribution
    proportion_paper = 1 - proportion_solid_wood

    # wood density (Kennedy, 1965)
    wood_density = 460

    # carbon content
    carbon_content = 0.5

    product_stock_dict = {}  # Dictionary to track product stock for each node across iterations

    for t, n in enumerate(path, start=1):

        d = n.data()
        node_id = id(n)  # or another unique identifier specific to your application

        # Track the ecosystem carbon stock
        if mask and not fm.match_mask(mask, d['_dtk']):
            continue
        result = _legacy_inventory_lookup(fm, t, d['_dtk'], d['_age'], yname)

        # Retrieve the last tuple of stocks from the dictionary
        last_stocks = next(reversed(product_stock_dict.values()), (0, 0))
        old_product_stock_solid_wood, old_product_stock_paper = last_stocks

        if fm.is_harvest(d['acode']):
            # Calculate new product stock
            new_product_carbon = fm.compile_product(t, expr, d['acode'], [d['dtk']], d['age'], coeff=False) * wood_density * carbon_content / 1000 # Convert kg to ton
            new_product_stock_solid_wood = new_product_carbon * proportion_solid_wood
            new_product_stock_paper = new_product_carbon * proportion_paper

            # Apply decay to old stocks and add new stocks
            # Apply decay to all stocks within the same period they're produced
            sum_product_stock_solid_wood = old_product_stock_solid_wood * (1 - k_solid_wood)**10 + new_product_stock_solid_wood
            sum_product_stock_paper = (old_product_stock_paper) * (1 - k_paper)**10 + new_product_stock_paper

        else:
            # If not harvesting, simply apply decay to the old product stocks
            sum_product_stock_solid_wood = old_product_stock_solid_wood * (1 - k_solid_wood)
            sum_product_stock_paper = old_product_stock_paper * (1 - k_paper)

        # Update product_stock_dict with the new sum product stocks for this node
        product_stock_dict[node_id] = (sum_product_stock_solid_wood, sum_product_stock_paper)

        ecosystem_stock = _legacy_inventory_lookup(fm, t, d['_dtk'], d['_age'], yname)
        result = ecosystem_stock + sum_product_stock_solid_wood + sum_product_stock_paper

    return result


def cmp_c_ce(fm, path, expr, half_life_solid_wood, half_life_paper, proportion_solid_wood, util_rate, displacement_factor_solid, credit, mask=None):

        """
        Compile objective function coefficient for net system carbon emission indicators
        (given ForestModel instance, leaf-to-root-node path, and expression to evaluate).
        """

        hwps_solid_pool = 0.
        hwps_paper_pool = 0.
        hwps_residue_pool = 0.
        hwps_solid_emission = 0.
        hwps_paper_emission = 0.
        hwps_residue_emission = 0.
        result = 0.

        # Calculate decay rates based on half-lives
        k_solid_wood = math.log(2) / half_life_solid_wood  # Decay rate for solid wood products (30-year half-life)
        k_paper = math.log(2) / half_life_paper  # Decay rate for paper (2-year half-life)

        # Define the allocation distribution
        proportion_paper = 1 - proportion_solid_wood

        # wood density (Kennedy, 1965)
        wood_density = 460

        # carbon content
        carbon_content = 0.5

        for t, n in enumerate(path, start=1):

            d = n.data()

            eco_emission = _legacy_inventory_lookup(fm, t, d['_dtk'], d['_age'], 'net_emission')

            # Track the new product stock
            if fm.is_harvest(d['acode']):
                # Calculate new product stock
                new_product_stock = fm.compile_product(t, expr, d['acode'], [d['dtk']], d['age'], coeff=False) * wood_density * carbon_content / 1000  # Convert kg to ton
            else:
                new_product_stock = 0.

            # Calculate product stock
            hwps_solid_pool = hwps_solid_pool * (1 - k_solid_wood)**10 + new_product_stock * util_rate * proportion_solid_wood
            hwps_paper_pool = hwps_paper_pool * (1 - k_paper)**10 + new_product_stock * util_rate * proportion_paper
            hwps_residue_pool = new_product_stock * (1.0 - util_rate)

            # Calculate prodcut emission
            hwps_solid_emission = hwps_solid_pool * (1- (1 - k_solid_wood)**10)
            hwps_paper_emission = hwps_paper_pool * (1- (1 - k_paper)**10)
            hwps_residue_emission = hwps_residue_pool
            hwps_sum_emission = hwps_solid_emission + hwps_paper_emission + hwps_residue_emission

            # Calculate Substitution Effect
            substitution_effect_solid = new_product_stock * util_rate * proportion_solid_wood * displacement_factor_solid * credit  # Emissions avoided by using HWPs
            substitution_effect_paper = 0.
            substitution_effect_residue = 0.
            substitution_effect_sum = substitution_effect_solid + substitution_effect_paper + substitution_effect_residue

            # Accumlate the total system carbon stock in each timestep
            result += (eco_emission + hwps_sum_emission - substitution_effect_sum) * -1 * 44 / 12
            # result += (eco_emission + hwps_sum_emission - substitution_effect_sum)

        return result


def track_system_stock(fm, half_life_solid_wood, half_life_paper, proportion_solid_wood, util_rate):

    hwps_solid_pool = 0.
    hwps_paper_pool = 0.
    hwps_residue_pool = 0.

    sys_pool_list = []
    eco_pool_list = []
    hwps_solid_pool_list = []
    hwps_paper_pool_list = []
    hwps_residue_pool_list = []
    hwps_sum_pool_list = []

    # Calculate decay rates based on half-lives
    k_solid_wood = math.log(2) / half_life_solid_wood
    k_paper = math.log(2) / half_life_paper

    # Define the allocation distribution
    proportion_paper = 1 - proportion_solid_wood

    # Constants
    wood_density = 460 #(Kennedy, 1965)
    carbon_content = 0.5

    for period in fm.periods:

        # Track Ecosystem Carbon Stock
        eco_pool = _legacy_inventory_total(fm, period, 'ecosystem')

        # Calculate new product stocks
        new_product_stock = fm.compile_product(period, 'totvol', acode='harvest') * wood_density * carbon_content / 1000 # Convert kg to ton
        # Calculate product stock
        hwps_solid_pool = hwps_solid_pool * (1 - k_solid_wood)**10 + new_product_stock * util_rate * proportion_solid_wood
        hwps_paper_pool = hwps_paper_pool * (1 - k_paper)**10 + new_product_stock * util_rate * proportion_paper
        hwps_residue_pool = new_product_stock * (1.0 - util_rate)
        hwps_sum_pool = hwps_solid_pool + hwps_paper_pool

        # Calculate total system carbon stock
        sys_pool = eco_pool + hwps_sum_pool

        # Update stock lists for this period
        sys_pool_list.append(sys_pool)
        eco_pool_list.append(eco_pool)
        hwps_solid_pool_list.append(hwps_solid_pool)
        hwps_paper_pool_list.append(hwps_paper_pool)
        hwps_residue_pool_list.append(hwps_residue_pool)
        hwps_sum_pool_list.append(hwps_sum_pool)

    # Prepare data for plotting
    data = {
        'period': fm.periods,
        'solid_wood': hwps_solid_pool_list,
        'paper': hwps_paper_pool_list,
        'residue': hwps_residue_pool_list,
        'sum_product': hwps_sum_pool_list,
        'ecosystem': eco_pool_list,
        'system': sys_pool_list
    }

    df = pd.DataFrame(data)

    return df


def track_system_emission(fm, half_life_solid_wood, half_life_paper, proportion_solid_wood, util_rate, displacement_factor_solid, credit):

    hwps_solid_pool = 0.
    hwps_paper_pool = 0.
    hwps_residue_pool = 0.
    hwps_solid_emission = 0.
    hwps_paper_emission = 0.
    hwps_residue_emission = 0.

    sys_emission_list = []
    eco_emission_list = []
    hwps_solid_emission_list = []
    hwps_paper_emission_list = []
    hwps_residue_emission_list = []
    hwps_sum_emission_list = []

    # Calculate decay rates based on half-lives
    k_solid_wood = math.log(2) / half_life_solid_wood
    k_paper = math.log(2) / half_life_paper

    # Define the allocation distribution
    proportion_paper = 1-proportion_solid_wood

    # Constants
    wood_density = 460 #(Kennedy, 1965)
    carbon_content = 0.5

    for period in fm.periods:

        # Calculate ecosytem emission
        eco_emission = _legacy_inventory_total(fm, period, 'net_emission') * 44 / 12

        # Calculate new product stocks
        new_product_stock = fm.compile_product(period, 'totvol', acode='harvest') * wood_density * carbon_content / 1000

        # Calculate total product stock
        hwps_solid_pool = hwps_solid_pool * (1 - k_solid_wood)**10 + new_product_stock * util_rate * proportion_solid_wood
        hwps_paper_pool = hwps_paper_pool * (1 - k_paper)**10 + new_product_stock * util_rate * proportion_paper
        hwps_residue_pool =  new_product_stock * (1- util_rate)

        # Calculate product emission
        hwps_solid_emission = hwps_solid_pool*(1- (1 - k_solid_wood)**10) * 44 / 12 #Convert from C to CO2
        hwps_paper_emission = hwps_paper_pool*(1- (1 - k_paper)**10) * 44 / 12 #Convert from C to CO2
        hwps_residue_emission = hwps_residue_pool * 44 / 12 #Convert from C to CO2

        hwps_sum_emission = hwps_solid_emission + hwps_paper_emission + hwps_residue_emission

        # Calculate Substitution Effect
        substitution_effect_solid = new_product_stock * util_rate * proportion_solid_wood * displacement_factor_solid * credit # Emissions avoided by using HWPs
        substitution_effect_paper = 0.
        substitution_effect_residue = 0.
        substitution_effect_sum = (substitution_effect_solid + substitution_effect_paper + substitution_effect_residue) * 44 / 12 #Convert from C to CO2

        # Calculate net system carbon emission
        sys_emission = (eco_emission + hwps_sum_emission - substitution_effect_sum)

        # Update stock lists for this period
        sys_emission_list.append(sys_emission)
        eco_emission_list.append(eco_emission)
        hwps_solid_emission_list.append(hwps_solid_emission)
        hwps_paper_emission_list.append(hwps_paper_emission)
        hwps_residue_emission_list.append(hwps_residue_emission)
        hwps_sum_emission_list.append(hwps_sum_emission)

    # Prepare data for plotting
    data = {
        'period': fm.periods,
        'solid_wood': hwps_solid_emission_list,
        'paper': hwps_paper_emission_list,
        'residue': hwps_residue_emission_list,
        'sum_product': hwps_sum_emission_list,
        'ecosystem': eco_emission_list,
        'system': sys_emission_list
    }

    df = pd.DataFrame(data)

    # Plotting
    _fig, ax = plt.subplots(1, 6, figsize=(20, 4))  # Adjusted for 5 subplots
    ax[0].bar(df.period, df.solid_wood)
    ax[0].set_title('Solid Wood Product CO2 Emission')
    ax[1].bar(df.period, df.paper)
    ax[1].set_title('Paper Product CO2 Emission')
    ax[2].bar(df.period, df.residue)
    ax[2].set_title('Residue CO2 Emission')
    ax[3].bar(df.period, df.sum_product)
    ax[3].set_title('Total Product CO2 Emission')
    ax[4].bar(df.period, df.ecosystem)
    ax[4].set_title('Net Ecosystem CO2 Emission')
    ax[5].bar(df.period, df.system)
    ax[5].set_title('Net System CO2 Emission')

    for a in ax:
        a.set_ylim(None, None)
        a.set_xlabel('Period')
        a.set_ylabel('CO2 (tons)')

    plt.tight_layout()

    return df
