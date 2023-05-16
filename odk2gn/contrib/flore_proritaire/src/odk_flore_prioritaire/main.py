import click


@click.command(name="flore_prio")
def synchronize():
    print("SYNCHRONIZE FROM FLORE PRIO")


@click.command(name="again_flore_prio")
def upgrade_odk_form():
    print("UPGRADE FROM FLORE PRIO")
