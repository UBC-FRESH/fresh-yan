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
def version() -> None:
    """Print package and key dependency versions."""
    import libcbm
    import ws3

    typer.echo(f"fresh-yan {__version__} | ws3 {ws3.__version__} | libcbm {libcbm.__version__}")


if __name__ == "__main__":
    app()
