from dataclasses import dataclass

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

    @property
    def status(self) -> str:
        """Get ZMW filter status from row (as dict) of lima.report
        Args:
            row: row from lima.report file as a dictionary
        """
        if well_from_barcode(self.IdxHighestNamed) != well_from_barcode(self.IdxLowestNamed):
            return HYBRID_STATUS
        else:
            return PASS_STATUS
