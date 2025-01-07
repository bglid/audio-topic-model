from typing import Optional

import argparse
from enum import Enum
from random import choice

import topic_model
import typer
from rich.console import Console

from audio_topic_model import version


def run_cli():
    """
    Function that takes our args from cli and executes the correct app.
    """

    # Adding arg parser
    parser = argparse.ArgumentParser(description="Run different project tools")
    # adding subparser for choosing tool
    subparsers = parser.add_subparsers(dest="tool", description={"Which tool to use"})

    # keyword extraction: add later

    # topic modeling args!
    topic_parser = subparsers.add_parser("topic", help="Run Topic Modeling")

    topic_parser.add_argument(
        "--input",
        type=str,
        default="",
        required=True,
        help="Path to directory of files to be read into tool",
    )

    topic_parser.add_argument(
        "--output",
        type=str,
        default="",
        required=True,
        help="Path to directory for destination of results.",
    )

    topic_parser.add_argument(
        "--name",
        type=str,
        default="",
        required=True,
        help="Name of the run, used in naming the results file",
    )

    topic_parser.add_argument(
        "--uri",
        type=str,
        default="",
        help="URI needed for Neo4j DB",
    )

    topic_parser.add_argument(
        "--auth_username",
        type=str,
        default="",
        help="Neo4j auth username, needed for connection",
    )

    topic_parser.add_argument(
        "--auth_password",
        type=str,
        default="",
        help="Neo4j auth password, needed for connection",
    )

    args = parser.parse_args()

    # choosing which tool to run
    if args.tool == "topic":
        topic_model.topic_modeling(
            input=args.input,
            output=args.output,
            name=args.name,
            uri=args.uri,
            auth_username=args.auth_username,
            auth_password=args.auth_password,
        )
    else:
        parser.print_help()


class Color(str, Enum):
    white = "white"
    red = "red"
    cyan = "cyan"
    magenta = "magenta"
    yellow = "yellow"
    green = "green"


app = typer.Typer(
    name="audio-topic-model",
    help="Micro service for performing topic modeling on audio data.",
    add_completion=False,
)
console = Console()


def version_callback(print_version: bool) -> None:
    """Print the version of the package."""
    if print_version:
        console.print(f"[yellow]audio-topic-model[/] version: [bold blue]{version}[/]")
        raise typer.Exit()


@app.command(name="")
def main(
    name: str = typer.Option(..., help="Person to greet."),
    color: Optional[Color] = typer.Option(
        None,
        "-c",
        "--color",
        "--colour",
        case_sensitive=False,
        help="Color for print. If not specified then choice will be random.",
    ),
    print_version: bool = typer.Option(
        None,
        "-v",
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Prints the version of the audio-topic-model package.",
    ),
) -> None:
    """Print a greeting with a giving name."""
    if color is None:
        color = choice(list(Color))

    run_cli()


if __name__ == "__main__":
    app()
