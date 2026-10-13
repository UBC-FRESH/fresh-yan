"""FreshForge provider exposing the fresh-yan modelling pipeline as workflow nodes.

Registered through the ``freshforge.providers`` entry point, so any FreshForge run can
compose these nodes into reproducible workflows (see ``workflows/``): carbon yield curve
generation, the no-harvest comparison, the base scenario, the trade-off grid, and the
sensitivity figures.

Workflows must be run from the repository root: the model inputs (``data/``) and the
default record paths are repository-relative.  Node parameters may be strings (run
matrices substitute placeholders as strings); they are coerced here.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from freshforge.providers import NodeTypeMetadata, ProviderMetadata
from freshforge.records import Diagnostic, DiagnosticSeverity, ProviderRunResult, RunStatus

PROVIDER_ID = "fresh_yan.pipeline"
PROVIDER_VERSION = "0.1.0"

_NODE_TYPES = (
    NodeTypeMetadata(
        id="generate_curves",
        name="Generate carbon yield curves",
        description=("Managed curves from simulated clearcuts (rotation-cycle equilibrium); "
                     "natural curves from the spun-up no-harvest trajectories."),
        parameters=("out_dir", "rotation_age", "n_steps", "mode", "tsa", "model_name",
                    "model_path", "section_units", "harvest_acode"),
        artifacts=("curves_p", "curves_f"),
    ),
    NodeTypeMetadata(
        id="no_harvest",
        name="No-harvest comparison records",
        description="ws3 carbon yield-curve landscape vs a direct libCBM run (no harvest).",
        parameters=("out_dir", "tsa", "model_name", "model_path", "curves_dir",
                    "section_units", "harvest_acode"),
        artifacts=("cbm_csv", "ws3_csv", "pct_diff_csv", "summary_csv", "figures"),
    ),
    NodeTypeMetadata(
        id="base_scenario",
        name="Base scenario records",
        description="Maximize even-flow harvest volume over the 200-year horizon.",
        parameters=("out_dir", "solver", "tsa", "model_name", "model_path", "curves_dir",
                    "section_units", "harvest_acode"),
        artifacts=("records_csv", "figure"),
    ),
    NodeTypeMetadata(
        id="trade_off_grid",
        name="Trade-off grid records",
        description=("Emission-minimizing scenarios over (displacement factor, solid-wood "
                     "half-life) on the corrected accounting."),
        parameters=("out_dir", "displacements", "half_lives", "workers", "solver", "tsa",
                    "model_name", "model_path", "curves_dir", "section_units",
                    "harvest_acode"),
        artifacts=("harvest_csv", "stock_csv", "emission_csv", "summary_csv"),
    ),
    NodeTypeMetadata(
        id="sensitivity_figures",
        name="Sensitivity figures",
        description="3D surface and orthographic views of total harvested volume.",
        parameters=("summary", "out_dir"),
        artifacts=("3d_pdf", "xyz_pdf"),
    ),
)


def _int(params: dict[str, Any], key: str, default: int) -> int:
    value = params.get(key, default)
    return int(float(value))


def _float_list(params: dict[str, Any], key: str) -> list[float] | None:
    value = params.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return [float(v) for v in value.split(",") if v.strip()]
    return [float(v) for v in value]


def _int_list(params: dict[str, Any], key: str) -> list[int] | None:
    value = params.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return [int(float(v)) for v in value.split(",") if v.strip()]
    return [int(v) for v in value]


class PipelineProvider:
    """fresh-yan pipeline nodes for FreshForge workflows."""

    def metadata(self) -> ProviderMetadata:
        return ProviderMetadata(
            id=PROVIDER_ID,
            version=PROVIDER_VERSION,
            name="fresh-yan pipeline",
            description=("Reproducible workflow nodes for the HWP half-life and displacement "
                         "uncertainty manuscript (ws3 + libCBM + HWP accounting, TSA 24)."),
            node_types=_NODE_TYPES,
        )

    def validate_node(
        self,
        node: Any,
        node_type: NodeTypeMetadata,
        *,
        location: str,
    ) -> tuple[Diagnostic, ...]:
        params = dict(node.parameters or {})
        diagnostics: list[Diagnostic] = []
        model_path = params.get("model_path")
        if model_path and not Path(model_path).exists():
            diagnostics.append(Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="fresh_yan.model_path",
                message=f"model_path does not exist: {model_path}",
                location=location,
            ))
        if node_type.id == "generate_curves":
            mode = str(params.get("mode", "cycle"))
            if mode not in ("single", "cycle"):
                diagnostics.append(Diagnostic(
                    severity=DiagnosticSeverity.ERROR,
                    code="fresh_yan.generate_curves.mode",
                    message=f"mode must be 'single' or 'cycle', got '{mode}'",
                    location=location,
                ))
            if _int(params, "rotation_age", 120) <= 0:
                diagnostics.append(Diagnostic(
                    severity=DiagnosticSeverity.ERROR,
                    code="fresh_yan.generate_curves.rotation_age",
                    message="rotation_age must be a positive integer",
                    location=location,
                ))
        if node_type.id in ("base_scenario", "trade_off_grid"):
            solver = str(params.get("solver", "highs"))
            if solver not in ("highs", "gurobi"):
                diagnostics.append(Diagnostic(
                    severity=DiagnosticSeverity.ERROR,
                    code="fresh_yan.solver",
                    message=f"solver must be 'highs' or 'gurobi', got '{solver}'",
                    location=location,
                ))
        return tuple(diagnostics)

    def run_node(
        self,
        node: Any,
        node_type: NodeTypeMetadata,
        *,
        context: Any,
    ) -> ProviderRunResult:
        if not Path("data/woodstock_model_files_tsa24").exists():
            return ProviderRunResult(
                status=RunStatus.FAILED,
                diagnostics=(Diagnostic(
                    severity=DiagnosticSeverity.ERROR,
                    code="fresh_yan.workdir",
                    message=("Workflows must run from the fresh-yan repository root "
                             "(model inputs are repository-relative)."),
                    location=node.id,
                ),),
            )
        params = dict(node.parameters or {})
        try:
            if node_type.id == "generate_curves":
                return self._generate_curves(node, params, context)
            if node_type.id == "no_harvest":
                return self._no_harvest(node, params, context)
            if node_type.id == "base_scenario":
                return self._base_scenario(node, params, context)
            if node_type.id == "trade_off_grid":
                return self._trade_off_grid(node, params, context)
            if node_type.id == "sensitivity_figures":
                return self._sensitivity_figures(node, params, context)
        except Exception as exc:  # report provider failures as diagnostics
            return ProviderRunResult(
                status=RunStatus.FAILED,
                diagnostics=(Diagnostic(
                    severity=DiagnosticSeverity.ERROR,
                    code=f"fresh_yan.{node_type.id}.failed",
                    message=str(exc),
                    location=node.id,
                ),),
            )
        return ProviderRunResult(
            status=RunStatus.FAILED,
            diagnostics=(Diagnostic(
                severity=DiagnosticSeverity.ERROR,
                code="fresh_yan.unknown_node_type",
                message=f"unknown node type '{node_type.id}'",
                location=node.id,
            ),),
        )

    # --- node implementations ---

    def _generate_curves(
        self, node: Any, params: dict[str, Any], context: Any
    ) -> ProviderRunResult:
        from .curves import generate
        from .model import curves_dir_for

        tsa = str(params.get("tsa", "tsa24"))
        out_dir = context.resolve_path(curves_dir_for(tsa, params.get("out_dir")))
        generate(str(out_dir),
                 rotation_age=_int(params, "rotation_age", 120),
                 n_steps=_int(params, "n_steps", 700),
                 mode=str(params.get("mode", "cycle")),
                 tsa=tsa,
                 model_name=params.get("model_name"),
                 model_path=params.get("model_path"),
                 section_units=str(params.get("section_units", "years")),
                 harvest_acode=str(params.get("harvest_acode", "harvest")))
        return ProviderRunResult(
            status=RunStatus.SUCCESS,
            outputs={"curves_dir": str(out_dir)},
            artifacts={
                "curves_p": str(out_dir / "c_curves_p.pkl"),
                "curves_f": str(out_dir / "c_curves_f.pkl"),
            },
        )

    def _no_harvest(self, node: Any, params: dict[str, Any], context: Any) -> ProviderRunResult:
        from .model import record_dir_for
        from .noharvest import generate

        tsa = str(params.get("tsa", "tsa24"))
        out_dir = context.resolve_path(record_dir_for(tsa, "results/no_harvest",
                                                      params.get("out_dir")))
        generate(str(out_dir), tsa=tsa, model_name=params.get("model_name"),
                 model_path=params.get("model_path"), curves_dir=params.get("curves_dir"),
                 section_units=str(params.get("section_units", "years")),
                 harvest_acode=str(params.get("harvest_acode", "harvest")))
        return ProviderRunResult(
            status=RunStatus.SUCCESS,
            outputs={"records_dir": str(out_dir)},
            artifacts={
                "cbm_csv": str(out_dir / "no_harvest_cbm.csv"),
                "ws3_csv": str(out_dir / "no_harvest_ws3.csv"),
                "pct_diff_csv": str(out_dir / "no_harvest_pct_diff.csv"),
                "summary_csv": str(out_dir / "no_harvest_pct_diff_summary.csv"),
                "figures": str(out_dir / "no_harvest_carbon_stock_whole_st.pdf"),
            },
        )

    def _base_scenario(self, node: Any, params: dict[str, Any], context: Any) -> ProviderRunResult:
        from .base_scenario import generate
        from .model import record_dir_for

        tsa = str(params.get("tsa", "tsa24"))
        out_dir = context.resolve_path(record_dir_for(tsa, "results/base_scenario",
                                                      params.get("out_dir")))
        generate(str(out_dir), solver=str(params.get("solver", "highs")), tsa=tsa,
                 model_name=params.get("model_name"), model_path=params.get("model_path"),
                 curves_dir=params.get("curves_dir"),
                 section_units=str(params.get("section_units", "years")),
                 harvest_acode=str(params.get("harvest_acode", "harvest")))
        return ProviderRunResult(
            status=RunStatus.SUCCESS,
            outputs={"records_dir": str(out_dir)},
            artifacts={
                "records_csv": str(out_dir / "base_scenario.csv"),
                "figure": str(out_dir / "base_scenario.pdf"),
            },
        )

    def _trade_off_grid(self, node: Any, params: dict[str, Any], context: Any) -> ProviderRunResult:
        from .model import record_dir_for
        from .tradeoff_grid import generate

        tsa = str(params.get("tsa", "tsa24"))
        out_dir = context.resolve_path(record_dir_for(tsa, "results/tradeoff_grid",
                                                      params.get("out_dir")))
        generate(str(out_dir),
                 displacements=_float_list(params, "displacements"),
                 half_lives=_int_list(params, "half_lives"),
                 workers=_int(params, "workers", 1),
                 solver=str(params.get("solver", "highs")),
                 tsa=tsa,
                 model_name=params.get("model_name"),
                 model_path=params.get("model_path"),
                 curves_dir=params.get("curves_dir"),
                 section_units=str(params.get("section_units", "years")),
                 harvest_acode=str(params.get("harvest_acode", "harvest")))
        return ProviderRunResult(
            status=RunStatus.SUCCESS,
            outputs={"records_dir": str(out_dir)},
            artifacts={
                "harvest_csv": str(out_dir / "tradeoff_grid_harvest.csv"),
                "stock_csv": str(out_dir / "tradeoff_grid_stock.csv"),
                "emission_csv": str(out_dir / "tradeoff_grid_emission.csv"),
                "summary_csv": str(out_dir / "tradeoff_grid_summary.csv"),
            },
        )

    def _sensitivity_figures(
        self, node: Any, params: dict[str, Any], context: Any
    ) -> ProviderRunResult:
        summary = context.resolve_path(params.get(
            "summary", "results/tradeoff_grid/tradeoff_grid_summary.csv"))
        out_dir = context.resolve_path(params.get("out_dir", "results/sensitivity"))
        script = Path("scripts/analyze_sensitivity.py")
        if not script.exists():
            raise FileNotFoundError(f"missing analysis script: {script}")
        out_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run([sys.executable, str(script), "--summary", str(summary),
                        "--out-dir", str(out_dir)], check=True)
        return ProviderRunResult(
            status=RunStatus.SUCCESS,
            outputs={"figures_dir": str(out_dir)},
            artifacts={
                "3d_pdf": str(out_dir / "3d.pdf"),
                "xyz_pdf": str(out_dir / "xyz.pdf"),
            },
        )


def provider_factory() -> PipelineProvider:
    """Entry-point factory for the ``freshforge.providers`` group."""
    return PipelineProvider()
