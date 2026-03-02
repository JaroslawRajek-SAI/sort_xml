# sort_xml

Sort XML elements according to a YAML configuration. Output is written to a new file (by default `<name>_sorted.xml`).

**Requirements:** Python 3, PyYAML (`pip install pyyaml`). For **CDATA preservation**, lxml is used when available (`pip install lxml`); otherwise the standard library is used and CDATA sections become escaped text.

## Usage

```bash
python sort_xml.py <xml_file> [config_file] [-o output_file]
```

- **xml_file** — XML file to sort (required)
- **config_file** — YAML config (optional; default: `config.yml`)
- **-o, --output** — Output path (optional; default: `<xml_file>_sorted.xml`)

### Examples

```bash
# Use default config.yml in current directory
python sort_xml.py POLITIET_services-configuration.xml

# Specify config and output file
python sort_xml.py POLITIET_services-configuration.xml config.yml -o result.xml
```

## Config format

The top-level keys in the config are **document root tag names**. They identify the type of configuration file (e.g. `acquisition-configuration` for services, `base-configuration` for base). The script uses the XML root element’s tag to choose which spec to apply.

Under each root-tag key, the structure is the same as before: child tags and their sort rules.

- **List of field names** — sort direct children with that tag by those fields (element text; use `@attr` for attributes).
- **Nested dict** — apply rules to the first direct child with that tag (recursive).

### Sample config (services + base)

```yaml
acquisition-configuration:   # root of POLITIET_services-configuration.xml
  sequences:
    sequence:
      - name
    sequence-functions:
      sequence-function:
        - order
        - name

base-configuration:           # root of POLITIET_base-configuration.xml
  external-connectors:
    external-connector:
      - name
```

If the file’s root tag is not in the config, no sorting is applied and a note is printed.
