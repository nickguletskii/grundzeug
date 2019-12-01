from argparse import ArgumentParser

from grundzeug.config.providers.argparse import ArgParseConfigurationProvider
from grundzeug.config.providers.common import DictTreeConfigurationProvider
from tests.config.test_config import ExampleConfigurationClass


class TestProviders:
    def test_argparser_provider(self):
        provider = ArgParseConfigurationProvider()
        arg_parser = ArgumentParser()
        provider.manage_configuration(ExampleConfigurationClass)
        provider.register_arguments(arg_parser)
        args = arg_parser.parse_args(["--Dfoo.bar.baz", "42"])
        provider.process_parsed_arguments(args)
        assert provider.get_value(["foo", "bar", "baz"]) == 42

    def test_dict_tree_provider(self):
        provider = DictTreeConfigurationProvider({})
        provider.set_value(ExampleConfigurationClass.property, 42)
        assert provider.get_value(["foo", "bar", "baz"]) == 42
