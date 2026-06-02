"""Sync pair configurations and known-incorrect commit lists."""

from dataclasses import dataclass, field


@dataclass
class SyncConfig:
    """Configuration for a single copybara sync direction."""

    name: str
    direction: str  # "inbound" or "outbound"
    public_repo_url: str
    public_repo_slug: str  # "dagster" or "skills"
    synced_label: str
    originated_label: str
    internal_path: str  # for outbound completeness (e.g. "dagster-oss/")
    internal_path_prefix: str  # for correctness normalization (e.g. "dagster-oss/")
    file_renames: dict[str, str] = field(default_factory=dict)
    known_incorrect: list[str] = field(default_factory=list)
    source_repo_name: str = ""
    dest_repo_name: str = ""


# Copybara renames certain files when syncing between internal and dagster-io/dagster.
# Internal (dagster-oss/) has *.oss.{ext} variants that map to the canonical names in OSS.
# This dict maps the internal name (under dagster-oss/) to the OSS name.
DAGSTER_FILE_RENAMES: dict[str, str] = {
    "js_modules/yarn.oss.lock": "js_modules/yarn.lock",
    "js_modules/.yarnrc.oss.yml": "js_modules/.yarnrc.yml",
    "js_modules/package.oss.json": "js_modules/package.json",
}

# Commits known to have been incorrectly synced (extra or missing files due to a copybara
# race condition). Each entry is the hash of the **destination** commit (the one that
# landed with extra/missing file changes). Once an incorrect sync has been identified and
# its effects fixed by a later commit, add the destination hash here so the correctness
# check does not keep failing on historical incidents that have already been addressed.

KNOWN_DAGSTER_INBOUND_INCORRECTLY_SYNCED_COMMITS: list[str] = [
    # fix: replace bare except clauses -- synced 23 extra js_modules files, fixed by
    # "[ui] Revert accidental reversion in js_modules (#22025)"
    "4059fb0edb64e47fc29a0494f6011b526209b623",
    # [docs] fix inventory URIs -- synced 18 extra docs example files, fixed by later syncs
    "b01b250b63ec8a8272de402f329b46d1b34b37fe",
    # [dagster-spark] mark spark declarative pipelines as preview -- synced 3 extra files
    # (asset_daemon.py, serdes pack), fixed by "Owen/unrevert write path (#22067)"
    "51473d6803e3e3323638511cdc0be53c13521ef4",
    # [dg] Bump actions/setup-python -- synced 2 extra files (freshness policies doc,
    # conftest), fixed by later syncs
    "d296bad64eec239147f6b60cae8898bf30987140",
    # Update OSS yarn.lock (#33540) -- synced extra python_modules/automation/automation/git.py
    # (two internal commits reference the same OSS hash; include both)
    "8a2eed789c184aec9edcf7da9dd2026e0ac0aa68",
    "71a5a8b814e03381fbdb99731d257178d1e14dfb",
    # fix(dlt): drop local state before run -- synced extra buildkite/steps/packages.py
    "d1dcf85a65f353dc374619d832ad602a2ae9f058",
    # [dg] Bump actions/checkout -- synced extra events/__init__.py
    "7f043ce962acab36f2919cfc8a02dac623eb4244",
    # [dagster-postgres] add workload identity federation auth -- inbound sync of John
    # Mav's OSS PR #33735 included a stale revert of Joe Braha's cluster_id additions in
    # dagster-oss/.buildkite/.../trigger_step_builder.py. Joe's cluster_id was later
    # intentionally reverted by "fix: revert trigger cluster_id + add queue to dogfood
    # gate steps (#23396)", so the current state is consistent.
    "e3554b46b14c77826141314ee2086be3ae04b71c",
    # Adds kinds tags for Alteryx, Boomi, and SAP (#33807) -- inbound sync carried an
    # extra revert of examples/docs_projects/project_components_pdf_extraction/pyproject.toml
    # from a concurrent outbound (#24193). The pdf_extraction change was re-applied by
    # a later inbound, so current state is consistent.
    "3a0727013a194d4c9c44fec38aae69328f58e05b",
]

