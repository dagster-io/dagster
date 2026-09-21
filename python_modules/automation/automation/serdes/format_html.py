import re
from html import escape

from automation.serdes.format_text import simplify_type_str
from automation.serdes.models import BuiltinType, SerdesEnum, SerdesObject, SerdesUnion
from automation.serdes.registry import Registry, _extract_referenced_types


def _build_backlinks(registry: Registry) -> dict[str, list[str]]:
    """Build reverse index: for each type, which types reference it."""
    backlinks: dict[str, list[str]] = {}

    # Scan all types and their fields
    for typename, serdes_type in registry.types.items():
        for field in serdes_type.fields:
            if field.type_str:
                referenced = _extract_referenced_types(field.type_str)
                for ref in referenced:
                    if ref not in backlinks:
                        backlinks[ref] = []
                    backlinks[ref].append(typename)

        # Also track base class references
        if serdes_type.base_classes:
            for base in serdes_type.base_classes:
                if base not in backlinks:
                    backlinks[base] = []
                backlinks[base].append(typename)

    # Track union implementations
    for union_name, serdes_union in registry.unions.items():
        for impl in serdes_union.implementations:
            if impl not in backlinks:
                backlinks[impl] = []
            backlinks[impl].append(union_name)

    # Sort and deduplicate
    for typename in backlinks:
        backlinks[typename] = sorted(set(backlinks[typename]))

    return backlinks


def _linkify_typename(type_str: str, registry: Registry) -> str:
    """Convert type references to HTML links, with full type on hover."""
    if not type_str:
        return ""

    # Simplify for display
    simplified = simplify_type_str(type_str)

    # Find all capitalized type names in the simplified version
    pattern = r"\b([A-Z][a-zA-Z0-9_]*)\b"

    def replace_with_link(match):
        typename = match.group(1)
        # Determine type kind for title
        kind = None
        if typename in registry.types:
            kind = "object"
        elif typename in registry.enums:
            kind = "enum"
        elif typename in registry.unions:
            kind = "union"
        elif typename in registry.builtins:
            kind = "builtin"

        if kind:
            return f'<a href="#{typename}" title="{kind}: {typename}">{typename}</a>'
        return typename

    result = re.sub(pattern, replace_with_link, escape(simplified))

    # Wrap in span with full type as title (hover text)
    if simplified != type_str:
        return f'<span title="{escape(type_str)}">{result}</span>'
    return result


def _format_backlinks(typename: str, backlinks: dict[str, list[str]], registry: Registry) -> str:
    """Format collapsible backlinks section."""
    refs = backlinks.get(typename, [])
    if not refs:
        return ""

    lines = []
    lines.append('<details class="backlinks">')
    lines.append(f"<summary>Referenced by ({len(refs)})</summary>")
    lines.append("<ul>")
    for ref in refs:
        # Determine kind for badge
        if ref in registry.types:
            badge = '<span class="badge-mini badge-object">obj</span>'
        elif ref in registry.enums:
            badge = '<span class="badge-mini badge-enum">enum</span>'
        elif ref in registry.unions:
            badge = '<span class="badge-mini badge-union">union</span>'
        elif ref in registry.builtins:
            badge = '<span class="badge-mini badge-builtin">builtin</span>'
        else:
            badge = ""
        lines.append(f'<li>{badge} <a href="#{ref}">{escape(ref)}</a></li>')
    lines.append("</ul>")
    lines.append("</details>")
    return "\n".join(lines)


def format_enum_html(
    serdes_enum: SerdesEnum, registry: Registry, backlinks: dict[str, list[str]]
) -> str:
    lines = []
    lines.append(f'<div class="type-detail" id="{serdes_enum.typename}">')
    lines.append(
        f'<h3>{escape(serdes_enum.typename)} <span class="badge badge-enum">enum</span> <a href="#toc" class="backlink">↑</a></h3>'
    )
    lines.append('<div class="type-info">')
    lines.append(f"<div><strong>Storage Name:</strong> {escape(serdes_enum.storage_name)}</div>")
    lines.append(f"<div><strong>Type:</strong> <code>{escape(serdes_enum.class_type)}</code></div>")
    lines.append(
        f"<div><strong>Members:</strong> {', '.join(escape(m) for m in serdes_enum.members)}</div>"
    )

    # Add backlinks
    backlinks_html = _format_backlinks(serdes_enum.typename, backlinks, registry)
    if backlinks_html:
        lines.append(backlinks_html)

    lines.append("</div>")
    lines.append("</div>")
    return "\n".join(lines)


