__version__ = '2.0'
import os

if not os.getenv("IS_CLOUD", False):
    from .dataset import KarmanDataset
    from .nn import SimpleNetwork
    from .util import exponential_atmosphere
