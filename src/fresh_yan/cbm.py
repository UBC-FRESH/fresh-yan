"""libCBM and ws3-libCBM comparison utilities.

Extracted from ``msc_walter_yan/util.py`` (the original MSc modelling repository)
so that this package is self-contained.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import ws3.core


def run_cbm(sit_config, sit_tables, n_steps):
    import inspect

    from libcbm.input.sit import sit_cbm_factory, sit_reader
    from libcbm.model.cbm import cbm_simulator
    from libcbm.model.cbm.cbm_output import CBMOutput
    sit_data = sit_reader.parse(sit_classifiers=sit_tables['sit_classifiers'],
                                sit_disturbance_types=sit_tables['sit_disturbance_types'],
                                sit_age_classes=sit_tables['sit_age_classes'],
                                sit_inventory=sit_tables['sit_inventory'],
                                sit_yield=sit_tables['sit_yield'],
                                sit_events=sit_tables['sit_events'],
                                sit_transitions=sit_tables['sit_transitions'],
                                sit_eligibilities=None)
    sit = sit_cbm_factory.initialize_sit(sit_data=sit_data, config=sit_config)
    classifiers, inventory = sit_cbm_factory.initialize_inventory(sit)
    cbm_output = CBMOutput(classifier_map=sit.classifier_value_names,
                           disturbance_type_map=sit.disturbance_name_map)
    with sit_cbm_factory.initialize_cbm(sit) as cbm:
        # Apply rule-based disturbance events and transition rules from the SIT input
        rule_based_processor = sit_cbm_factory.create_sit_rule_based_processor(sit, cbm)
        # Spin up the CBM inventory and run it through the requested timesteps.
        simulate_kwargs = {
            "n_steps": n_steps,
            "classifiers": classifiers,
            "inventory": inventory,
            "pre_dynamics_func": rule_based_processor.pre_dynamics_func,
            "reporting_func": cbm_output.append_simulation_result,
        }
        if "backend_type" in inspect.signature(cbm_simulator.simulate).parameters:
            from libcbm.storage.backends import BackendType
            simulate_kwargs["backend_type"] = BackendType.numpy
        cbm_simulator.simulate(cbm, **simulate_kwargs)
    return cbm_output


def plugin_c_curves(fm, c_curves_p, c_curves_f, pools, fluxes):
    """Plug the generated carbon yield curves into the model's dtypes.

    Works for both section-export layouts: legacy TSA 24 sections (yields registered
    under ``('?', '?', AU, '?', curve)`` wildcard masks) and femic ``export
    ws3-sections`` exports (yields registered under the full dtype key).
    """
    # Dictionary to track registered curves for each dtype_key
    registered_curves = {}

    for dtype_key in fm.dtypes:
        dt = fm.dt(dtype_key)

        # Locate the yield entry to plug the carbon curves into.  Mirror ws3's own mask
        # matching and prefer the most specific entry that carries curves.
        target = None
        best_wild = None
        for _mask, _ytype, curves in fm.yields:
            if not curves or not fm.match_mask(_mask, dtype_key):
                continue
            wild = sum(1 for m in _mask if m == '?')
            if best_wild is None or wild < best_wild:
                best_wild, target = wild, (_mask, _ytype, curves)
        if target is None:
            raise ValueError(
                f"no yield registry entry with curves for dtype {' '.join(dtype_key)}")
        _mask, _ytype, curves = target
        print('found match for mask', _mask, flush=True)

        # Initialize the tracking of registered curves for the dtype_key if not already done
        if dtype_key not in registered_curves:
            registered_curves[dtype_key] = set()

        # Register pool curves
        pool_data = c_curves_p.loc[' '.join(dtype_key)]
        for yname in pools:
            if yname not in registered_curves[dtype_key]:  # skip if already registered
                points = list(zip(pool_data.index.values, pool_data[yname], strict=False))
                curve = fm.register_curve(ws3.core.Curve(yname,
                                                         points=points,
                                                         type='a',
                                                         is_volume=False,
                                                         xmax=fm.max_age,
                                                         period_length=fm.period_length))
                curves.append((yname, curve))
                dt.add_ycomp('a', yname, curve)

                # Mark the curve as registered
                registered_curves[dtype_key].add(yname)

        # Register flux curves
        flux_data = c_curves_f.loc[' '.join(dtype_key)]
        for yname in fluxes:
            if yname not in registered_curves[dtype_key]:  # skip if already registered
                points = list(zip(flux_data.index.values, flux_data[yname], strict=False))
                curve = fm.register_curve(ws3.core.Curve(yname,
                                                         points=points,
                                                         type='a',
                                                         is_volume=False,
                                                         xmax=fm.max_age,
                                                         period_length=fm.period_length))
                curves.append((yname, curve))
                dt.add_ycomp('a', yname, curve)

                # Mark the curve as registered
                registered_curves[dtype_key].add(yname)


def compare_ws3_libcbm(
    fm, cbm_output, disturbance_type_mapping, biomass_pools, dom_pools,
    total_emission, gross_growth, plots, filename=None
):
    eco_pools = biomass_pools + dom_pools
    pi = cbm_output.classifiers.to_pandas().merge(
        cbm_output.pools.to_pandas(),
        left_on=["identifier", "timestep"],
        right_on=["identifier", "timestep"]
    )
    fi = cbm_output.classifiers.to_pandas().merge(
        cbm_output.flux.to_pandas(),
        left_on=["identifier", "timestep"],
        right_on=["identifier", "timestep"]
    )

    # Summarize CBM data. Sample libCBM at the END of each period (timestep 10p)
    # to match the ws3 period-p inventories; the previous start-of-period sampling
    # (timestep 10(p-1)+1) shifted the whole libCBM series one period earlier and
    # inflated every stock and flux difference (replay validation pinned t = 10p
    # as the age-exact pairing; see planning/ws3-libcbm-replay-findings.md).
    df_cbm = pd.DataFrame({
        'period': pi["timestep"] * 0.1,
        'biomass_stock': pi[biomass_pools].sum(axis=1),
        'dom_stock': pi[dom_pools].sum(axis=1),
        'eco_stock': pi[eco_pools].sum(axis=1),
        'total_emission': fi[total_emission].sum(axis=1),
        'gross_growth': fi[gross_growth].sum(axis=1)
    }).groupby('period').sum().iloc[10::10, :].reset_index()

    df_cbm['period'] = df_cbm['period'].round().astype(int)
    df_cbm['net_emission'] = df_cbm['total_emission'] - df_cbm['gross_growth']

    # Summarize WS3 data
    df_ws3 = pd.DataFrame({
        'period': fm.periods,
        'biomass_stock': [fm.inventory(period, 'biomass') for period in fm.periods],
        'dom_stock': [fm.inventory(period, 'DOM') for period in fm.periods],
        'eco_stock': [fm.inventory(period, 'ecosystem') for period in fm.periods],
        'net_emission': [fm.inventory(period, 'net_emission') for period in fm.periods]
    })

    # Plot
    if plots == "whole":
        # Create a single figure
        _fig = plt.figure(figsize=(10, 6))

        # Ecosystem stock
        plt.plot(df_cbm['period'], df_cbm['eco_stock'], label='libcbm Ecosystem Stock')
        plt.plot(df_ws3['period'], df_ws3['eco_stock'], label='ws3 Ecosystem Stock')

        # Biomass stock
        plt.plot(df_cbm['period'], df_cbm['biomass_stock'], label='libcbm Biomass Stock')
        plt.plot(df_ws3['period'], df_ws3['biomass_stock'], label='ws3 Biomass Stock')

        # DOM stock
        plt.plot(df_cbm['period'], df_cbm['dom_stock'], label='libcbm DOM Stock')
        plt.plot(df_ws3['period'], df_ws3['dom_stock'], label='ws3 DOM Stock')

        plt.xlabel('Period')
        plt.ylabel('Stock (tC)')
        plt.ylim(0, None)
        ticks = np.arange(df_cbm['period'].min() - 1, df_cbm['period'].max() + 1, 2)
        plt.xticks(ticks)
        plt.legend()
        plt.tight_layout()

    elif plots == "individual":
        # Create a figure with subplots
        _fig, axs = plt.subplots(4, 1, figsize=(10, 16))
        ticks = np.arange(df_cbm['period'].min() - 1, df_cbm['period'].max() + 1, 2)

        # 1) Ecosystem stock
        axs[0].plot(df_cbm['period'], df_cbm['eco_stock'], label='libcbm Ecosystem Stock')
        axs[0].plot(df_ws3['period'], df_ws3['eco_stock'], label='ws3 Ecosystem Stock')
        axs[0].set_xlabel('Period')
        axs[0].set_ylabel('Stock (tC)')
        axs[0].set_xticks(ticks)
        axs[0].legend()

        # 2) Biomass stock
        axs[1].plot(df_cbm['period'], df_cbm['biomass_stock'], label='libcbm Biomass Stock')
        axs[1].plot(df_ws3['period'], df_ws3['biomass_stock'], label='ws3 Biomass Stock')
        axs[1].set_xlabel('Period')
        axs[1].set_ylabel('Stock (tC)')
        axs[1].set_xticks(ticks)
        axs[1].legend()

        # 3) DOM stock
        axs[2].plot(df_cbm['period'], df_cbm['dom_stock'], label='libcbm DOM Stock')
        axs[2].plot(df_ws3['period'], df_ws3['dom_stock'], label='ws3 DOM Stock')
        axs[2].set_xlabel('Period')
        axs[2].set_ylabel('Stock (tC)')
        axs[2].set_xticks(ticks)
        axs[2].legend()


        # 5) Net ecosystem carbon emission
        axs[3].plot(df_cbm['period'], df_cbm['net_emission'], label='libcbm Net Ecosystem Emission')
        axs[3].plot(df_ws3['period'], df_ws3['net_emission'], label='ws3 Net Ecosystem Emission')
        axs[3].set_xlabel('Period')
        axs[3].set_ylabel('Emission (tC)')
        axs[3].set_xticks(ticks)
        axs[3].legend(loc='lower right')

        plt.tight_layout()

    elif plots == "emissions":
        _fig = plt.figure(figsize=(10, 4))
        plt.plot(df_cbm['period'], df_cbm['net_emission'],
                 label='libcbm Net Ecosystem Emission')
        plt.plot(df_ws3['period'], df_ws3['net_emission'],
                 label='ws3 Net Ecosystem Emission')
        plt.xlabel('Period')
        plt.ylabel('Emission (tC)')
        plt.xticks(np.arange(df_cbm['period'].min() - 1,
                             df_cbm['period'].max() + 1, 2))
        plt.legend()
        plt.tight_layout()

    # If a filename is provided, save the figure to PDF
    if filename is not None:
        plt.savefig(filename, format='pdf', bbox_inches='tight')

    # Finally, show the figure
    plt.show()

    return df_cbm, df_ws3


##############################################################
# Implement simple functions to generate, plug-in, and fix carbon yield curves into ws3 models
# #############################################################