def format_union_html(
    serdes_union: SerdesUnion, registry: Registry, backlinks: dict[str, list[str]]
) -> str:
    lines = []
    lines.append(f'<div class="type-detail" id="{serdes_union.typename}">')
    lines.append(
        f'<h3>{escape(serdes_union.typename)} <span class="badge badge-union">union</span> <a href="#toc" class="backlink">↑</a></h3>'
    )
    lines.append('<div class="type-info">')
    lines.append(
        f"<div><strong>Type:</strong> <code>{escape(serdes_union.base_class)}</code></div>"
    )
    lines.append(
        f"<div><strong>Implementations ({len(serdes_union.implementations)}):</strong></div>"
    )
    lines.append("<ul>")
    for impl in serdes_union.implementations:
        if impl in registry.types:
            lines.append(f'<li><a href="#{impl}">{escape(impl)}</a></li>')
        else:
            lines.append(f"<li>{escape(impl)}</li>")
    lines.append("</ul>")

    # Add backlinks
    backlinks_html = _format_backlinks(serdes_union.typename, backlinks, registry)
    if backlinks_html:
        lines.append(backlinks_html)

    lines.append("</div>")
    lines.append("</div>")
    return "\n".join(lines)


def format_builtin_html(
    builtin: BuiltinType, registry: Registry, backlinks: dict[str, list[str]]
) -> str:
    lines = []
    lines.append(f'<div class="type-detail" id="{builtin.typename}">')
    lines.append(
        f'<h3>{escape(builtin.typename)} <span class="badge badge-builtin">builtin</span> <a href="#toc" class="backlink">↑</a></h3>'
    )
    lines.append('<div class="type-info">')
    lines.append(f"<div><strong>Description:</strong> {escape(builtin.description)}</div>")

    # Add backlinks
    backlinks_html = _format_backlinks(builtin.typename, backlinks, registry)
    if backlinks_html:
        lines.append(backlinks_html)

    lines.append("</div>")
    lines.append("</div>")
    return "\n".join(lines)


def format_type_html(
    serdes_type: SerdesObject, registry: Registry, backlinks: dict[str, list[str]]
) -> str:
    lines = []
    lines.append(f'<div class="type-detail" id="{serdes_type.typename}">')

    # Build header with badges
    badges = '<span class="badge badge-object">object</span>'
    if serdes_type.is_record:
        badges += ' <span class="badge badge-record">@record</span>'

    lines.append(
        f'<h3>{escape(serdes_type.typename)} {badges} <a href="#toc" class="backlink">↑</a></h3>'
    )
    lines.append('<div class="type-info">')
    lines.append(f"<div><strong>Storage Name:</strong> {escape(serdes_type.storage_name)}</div>")
    lines.append(f"<div><strong>Type:</strong> <code>{escape(serdes_type.class_type)}</code></div>")
    lines.append(f"<div><strong>Serializer:</strong> {escape(serdes_type.serializer_type)}</div>")

    if serdes_type.base_classes:
        base_links = []
        for base in serdes_type.base_classes:
            if base in registry.unions:
                base_links.append(f'<a href="#{base}">{escape(base)}</a>')
            else:
                base_links.append(escape(base))
        lines.append(f"<div><strong>Base Classes:</strong> {', '.join(base_links)}</div>")

    if serdes_type.fields:
        lines.append(f"<div><strong>Fields ({len(serdes_type.fields)}):</strong></div>")
        lines.append('<table class="fields">')
        for field in serdes_type.fields:
            if field.type_str:
                linked_type = _linkify_typename(field.type_str, registry)
                lines.append(
                    f"<tr><td><code>{escape(field.name)}</code></td><td>{linked_type}</td></tr>"
                )
            else:
                lines.append(f"<tr><td><code>{escape(field.name)}</code></td><td></td></tr>")
        lines.append("</table>")

    if serdes_type.field_mappings:
        lines.append("<div><strong>Field Mappings:</strong></div>")
        lines.append("<ul>")
        for field, storage in serdes_type.field_mappings.items():
            lines.append(f"<li>{escape(field)} → {escape(storage)}</li>")
        lines.append("</ul>")

    if serdes_type.old_fields:
        lines.append("<div><strong>Old Fields (backward compat):</strong></div>")
        lines.append("<ul>")
        for field, default in serdes_type.old_fields.items():
            lines.append(f"<li>{escape(field)} = {escape(str(default))}</li>")
        lines.append("</ul>")

    if serdes_type.skip_when_empty:
        lines.append(
            f"<div><strong>Skip When Empty:</strong> {', '.join(escape(f) for f in serdes_type.skip_when_empty)}</div>"
        )

    if serdes_type.skip_when_none:
        lines.append(
            f"<div><strong>Skip When None:</strong> {', '.join(escape(f) for f in serdes_type.skip_when_none)}</div>"
        )

    # Add backlinks
    backlinks_html = _format_backlinks(serdes_type.typename, backlinks, registry)
    if backlinks_html:
        lines.append(backlinks_html)

    lines.append("</div>")
    lines.append("</div>")
    return "\n".join(lines)