KNOWN_DAGSTER_OUTBOUND_INCORRECTLY_SYNCED_COMMITS: list[str] = [
    # [docs] Doc project tests -- synced missing 25 js_modules files (reverted CSS modules
    # migration), fixed by "[ui] Revert accidental reversion in js_modules (#22025)"
    "4d788415c1dc6f8044dcad573ce548afaeef7283",
    # Add dagre patch file -- synced missing 2 files (nux.py, container.py), fixed by
    # "fix: replace bare except clauses (#33659)"
    "ac7e2f2b3fc2e4840fb4d6e5f499cf8215a6c9db",
    # [docs] fix failed test that expects @public -- synced missing 7 files (spark
    # components, serdes pack), fixed by later syncs
    "e5186ad7fb7f5029bf4b43c2a2a7ee99665b5e53",
    # [writer] AssetDaemonCursor compressed write path -- synced missing 7 files (spark
    # components), fixed by later syncs
    "6bfc87c83dd2b8f1ab27cbfd9f68018d868666c0",
    # Add partitions attribute support -- synced missing 28 files (docs infra, pipes,
    # examples), fixed by later syncs
    "3f82d1ea2ef53a65680ffcee6e4a991ab1a00240",
    # [docs] Enable pyright for docs examples -- synced missing 10 files (docs infra,
    # pipes client), fixed by later syncs
    "153396855ed2642ebb8bb55c09927dc8c86f71be",
    # [ui] Fix asset catalog sidebar -- synced missing 3 files (dlt, buildkite), fixed
    # by later syncs
    "7f73da5a70984fdcbf6b79967ccfd2bdd86acdeb",
    # [buildkite] Fix UI extra commands -- synced missing 2 files (dlt resource/tests),
    # fixed by later syncs
    "33dd56d31bea00332d19cd4af60341101e9ea58a",
    # [monorepo] Add pull_request passthrough -- synced missing 4 files, fixed by later syncs
    "f92b4cae06380c5dfb957ac3d1f007bebeae9d79",
    # Speed up dagster-graphql standalone tests -- synced missing 2 files (dg-cli
    # templates), fixed by later syncs
    "e271b904085352c8fb2ac38a96600b2131677688",
    # Bump immutable -- synced missing 2 files (yarn.lock, git.py), fixed by later syncs
    "df88d0958a6dc58eace2ef0b12b2016e596c50f9",
    # [changelog] 1.12.18 changelog -- synced missing 1 file (multiple.md), fixed by
    # later syncs
    "59b5e4b30d35a366b1866944335a3b80f09db81f",
    # [copybara] dagster-io/skills copybara sync -- synced missing 1 file (multiple.md),
    # fixed by later syncs
    "fa2db48504bfcdacbc9bf369b95a7f0ad0742c7a",
    # [Aikido] AI Fix for Unsafe subprocess usage -- synced extra js_modules/yarn.lock
    # (copybara regenerated yarn.lock during outbound sync)
    "38836841b3d6bc2badcf9040b81e579c9c61f06a",
    # Bump actions/checkout -- synced extra events/__init__.py, dg-cli templates,
    # runtime-environment.md, and .github/workflows files
    "657d67886332bf6e127aab661d66660e32762287",
    # [dg] Bump actions/setup-python -- synced extra dg-cli templates,
    # runtime-environment.md, and .github/workflows files
    "5fa0b5b4e301eef12594fba117573789a85d1ad7",
    # buildkite: add cluster_id to trigger steps (#23383) -- outbound sync to OSS
    # incorrectly reverted John Mav's WIF work in OSS (helm/*, dagster-postgres/*).
    # Re-added by the next outbound sync (4ad89db4, Isaac's UI fix).
    "b8609e25b2fe72e202bd6dac2062a3de66e1eda7",
    # [ui] Fix partition filter input unresponsive (#23393) -- outbound sync to OSS
    # carried 18 extra files: re-added John Mav's WIF work (fixing b8609e25's revert)
    # and reverted Joe Braha's cluster_id. Joe's cluster_id was later intentionally
    # reverted internally by #23396, so current state is consistent.
    "4ad89db4436a3ea6bc0804676093fb604ea2ff3a",
    # remove dagster-test reference from example docs project (#24193) -- outbound sync
    # to OSS reverted OSS PR #33807's kinds tags (8 files: _KindsTags.md, OpTags.tsx,
    # alteryx/boomi/sap svgs in two locations). Kinds tags were re-applied by a later
    # inbound sync, so current state is consistent.
    "6893ae16f14335789804f736efaa4a2927dc922d",
    # Exclude `_vendored` from ty (#24210) -- outbound sync to OSS reverted OSS PR #33807's
    # kinds tags plus #24193's pdf_extraction pyproject.toml change (9 files). Both were
    # re-applied by later syncs, so current state is consistent.
    "da5b67754949bb4fef00b549568f0dee298d58b2",
]

