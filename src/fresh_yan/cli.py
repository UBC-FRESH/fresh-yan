"""fresh-yan command-line interface."""

from __future__ import annotations

import typer

from . import __version__

app = typer.Typer(
    help=("Open, reproducible code, data, and results for the HWP half-life and "
          "displacement uncertainty manuscript (TSA 24, British Columbia)."),
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def no_harvest(
    out_dir: str = typer.Option("results/no_harvest", help="Output directory for records."),
) -> None:
    """Regenerate the no-harvest comparison records (ws3 vs libCBM)."""
    from .noharvest import generate

    generate(out_dir)


@app.command()
def base_scenario(
    out_dir: str = typer.Option("results/base_scenario", help="Output directory for records."),
    solver: str = typer.Option("highs", help="LP solver backend (highs or gurobi)."),
) -> None:
    """Regenerate the base scenario records (max even-flow harvest volume)."""
    from .base_scenario import generate

    generate(out_dir, solver=solver)


def _parse_range(spec: str, kind: str) -> list:
    """Parse 'start:stop' or 'start:step:stop' (inclusive)."""
    parts = [p.strip() for p in spec.split(":")]
    values = [int(p) for p in parts] if kind == "int" else [float(p) for p in parts]
    if len(values) == 2:
        start, stop = values
        step = 1 if kind == "int" else 0.1
    elif len(values) == 3:
        start, step, stop = values
    else:
        raise typer.BadParameter(f"expected start:stop or start:step:stop, got '{spec}'")
    out = []
    value = start
    while value <= stop + 1e-9:
        out.append(round(value, 10))
        value += step
    return out


@app.command()
def generate_curves(
    out_dir: str = typer.Option("curves", help="Output directory for the curve pickles."),
    n_steps: int = typer.Option(700, help="Curve length in years."),
) -> None:
    """Regenerate the carbon yield curves with corrected historical disturbance."""
    from .curves import generate

    generate(out_dir, n_steps=n_steps)


@app.command()
def trade_off_grid(
    out_dir: str = typer.Option("results/tradeoff_grid", help="Output directory for records."),
    displacements: str = typer.Option("0.0:0.1:2.4",
                                      help="Displacement factors as start:step:stop."),
    half_lives: str = typer.Option("1:200", help="Half-lives as start:stop or start:step:stop."),
    workers: int = typer.Option(1, help="Parallel worker processes."),
    solver: str = typer.Option("highs", help="LP solver backend (highs or gurobi)."),
) -> None:
    """Regenerate the trade-off grid records (emission-minimizing scenarios)."""
    from .tradeoff_grid import generate

    generate(out_dir,
             displacements=_parse_range(displacements, "float"),
             half_lives=_parse_range(half_lives, "int"),
             workers=workers, solver=solver)


@app.command()
def version() -> None:
    """Print package and key dependency versions."""
    import libcbm
    import ws3

    typer.echo(f"fresh-yan {__version__} | ws3 {ws3.__version__} | libcbm {libcbm.__version__}")


if __name__ == "__main__":
    app()
