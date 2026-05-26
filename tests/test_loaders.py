from __future__ import annotations

from core.loaders.single import SingleURLLoader
from core.loaders.csv_loader import CSVLoader
from core.loaders.json_loader import JSONLoader
from core.loaders.txt_loader import TxtLoader
from core.loaders.xml_loader import XMLLoader
from core.loaders.md_loader import MDLoader


class TestSingleURLLoader:
    def test_load(self):
        loader = SingleURLLoader("https://example.com", depth=2)
        results = list(loader.load())
        assert len(results) == 1
        assert results[0].source == "https://example.com"
        assert results[0].depth == 2


class TestCSVLoader:
    def test_load(self, sample_csv):
        loader = CSVLoader(sample_csv)
        results = list(loader.load())
        assert len(results) == 2
        assert results[0].source == "https://example.com"


class TestJSONLoader:
    def test_load_list(self, sample_json):
        loader = JSONLoader(sample_json)
        results = list(loader.load())
        assert len(results) == 2
        assert results[0].depth == 0
        assert results[0].tags == ["test"]


class TestTxtLoader:
    def test_load(self, sample_txt):
        loader = TxtLoader(sample_txt)
        results = list(loader.load())
        assert len(results) == 2
        assert results[0].source == "https://example.com"


class TestXMLLoader:
    def test_load(self, sample_xml):
        loader = XMLLoader(sample_xml)
        results = list(loader.load())
        assert len(results) == 2
        assert results[0].depth == 0


class TestMDLoader:
    def test_load(self, sample_md):
        loader = MDLoader(sample_md)
        results = list(loader.load())
        assert len(results) == 2
        assert results[0].source == "https://example.com"
