"""The SQL Server revision tree, and the record of what it is reconciled against.

dagster-mysql and dagster-postgres share the revision tree in dagster core.
dagster-mssql cannot: that tree carries per-dialect branches emitting DDL that is invalid
on SQL Server, and none of its revisions have ever been run against one. So this package
ships its own tree, which means it does *not* pick up new core migrations for free.

That creates a failure mode with no natural symptom. A fresh SQL Server deployment builds
its schema with ``MetaData.create_all()`` and stamps the head, so it is always correct and
a missing migration is invisible. An *existing* deployment upgrades by running
``dagster instance migrate``, which walks this tree and silently does nothing for any core
migration that was never ported. The schema then lags the code, and the first
symptom is a query against a column that does not exist.

``SYNCED_TO_CORE_REVISION`` is the tripwire. It records the head of core's tree at the
last time this tree was reconciled against it, and ``test_migrations.py`` fails as soon as
core's head moves. When that happens, for each new core revision either:

* port it, adding a revision here that has the same effect on SQL Server, or
* establish that it does not apply (it is a MySQL- or Postgres-only branch, or it touches
  something SQL Server builds differently),

then note the decision in ``CORE_REVISIONS_NOT_APPLICABLE`` below and advance
``SYNCED_TO_CORE_REVISION``. Advancing it without doing that work is the one thing that
turns a loud failure back into a silent one.
"""

# Head of `dagster:_core/storage/alembic` that this tree has been reconciled against.
SYNCED_TO_CORE_REVISION = "29b539ebc72a"

# Core revisions deliberately not ported, and why. Keyed by core revision id.
CORE_REVISIONS_NOT_APPLICABLE = {
    "29b539ebc72a": (
        "MySQL-only: widens bulk_actions.body to LONGTEXT. On SQL Server that column is"
        " already NVARCHAR(max), which has no equivalent limit to raise."
    ),
}
