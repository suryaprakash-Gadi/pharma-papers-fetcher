import pytest
from unittest.mock import patch
from pharma_papers.core import PubMedFetcher

@pytest.mark.parametrize("affiliation, expected", [
    ("Pfizer Inc.", True),
    ("Novartis Pharmaceuticals", True),
    ("GSK Biotech", True),
    ("Merck & Co., Inc.", True),
    ("Harvard University", False),
    ("Massachusetts General Hospital", False),
    ("National Institute of Health", False),
    ("Flatiron Health (an oncology data company)", True),
])
def test_pharma_affiliation_detection(affiliation, expected):
    fetcher = PubMedFetcher()
    assert fetcher._is_pharma_affiliated(affiliation) == expected


