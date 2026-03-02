#!/usr/bin/env python3
"""
sort_xml - Sort XML elements according to a YAML configuration file.

Usage: python sort_xml.py <xml_file> [config_file]
  xml_file    - Path to the XML file to sort
  config_file - Path to YAML config (default: config.yml)

Output: Creates <xml_file>_sorted.xml with elements sorted as defined in config.
"""

import argparse
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

try:
    from lxml import etree as ET
    _PARSER = ET.XMLParser(strip_cdata=False)
except ImportError:
    import xml.etree.ElementTree as ET
    _PARSER = None


def load_config(config_path: Path) -> dict:
    """Load and return the YAML configuration."""
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_sort_key(element: ET.Element, sort_fields: list) -> tuple:
    """
    Build a sort key tuple for an element based on sort fields.
    Supports both child element text and attributes (use @attrname for attributes).
    """
    key_parts = []
    for field in sort_fields:
        if field.startswith("@"):
            attr_name = field[1:]
            key_parts.append(element.get(attr_name, "") or "")
        else:
            child = element.find(field)
            if child is not None and child.text is not None:
                key_parts.append(child.text.strip())
            else:
                key_parts.append("")
    # Use numeric sort when possible for fields that look like numbers
    result = []
    for part in key_parts:
        try:
            result.append((0, int(part)))
        except (ValueError, TypeError):
            result.append((1, str(part).lower()))
    return tuple(result)


def process_section(parent: ET.Element, child_tag: str, sort_fields: list) -> None:
    """Sort direct children of parent that have tag child_tag."""
    children = list(parent.findall(child_tag))
    if not children:
        return
    # Build list of (key, element), sort, then reorder in place
    keyed = [(get_sort_key(el, sort_fields), el) for el in children]
    keyed.sort(key=lambda x: x[0])
    # Remove all then append in sorted order (ElementTree doesn't have reorder API)
    for _, el in keyed:
        parent.remove(el)
    for _, el in keyed:
        parent.append(el)


def apply_spec(parent: ET.Element, spec: dict) -> None:
    """
    Recursively apply spec from config. Spec is a dict:
    - key = child element tag, value = list of sort fields -> sort those children
    - key = child element tag, value = dict -> descend and apply to that subtree
    """
    if not isinstance(spec, dict):
        return
    for child_tag, value in spec.items():
        if isinstance(value, list):
            process_section(parent, child_tag, value)
        elif isinstance(value, dict):
            sub = parent.find(child_tag)
            if sub is not None:
                apply_spec(sub, value)


def fix_xml_declaration_quotes(path: Path) -> None:
    """Rewrite the XML declaration to use double quotes instead of single."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if not text.startswith("<?xml"):
        return
    first_line = text.split("\n", 1)[0]
    fixed = re.sub(
        r"<\?xml version='([^']*)' encoding='([^']*)'\?>",
        r'<?xml version="\1" encoding="\2"?>',
        first_line,
    )
    if fixed != first_line:
        path.write_text(fixed + "\n" + text.split("\n", 1)[1], encoding="utf-8")


def apply_config(root: ET.Element, config: dict) -> None:
    """
    Apply config by document root tag: use the root element's tag to select which
    spec to apply (e.g. acquisition-configuration vs base-configuration).
    """
    spec = config.get(root.tag)
    if spec is not None and isinstance(spec, dict):
        apply_spec(root, spec)
    elif root.tag not in config:
        print(f"Note: root tag '<{root.tag}>' not in config; no sorting applied.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sort XML elements according to a YAML configuration file."
    )
    parser.add_argument(
        "xml_file",
        type=Path,
        help="Path to the XML file to sort",
    )
    parser.add_argument(
        "config_file",
        type=Path,
        nargs="?",
        default=Path("config.yml"),
        help="Path to YAML config file (default: config.yml)",
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        default=None,
        help="Output file path (default: <xml_file>_sorted.xml)",
    )
    args = parser.parse_args()

    if not args.xml_file.exists():
        print(f"Error: XML file not found: {args.xml_file}", file=sys.stderr)
        sys.exit(1)
    if not args.config_file.exists():
        print(f"Error: Config file not found: {args.config_file}", file=sys.stderr)
        sys.exit(1)

    config = load_config(args.config_file)
    if not config:
        print("Error: Config is empty.", file=sys.stderr)
        sys.exit(1)

    if _PARSER is not None:
        tree = ET.parse(args.xml_file, _PARSER)
    else:
        tree = ET.parse(args.xml_file)
    root = tree.getroot()

    apply_config(root, config)

    out_path = args.output or args.xml_file.with_stem(args.xml_file.stem + "_sorted")
    if _PARSER is not None:
        tree.write(
            out_path,
            encoding="utf-8",
            xml_declaration=True,
            method="xml",
        )
        fix_xml_declaration_quotes(out_path)
    else:
        tree.write(
            out_path,
            encoding="unicode",
            default_namespace="",
            method="xml",
            xml_declaration=True,
        )
        fix_xml_declaration_quotes(out_path)
    print(f"Sorted XML written to: {out_path}")


if __name__ == "__main__":
    main()
