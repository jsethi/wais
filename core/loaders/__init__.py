from core.loaders.base import Loader
from core.loaders.single import SingleURLLoader
from core.loaders.csv_loader import CSVLoader
from core.loaders.json_loader import JSONLoader
from core.loaders.txt_loader import TxtLoader
from core.loaders.xml_loader import XMLLoader
from core.loaders.md_loader import MDLoader

__all__ = [
    "Loader", "SingleURLLoader", "CSVLoader", "JSONLoader",
    "TxtLoader", "XMLLoader", "MDLoader",
]
