from pathlib import Path

MASK_TIME = (r"\d+:\d+(:?AM|PM)", "9:00AM")
MASK_SLING_WARNING = (r"warning.*\n", "")
MASK_SLING_PROMO = (r"Follow Sling.*\n", "")
MASK_SLING_DOWNLOAD_DUCKDB = (r".*downloading duckdb.*\n", "")
MASK_JAFFLE_PLATFORM = (r" \/.*?\/jaffle-platform", " /.../jaffle-platform")

DAGSTER_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent
COMPONENTS_SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_beta_snippets"
    / "docs_beta_snippets"
    / "guides"
    / "components"
    / "index"
)
