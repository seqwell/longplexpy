import logging
import sys
from typing import Callable
from typing import List

import defopt

from longplexpy.tools.hello import hello

_tools: List[Callable] = [hello]


def setup_logging(level: str = "INFO") -> None:
    """Basic logging setup to print to the console."""
    fmt = "%(asctime)s %(name)s:%(funcName)s:%(lineno)s [%(levelname)s]: %(message)s"
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(fmt))

    logger = logging.getLogger("longplexpy")
    logger.setLevel(level)
    logger.addHandler(handler)


def run() -> None:
    """Sets up logging then hands over to defopt for running command line tools."""
    setup_logging()
    logger = logging.getLogger("longplexpy")
    logger.info("Executing: " + " ".join(sys.argv))
    defopt.run(
        funcs=_tools,
        argv=sys.argv[1:],
    )
    logger.info("Finished executing successfully.")
