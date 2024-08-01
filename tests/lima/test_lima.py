import pytest

import longplexpy.lima as lima
from longplexpy.lima import status_from_report_row
from longplexpy.lima import validate_header


@pytest.mark.parametrize(
    "report_row, status",
    [
        (
            {lima.FIRST_BARCODE: "seqwell_UDI1_A01_P5", lima.SECOND_BARCODE: "seqwell_UDI1_A01_P5"},
            lima.PASS_STATUS,
        ),
        (
            {lima.FIRST_BARCODE: "seqwell_UDI1_A01_P5", lima.SECOND_BARCODE: "seqwell_UDI1_A01_P7"},
            lima.PASS_STATUS,
        ),
        (
            {lima.FIRST_BARCODE: "seqwell_UDI1_B01_P5", lima.SECOND_BARCODE: "seqwell_UDI1_B01_P5"},
            lima.PASS_STATUS,
        ),
        (
            {lima.FIRST_BARCODE: "seqwell_UDI1_A01_P5", lima.SECOND_BARCODE: "seqwell_UDI1_A02_P5"},
            lima.HYBRID_STATUS,
        ),
        (
            {lima.FIRST_BARCODE: "seqwell_UDI1_A01_P5", lima.SECOND_BARCODE: "seqwell_UDI1_A02_P7"},
            lima.HYBRID_STATUS,
        ),
        (
            {lima.FIRST_BARCODE: "seqwell_UDI1_A01_P5", lima.SECOND_BARCODE: "seqwell_UDI1_B01_P5"},
            lima.HYBRID_STATUS,
        ),
    ],
)
def test_status_from_report_row(report_row: dict[str, str], status: str) -> None:
    assert status_from_report_row(report_row) == status


def test_validate_header() -> None:
    # Valid headers, no error raised
    validate_header(["here"], ["here"])
    validate_header(["here"], [])

    # Invalid headers, error raised
    with pytest.raises(ValueError):
        validate_header([], ["here"])
    with pytest.raises(ValueError):
        validate_header(["not_here"], ["here"])
