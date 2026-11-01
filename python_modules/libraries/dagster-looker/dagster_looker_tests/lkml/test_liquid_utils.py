import textwrap

from dagster_looker.lkml.liquid_utils import best_effort_render_liquid_sql


def _render(sql: str) -> str:
    return best_effort_render_liquid_sql("my_view", "my_view.view.lkml", sql)


# ########################
# ##### TESTS
# ########################


def test_render_condition_tag() -> None:
    # A top-level condition renders its body unconditionally.
    assert (
        _render("SELECT * FROM orders WHERE {% condition holiday %} holiday {% endcondition %}")
        == "SELECT * FROM orders WHERE  holiday "
    )

    # Enclosing tags drop blocks whose contents are blank, so a condition must report the
    # blankness of its body rather than claiming to be blank itself.
    assert (
        _render(
            textwrap.dedent("""
                {% if true %}
                {% condition order_filter %}SELECT * FROM analytics.orders{% endcondition %}
                {% endif %}
            """).strip()
        ).strip()
        == "SELECT * FROM analytics.orders"
    )
    assert (
        _render(
            "{% capture body %}{% condition order_filter %}"
            "SELECT * FROM analytics.orders"
            "{% endcondition %}{% endcapture %}{{ body }}"
        )
        == "SELECT * FROM analytics.orders"
    )
    assert (
        _render(
            "{% unless false %}{% condition order_filter %}"
            "SELECT * FROM analytics.orders"
            "{% endcondition %}{% endunless %}"
        )
        == "SELECT * FROM analytics.orders"
    )


def test_render_date_tags() -> None:
    assert (
        _render(
            "SELECT * FROM orders WHERE created_at BETWEEN"
            " {% date_start orders.created_at %} AND {% date_end orders.created_at %}"
        )
        == "SELECT * FROM orders WHERE created_at BETWEEN '2021-01-01' AND '2021-01-01'"
    )


def test_render_invalid_liquid_returns_sql_unchanged() -> None:
    sql = "SELECT * FROM orders WHERE {% condition holiday %} holiday"
    assert _render(sql) == sql