def format_html(registry: Registry) -> str:
    """Generate complete HTML document with TOC and type details."""
    # Build backlinks index
    backlinks = _build_backlinks(registry)

    lines = []

    # HTML header
    lines.append("<!DOCTYPE html>")
    lines.append("<html>")
    lines.append("<head>")
    lines.append('<meta charset="UTF-8">')
    lines.append("<title>Serdes Type Registry</title>")
    lines.append("<style>")
    lines.append("""
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; max-width: 1200px; margin: 40px auto; padding: 0 20px; }
h1 { border-bottom: 2px solid #333; padding-bottom: 10px; }
h2 { margin-top: 40px; border-bottom: 1px solid #666; padding-bottom: 8px; }
h3 { margin-top: 30px; color: #0366d6; }
.toc { background: #f6f8fa; padding: 20px; border-radius: 6px; margin: 20px 0; }
.toc ul { columns: 3; column-gap: 20px; list-style: none; padding-left: 0; }
.toc li { break-inside: avoid; }
.type-detail { margin: 30px 0; padding: 20px; border: 1px solid #e1e4e8; border-radius: 6px; }
.type-info { margin-top: 10px; }
.type-info > div { margin: 8px 0; }
.fields { margin: 10px 0; border-collapse: collapse; width: 100%; }
.fields td { padding: 4px 12px; border-bottom: 1px solid #e1e4e8; }
.fields td:first-child { width: 30%; font-weight: 500; }
.backlink { float: right; text-decoration: none; color: #666; font-size: 0.9em; }
.backlink:hover { color: #0366d6; }
.badge { display: inline-block; padding: 2px 8px; margin-left: 8px; border-radius: 3px; font-size: 0.75em; font-weight: 600; text-transform: uppercase; }
.badge-object { background: #dff0ff; color: #0366d6; }
.badge-enum { background: #fff4dd; color: #9a6700; }
.badge-union { background: #e8dff5; color: #6f42c1; }
.badge-builtin { background: #f0f0f0; color: #586069; }
.badge-record { background: #d1f0d1; color: #22863a; text-transform: none; }
.badge-mini { display: inline-block; padding: 1px 4px; margin-right: 4px; border-radius: 2px; font-size: 0.65em; font-weight: 600; text-transform: uppercase; }
code { background: #f6f8fa; padding: 2px 6px; border-radius: 3px; font-family: "SFMono-Regular", Consolas, monospace; }
a { color: #0366d6; text-decoration: none; }
a:hover { text-decoration: underline; }
.stats { margin: 20px 0; padding: 15px; background: #f6f8fa; border-radius: 6px; }
.backlinks { margin-top: 16px; padding: 12px; background: #f6f8fa; border-radius: 4px; }
.backlinks summary { cursor: pointer; font-weight: 600; color: #666; user-select: none; }
.backlinks summary:hover { color: #0366d6; }
.backlinks ul { margin: 8px 0 0 0; padding-left: 0; list-style: none; }
.backlinks li { margin: 4px 0; }
    """)
    lines.append("</style>")
    lines.append("</head>")
    lines.append("<body>")

    # Title
    lines.append("<h1>Serdes Type Registry</h1>")

    # Stats
    lines.append('<div class="stats">')
    lines.append(f"<strong>Total Types:</strong> {registry.size} ")
    lines.append(
        f"({len(registry.types)} objects, {len(registry.enums)} enums, {len(registry.unions)} unions, {len(registry.builtins)} builtins)"
    )
    lines.append("</div>")

    # Table of Contents
    lines.append('<div class="toc" id="toc">')
    lines.append("<h2>Table of Contents</h2>")

    # Objects TOC
    lines.append("<h3>Objects</h3>")
    lines.append("<ul>")
    lines.extend(
        f'<li><a href="#{typename}">{escape(typename)}</a></li>'
        for typename in sorted(registry.types.keys())
    )
    lines.append("</ul>")

    # Enums TOC
    lines.append("<h3>Enums</h3>")
    lines.append("<ul>")
    lines.extend(
        f'<li><a href="#{typename}">{escape(typename)}</a></li>'
        for typename in sorted(registry.enums.keys())
    )
    lines.append("</ul>")

    # Unions TOC
    lines.append("<h3>Unions</h3>")
    lines.append("<ul>")
    lines.extend(
        f'<li><a href="#{typename}">{escape(typename)}</a></li>'
        for typename in sorted(registry.unions.keys())
    )
    lines.append("</ul>")

    # Builtins TOC
    lines.append("<h3>Builtins</h3>")
    lines.append("<ul>")
    lines.extend(
        f'<li><a href="#{typename}">{escape(typename)}</a></li>'
        for typename in sorted(registry.builtins.keys())
    )
    lines.append("</ul>")

    lines.append("</div>")

    # Type Details
    lines.append("<h2>Object Types</h2>")
    lines.extend(
        format_type_html(registry.types[typename], registry, backlinks)
        for typename in sorted(registry.types.keys())
    )

    # Enum Details
    lines.append("<h2>Enum Types</h2>")
    lines.extend(
        format_enum_html(registry.enums[typename], registry, backlinks)
        for typename in sorted(registry.enums.keys())
    )

    # Union Details
    lines.append("<h2>Union Types</h2>")
    lines.extend(
        format_union_html(registry.unions[typename], registry, backlinks)
        for typename in sorted(registry.unions.keys())
    )

    # Builtin Details
    lines.append("<h2>Builtin Types</h2>")
    lines.extend(
        format_builtin_html(registry.builtins[typename], registry, backlinks)
        for typename in sorted(registry.builtins.keys())
    )

    lines.append("</body>")
    lines.append("</html>")

    return "\n".join(lines)
