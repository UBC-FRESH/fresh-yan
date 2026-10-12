"""ws3 optimization helpers for the manuscript scenarios.

Objective and constraint coefficient functions, scenario compilation, and problem
construction, extracted from ``msc_walter_yan/util.py`` so this package is
self-contained. The base (max even-flow harvest) scenario maximizes harvest volume
via ``cmp_c_z``; the harvest action must be flagged (``fm.actions[<acode>].is_harvest
= True``, where ``<acode>`` is ``harvest`` for the legacy TSA 24 sections or ``cc`` for
femic exports) for the coefficients to compile (see ``generate_c_curves_tsa24.ipynb``
cell 40).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import ws3.opt


def cmp_c_z(fm, path, expr):
    """
    Compile objective function coefficient (given ForestModel instance,
    leaf-to-root-node path, and expression to evaluate).
    """
    result = 0.
    for t, n in enumerate(path, start=1):
        d = n.data()
        if fm.is_harvest(d['acode']):
            result += fm.compile_product(t, expr, d['acode'], [d['dtk']], d['age'], coeff=False)
    return result


def cmp_c_cflw(fm, path, expr, mask=None): # product, all harvest actions
    """
    Compile flow constraint coefficient for product indicator (given ForestModel
    instance, leaf-to-root-node path, expression to evaluate, and optional mask).
    """
    result = {}
    for t, n in enumerate(path, start=1):
        d = n.data()
        if mask and not fm.match_mask(mask, d['dtk']):
            continue
        if fm.is_harvest(d['acode']):
            result[t] = fm.compile_product(t, expr, d['acode'], [d['dtk']], d['age'], coeff=False)
    return result


def cmp_c_caa(fm, path, expr, acodes, mask=None): # product, named actions
    """
    Compile constraint coefficient for product indicator (given ForestModel
    instance, leaf-to-root-node path, expression to evaluate, list of action codes,
    and optional mask).
    """
    result = {}
    for t, n in enumerate(path, start=1):
        d = n.data()
        if mask and not fm.match_mask(mask, d['dtk']):
            continue
        if d['acode'] in acodes:
            result[t] = fm.compile_product(t, expr, d['acode'], [d['dtk']], d['age'], coeff=False)
    return result


def cmp_c_ci(fm, path, yname, mask=None): # product, named actions
    """
    Compile constraint coefficient for inventory indicator (given ForestModel instance,
    leaf-to-root-node path, expression to evaluate, and optional mask).
    """
    result = {}
    for t, n in enumerate(path, start=1):
        d = n.data()
        if mask and not fm.match_mask(mask, d['_dtk']):
            continue
        result[t] = fm.inventory(t, yname=yname, age=d['_age'], dtype_keys=[d['_dtk']])
        #result[t] = fm.inventory(t, yname=yname, age=d['age'], dtype_keys=[d['dtk']])
    return result


def compile_scenario(fm, harvest_acode='harvest'):
    """Per-period scenario indicators; ``harvest_acode`` is the stand-replacing action."""
    oha = [fm.compile_product(period, '1.', acode=harvest_acode)
           for period in fm.periods]
    ohv = [fm.compile_product(period, 'totvol * 0.85', acode=harvest_acode)
           for period in fm.periods]
    ogs = [fm.inventory(period, 'totvol') for period in fm.periods]
    ocp = [fm.inventory(period, 'ecosystem') for period in fm.periods]
    ocf = [fm.inventory(period, 'total_emission') for period in fm.periods]
    data = {'period':fm.periods,
            'oha':oha,
            'ohv':ohv,
            'ogs':ogs,
            'ocp':ocp,
            'ocf':ocf}
    df = pd.DataFrame(data)
    return df


def plot_scenario(df):
    fig, ax = plt.subplots(1, 4, figsize=(20, 5))
    # Plot and label the first subplot for harvested area
    ax[0].bar(df.period, df.oha)
    ax[0].set_ylim(0, None)
    ax[0].set_title('Harvested area')
    ax[0].set_xlabel('Period')
    ax[0].set_ylabel('Area (ha)')

    # Plot and label the second subplot for harvested volume
    ax[1].bar(df.period, df.ohv)
    ax[1].set_ylim(0, None)
    ax[1].set_title('Harvested volume')
    ax[1].set_xlabel('Period')
    ax[1].set_ylabel('Volume (m3)')

    # Plot and label the third subplot for growing stock
    ax[2].bar(df.period, df.ogs)
    ax[2].set_ylim(0, None)
    ax[2].set_xlabel('Period')
    ax[2].set_title('Growing Stock')
    ax[2].set_ylabel('Volume (m3)')

    # Plot and label the fourth subplot for ecosystem carbon stock
    ax[3].bar(df.period, df.ocp)
    ax[3].set_ylim(0, None)
    ax[3].set_title('Ecosystem C stock')
    ax[3].set_xlabel('Period')
    ax[3].set_ylabel('Stock (ton)')

    return fig, ax


##############################################################
# Implement simple functions to run CBM from ws3 export data and output resutls
# #############################################################


def gen_scenario(fm, name='base', util_rate=0.85, harvest_acode='harvest',
                 cflw_ha=None, cflw_hv=None,
                 cgen_ha=None, cgen_hv=None,
                 cgen_gs=None, tvy_name='totvol', cp_name='ecosystem',
                 cf_name='total_emissions', obj_mode='max', mask=None):
    """Build the base optimization problem (max even-flow harvest volume).

    The harvest action must be flagged (``fm.actions[harvest_acode].is_harvest =
    True``) for the objective coefficients (``cmp_c_z``) to compile.
    """
    if harvest_acode not in fm.actions:
        raise ValueError(
            f"harvest_acode {harvest_acode!r} is not an action in the model "
            f"(actions: {sorted(fm.actions)}); a missing acode silently zeroes the "
            "harvest coefficients")
    from functools import partial

    cflw_ha = cflw_ha or {}
    cflw_hv = cflw_hv or {}
    cgen_ha = cgen_ha or {}
    cgen_hv = cgen_hv or {}
    cgen_gs = cgen_gs or {}

    coeff_funcs = {}
    cflw_e = {}
    cgen_data = {}
    acodes = ['null', harvest_acode]  # define list of action codes
    vexpr = f'{tvy_name} * {util_rate:0.2f}'  # define volume expression

    if obj_mode == 'max':  # maximize harvest volume
        sense = ws3.opt.SENSE_MAXIMIZE
    elif obj_mode == 'min':  # minimize harvest volume
        sense = ws3.opt.SENSE_MINIMIZE
    else:
        raise ValueError(f'Invalid obj_mode: {obj_mode}')

    # Objective function coefficient for harvest volume
    coeff_funcs['z'] = partial(cmp_c_z, expr=vexpr)

    if cflw_ha:  # even-flow constraint on harvest area
        cname = 'cflw_ha'
        coeff_funcs[cname] = partial(cmp_c_caa, expr='1.', acodes=[harvest_acode],
                                     mask=None)
        cflw_e[cname] = cflw_ha
    if cflw_hv:  # even-flow constraint on harvest volume
        cname = 'cflw_hv'
        coeff_funcs[cname] = partial(cmp_c_caa, expr=vexpr, acodes=[harvest_acode],
                                     mask=None)
        cflw_e[cname] = cflw_hv
    if cgen_ha:  # general constraint on harvest area
        cname = 'cgen_ha'
        coeff_funcs[cname] = partial(cmp_c_caa, expr='1.', acodes=[harvest_acode],
                                     mask=None)
        cgen_data[cname] = cgen_ha
    if cgen_hv:  # general constraint on harvest volume
        cname = 'cgen_hv'
        coeff_funcs[cname] = partial(cmp_c_caa, expr=vexpr, acodes=[harvest_acode],
                                     mask=None)
        cgen_data[cname] = cgen_hv
    if cgen_gs:  # general constraint on growing stock
        cname = 'cgen_gs'
        coeff_funcs[cname] = partial(cmp_c_ci, yname=tvy_name, mask=None)
        cgen_data[cname] = cgen_gs
    return fm.add_problem(name, coeff_funcs, cflw_e, cgen_data=cgen_data,
                          acodes=acodes, sense=sense, mask=mask)
