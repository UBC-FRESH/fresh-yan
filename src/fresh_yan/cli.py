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

_DEFAULT_TSA = "tsa24"


@app.command()
def no_harvest(
    out_dir: str | None = typer.Option(
        None, help="Output directory for records (default: results/no_harvest)."),
    tsa: str = typer.Option(_DEFAULT_TSA, help="Management unit label; sets the default "
                                               "model path and record layout."),
    model_name: str | None = typer.Option(
        None, help="Woodstock section stem (default: the TSA label)."),
    model_path: str | None = typer.Option(
        None, help="Woodstock sections directory (default: data/woodstock_model_files_<tsa>)."),
    curves_dir: str | None = typer.Option(
        None, help="Curve directory (default: curves; curves/<tsa> for other TSAs)."),
) -> None:
    """Regenerate the no-harvest comparison records (ws3 vs libCBM)."""
    from .model import record_dir_for
    from .noharvest import generate

    generate(record_dir_for(tsa, "results/no_harvest", out_dir), tsa=tsa,
             model_name=model_name, model_path=model_path, curves_dir=curves_dir)


@app.command()
def base_scenario(
    out_dir: str | None = typer.Option(
        None, help="Output directory for records (default: results/base_scenario)."),
    solver: str = typer.Option("highs", help="LP solver backend (highs or gurobi)."),
    tsa: str = typer.Option(_DEFAULT_TSA, help="Management unit label; sets the default "
                                               "model path and record layout."),
    model_name: str | None = typer.Option(
        None, help="Woodstock section stem (default: the TSA label)."),
    model_path: str | None = typer.Option(
        None, help="Woodstock sections directory (default: data/woodstock_model_files_<tsa>)."),
    curves_dir: str | None = typer.Option(
        None, help="Curve directory (default: curves; curves/<tsa> for other TSAs)."),
) -> None:
    """Regenerate the base scenario records (max even-flow harvest volume)."""
    from .base_scenario import generate
    from .model import record_dir_for

    generate(record_dir_for(tsa, "results/base_scenario", out_dir), solver=solver,
             tsa=tsa, model_name=model_name, model_path=model_path, curves_dir=curves_dir)


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
    out_dir: str | None = typer.Option(
        None, help="Output directory for the curve pickles (default: curves; "
                   "curves/<tsa> for other TSAs)."),
    n_steps: int = typer.Option(700, help="Curve length in years."),
    rotation_age: int = typer.Option(120, help="Simulated clearcut age for managed curves."),
    tsa: str = typer.Option(_DEFAULT_TSA, help="Management unit label; sets the default "
                                               "model path."),
    model_name: str | None = typer.Option(
        None, help="Woodstock section stem (default: the TSA label)."),
    model_path: str | None = typer.Option(
        None, help="Woodstock sections directory (default: data/woodstock_model_files_<tsa>)."),
) -> None:
    """Regenerate the carbon yield curves (managed curves from simulated clearcuts)."""
    from .curves import generate
    from .model import curves_dir_for

    generate(curves_dir_for(tsa, out_dir), n_steps=n_steps, rotation_age=rotation_age,
             tsa=tsa, model_name=model_name, model_path=model_path)


@app.command()
def trade_off_grid(
    out_dir: str | None = typer.Option(
        None, help="Output directory for records (default: results/tradeoff_grid)."),
    displacements: str = typer.Option("0.0:0.1:2.4",
                                      help="Displacement factors as start:step:stop."),
    half_lives: str = typer.Option("1:200", help="Half-lives as start:stop or start:step:stop."),
    workers: int = typer.Option(1, help="Parallel worker processes."),
    solver: str = typer.Option("highs", help="LP solver backend (highs or gurobi)."),
    tsa: str = typer.Option(_DEFAULT_TSA, help="Management unit label; sets the default "
                                               "model path and record layout."),
    model_name: str | None = typer.Option(
        None, help="Woodstock section stem (default: the TSA label)."),
    model_path: str | None = typer.Option(
        None, help="Woodstock sections directory (default: data/woodstock_model_files_<tsa>)."),
    curves_dir: str | None = typer.Option(
        None, help="Curve directory (default: curves; curves/<tsa> for other TSAs)."),
) -> None:
    """Regenerate the trade-off grid records (emission-minimizing scenarios)."""
    from .model import record_dir_for
    from .tradeoff_grid import generate

    generate(record_dir_for(tsa, "results/tradeoff_grid", out_dir),
             displacements=_parse_range(displacements, "float"),
             half_lives=_parse_range(half_lives, "int"),
             workers=workers, solver=solver, tsa=tsa, model_name=model_name,
             model_path=model_path, curves_dir=curves_dir)


@app.command()
def version() -> None:
    """Print package and key dependency versions."""
    import libcbm
    import ws3

    typer.echo(f"fresh-yan {__version__} | ws3 {ws3.__version__} | libcbm {libcbm.__version__}")


if __name__ == "__main__":
    app()
