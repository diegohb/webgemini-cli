import asyncio
from gemiterm.cli import cli

if __name__ == "__main__":
    result = cli(standalone_mode=False)
    if asyncio.iscoroutine(result):
        asyncio.run(result)