KNOWN_SKILLS_INBOUND_INCORRECTLY_SYNCED_COMMITS: list[str] = [
    # skills inbound sync carried extra copy.bara.sky change (race condition)
    "5a7a4860651c2630e3e30bb25651011ee41e2d02",
    "7e5e9efd0131f78b89e4cfd58266a92033c73942",
]

KNOWN_SKILLS_OUTBOUND_INCORRECTLY_SYNCED_COMMITS: list[str] = [
    # skills outbound syncs carried extra file changes (CHANGELOG.md,
    # scripts/release/changelog.py, CONTRIBUTING.md) due to race condition
    "019683d75c3d4b8ecc98232912e727d74589d9db",
    "77130e5db58f357f12e6c60f5c2257f14df8d4b5",
    "1b4c90176aae779c4e0bd1eb580d200dc93de083",
    # fix(copybara): update file:// origin URL (#23385) -- outbound sync to skills carried
    # 3 extra plugin.json bumps (.claude-plugin/plugin.json, dagster-expert, dignified-python)
    # from a stale skills snapshot
    "3f04acfbd53705f63124c034f74966339cc04481",
]


SYNC_CONFIGS: list[SyncConfig] = [
    SyncConfig(
        name="dagster-inbound",
        direction="inbound",
        public_repo_url="https://github.com/dagster-io/dagster.git",
        public_repo_slug="dagster",
        synced_label="Dagster-RevId",
        originated_label="Internal-RevId",
        internal_path="dagster-oss/",
        internal_path_prefix="dagster-oss/",
        file_renames=DAGSTER_FILE_RENAMES,
        known_incorrect=KNOWN_DAGSTER_INBOUND_INCORRECTLY_SYNCED_COMMITS,
        source_repo_name="dagster-io/dagster",
        dest_repo_name="dagster-io/internal",
    ),
    SyncConfig(
        name="dagster-outbound",
        direction="outbound",
        public_repo_url="https://github.com/dagster-io/dagster.git",
        public_repo_slug="dagster",
        synced_label="Internal-RevId",
        originated_label="Dagster-RevId",
        internal_path="dagster-oss/",
        internal_path_prefix="dagster-oss/",
        file_renames=DAGSTER_FILE_RENAMES,
        known_incorrect=KNOWN_DAGSTER_OUTBOUND_INCORRECTLY_SYNCED_COMMITS,
        source_repo_name="dagster-io/internal",
        dest_repo_name="dagster-io/dagster",
    ),
    SyncConfig(
        name="skills-inbound",
        direction="inbound",
        public_repo_url="https://github.com/dagster-io/skills.git",
        public_repo_slug="skills",
        synced_label="Skills-RevId",
        originated_label="Internal-RevId",
        internal_path="public/skills/",
        internal_path_prefix="public/skills/",
        file_renames={},
        known_incorrect=KNOWN_SKILLS_INBOUND_INCORRECTLY_SYNCED_COMMITS,
        source_repo_name="dagster-io/skills",
        dest_repo_name="dagster-io/internal",
    ),
    SyncConfig(
        name="skills-outbound",
        direction="outbound",
        public_repo_url="https://github.com/dagster-io/skills.git",
        public_repo_slug="skills",
        synced_label="Internal-RevId",
        originated_label="Skills-RevId",
        internal_path="public/skills/",
        internal_path_prefix="public/skills/",
        file_renames={},
        known_incorrect=KNOWN_SKILLS_OUTBOUND_INCORRECTLY_SYNCED_COMMITS,
        source_repo_name="dagster-io/internal",
        dest_repo_name="dagster-io/skills",
    ),
]


def get_sync_config(name: str) -> SyncConfig:
    """Get a sync config by name."""
    for config in SYNC_CONFIGS:
        if config.name == name:
            return config
    raise ValueError(f"Unknown sync config: {name}. Valid names: {[c.name for c in SYNC_CONFIGS]}")


def get_sync_configs_for_slug(slug: str) -> list[SyncConfig]:
    """Get all sync configs for a public repo slug (e.g. 'dagster' or 'skills')."""
    return [c for c in SYNC_CONFIGS if c.public_repo_slug == slug]
