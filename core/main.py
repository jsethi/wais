import typer

from core.cli.run import run_command
from core.cli.resume import resume_command
from core.cli.diff import diff_command
from core.cli.list import list_command

app = typer.Typer(
    name="wais",
    help="Web Archival & Ingestion System v1.0",
    no_args_is_help=True,
)

app.command(name="run")(run_command)
app.command(name="resume")(resume_command)
app.command(name="diff")(diff_command)
app.command(name="list")(list_command)

if __name__ == "__main__":
    app()
