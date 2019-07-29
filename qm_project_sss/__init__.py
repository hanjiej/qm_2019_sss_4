"""
qm_project_sss
This package implements semi-empirical quantum mechanical (SCF+MP2) simulation parameterized to reproduce first-principles QM data using a minimal model.
"""

# Add imports here
from .hartree_fock import *
from .noble_gas_model import *

# Handle versioneer
from ._version import get_versions
versions = get_versions()
__version__ = versions['version']
__git_revision__ = versions['full-revisionid']
del get_versions, versions
