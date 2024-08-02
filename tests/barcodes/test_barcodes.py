import pytest

from longplexpy.barcodes import well_from_barcode


@pytest.mark.parametrize(
    "barcode_name, well",
    [
        ("seqwell_UDI1_A01_P5", "A01"),
        ("seqwell_UDI1_A01_P7", "A01"),
        ("seqwell_UDI3_A01_P5", "A01"),
        ("seqwell_UDI3_A01_P7", "A01"),
        ("seqwell_UDI3_C03_P5", "C03"),
        ("seqwell_UDI3_C03_P7", "C03"),
    ],
)
def test_well_from_barcode(barcode_name: str, well: str) -> None:
    assert well_from_barcode(barcode_name) == well


@pytest.mark.parametrize(
    "barcode_name",
    [
        "seqwellUDI1_A01_P5",
        "seqwell_UDI1A01_P7",
        "seqwell_UDI3_A01P5",
        "seqwell_UDI3A01P7",
        "seqwellUDI3C03P5",
        "seqwell_UDI3_C03_P7_extra",
    ],
)
def test_well_from_barcode_raises_value_error(barcode_name: str) -> None:
    with pytest.raises(ValueError):
        well_from_barcode(barcode_name)
