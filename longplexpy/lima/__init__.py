from dataclasses import dataclass
from typing import Iterable

from fgpyo.util.metric import Metric

from longplexpy.barcodes import well_from_barcode

PASS_STATUS = "pass"
HYBRID_STATUS = "undesired_hybrid"


@dataclass(frozen=True)
class LimaReportMetric(Metric["LimaReportMetric"]):
    """A dataclass that captures relevant portions of the *.lima.report

    Attributes:
        ZMW: name of the ZMW Lima is reporting on. Note this will not necessarily match the
            read name in the input BAM. Notably "/ccs" will be stripped off.
        IdxLowestNamed: the name of the barcode occurring first in the read
        IdxHighestNamed: the name of the barcode occuring last in the read
    """
    ZMW: str
    IdxLowestNamed: str
    IdxHighestNamed: str

def status_from_report_row(lima_report: "LimaReportMetric") -> str:
    """Get ZMW filter status from row (as dict) of lima.report

    Args:
        row: row from lima.report file as a dictionary
    """
    if well_from_barcode(lima_report.IdxHighestNamed) != well_from_barcode(
        lima_report.IdxLowestNamed
    ):
        return HYBRID_STATUS
    else:
        return PASS_STATUS


def validate_header(input_fieldnames: Iterable[str], required_fields: Iterable[str]) -> None:
    """Validates that a header has the required fields

    Args:
        input_fieldnames: list of fieldnames in input header
        required_fields: list of required fields.
            Default = REPORT_FIELDS
    Raises:
        ValueError if any required fields are not fond in the input fieldnames
    """
    missing_fields = [field for field in required_fields if field not in input_fieldnames]
    if len(missing_fields) != 0:
        raise ValueError(f"Input is missing required fields: {', '.join(missing_fields)}")
