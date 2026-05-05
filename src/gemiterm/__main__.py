import asyncio
from click.exceptions import NoArgsIsHelpError

from gemiterm.cli import cli

if __name__ == "__main__":
    try:
        result = cli(standalone_mode=False)
        if asyncio.iscoroutine(result):
            asyncio.run(result)
    except NoArgsIsHelpError:
        cli.main(["--help"])
