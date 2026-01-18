import warnings

from dagster import BetaWarning, PreviewWarning, SupersessionWarning

warnings.filterwarnings("ignore", category=BetaWarning)
warnings.filterwarnings("ignore", category=PreviewWarning)
warnings.filterwarnings("ignore", category=SupersessionWarning)
# DeprecationWarning is a Python built-in
warnings.filterwarnings("ignore", category=DeprecationWarning)
