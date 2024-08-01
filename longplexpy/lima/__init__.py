from typing import Iterable

from longplexpy.barcodes import well_from_barcode

PASS_STATUS = "pass"
HYBRID_STATUS = "undesired_hybrid"
FIRST_BARCODE = "IdxLowestNamed"
SECOND_BARCODE = "IdxHighestNamed"
ZMW_NAME = "ZMW"

REPORT_FIELDS = [FIRST_BARCODE, SECOND_BARCODE, ZMW_NAME]


def status_from_report_row(row: dict[str, str]) -> str:
    """Get ZMW filter status from row (as dict) of lima.report

    Args:
        row: row from lima.report file as a dictionary
    """
    if well_from_barcode(row[FIRST_BARCODE]) != well_from_barcode(row[SECOND_BARCODE]):
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
        raise ValueError(f"Input is missing required fields: {", ".join(missing_fields)}")
