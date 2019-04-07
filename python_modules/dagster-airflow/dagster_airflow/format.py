from dagster import check
from dagster.utils.indenting_printer import IndentingStringIoPrinter


def format_config_for_graphql(config):
    '''This recursive descent thing formats a config dict for GraphQL.'''

    def _format_config_subdict(config, current_indent=0):
        check.dict_param(config, 'config', key_type=str)

        printer = IndentingStringIoPrinter(indent_level=2, current_indent=current_indent)
        printer.line('{')

        n_elements = len(config)
        for i, key in enumerate(sorted(config, key=lambda x: x[0])):
            value = config[key]
            with printer.with_indent():
                formatted_value = (
                    _format_config_item(value, current_indent=printer.current_indent)
                    .lstrip(' ')
                    .rstrip('\n')
                )
                printer.line(
                    '{key}: {formatted_value}{comma}'.format(
                        key=key,
                        formatted_value=formatted_value,
                        comma=',' if i != n_elements - 1 else '',
                    )
                )
        printer.line('}')

        return printer.read()

    def _format_config_sublist(config, current_indent=0):
        printer = IndentingStringIoPrinter(indent_level=2, current_indent=current_indent)
        printer.line('[')

        n_elements = len(config)
        for i, value in enumerate(config):
            with printer.with_indent():
                formatted_value = (
                    _format_config_item(value, current_indent=printer.current_indent)
                    .lstrip(' ')
                    .rstrip('\n')
                )
                printer.line(
                    '{formatted_value}{comma}'.format(
                        formatted_value=formatted_value, comma=',' if i != n_elements - 1 else ''
                    )
                )
        printer.line(']')

        return printer.read()

    def _format_config_item(config, current_indent=0):
        printer = IndentingStringIoPrinter(indent_level=2, current_indent=current_indent)

        if isinstance(config, dict):
            return _format_config_subdict(config, printer.current_indent)
        elif isinstance(config, list):
            return _format_config_sublist(config, printer.current_indent)
        elif isinstance(config, bool):
            return repr(config).lower()
        else:
            return repr(config).replace('\'', '"')

    check.dict_param(config, 'config', key_type=str)
    if not isinstance(config, dict):
        check.failed('Expected a dict to format as config, got: {item}'.format(item=repr(config)))

    return _format_config_subdict(config)
