import click
import json
import os

dir_path = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1])
titles = json.loads(open(f"{dir_path}/data/titles.json").read())

@click.group(help="Simplify puzzle editing: extract or import the files related to a certain puzzle.",options_metavar='')
def cli():
    pass

@cli.command(
                name="extract",
                help="Extracts all the files related to a certain puzzle from the ROM into a specific directory",
                no_args_is_help = True,
                options_metavar = "[--lang]"
            )
@click.argument("romfile")
@click.argument("puzzle")
@click.argument("out_dir")
@click.option("--lang", is_flag=True, default = False, help = "Load the game titles in their original language.")
def extract(romfile, puzzle, out_dir, long):
    romfile, id, title = rom.load(romfile, long)