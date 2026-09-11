import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from check_driver_compatibility import differences, inspect_candidate


class CompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.schema = {'type': 'object', 'required': ['pid'], 'additionalProperties': False,
                       'properties': {'pid': {'type': 'integer'},
                                      'delivery_mode': {'enum': ['background'], 'default': 'background'}}}

    def test_additive_changes_do_not_require_adapter_rewrites(self):
        new = copy.deepcopy(self.schema)
        new['description'] = 'New documentation'
        new['properties']['optional'] = {'type': 'string'}
        new['properties']['delivery_mode']['enum'].append('foreground')
        new['required'] = []
        self.assertEqual(differences(self.schema, new), [])

    def test_removed_fields_new_requirements_types_and_defaults_are_reported(self):
        for change in ('remove', 'required', 'type', 'default', 'enum'):
            with self.subTest(change=change):
                new = copy.deepcopy(self.schema)
                if change == 'remove': del new['properties']['pid']
                if change == 'required': new['required'].append('other')
                if change == 'type': new['properties']['pid']['type'] = 'string'
                if change == 'default': new['properties']['delivery_mode']['default'] = 'foreground'
                if change == 'enum': new['properties']['delivery_mode']['enum'] = ['foreground']
                self.assertTrue(differences(self.schema, new))

    def test_metadata_probe_never_invokes_input_or_installs(self):
        def cli(driver, *args):
            if args == ('manifest',):
                return json.dumps({'binary_version': 'future', 'subcommands': [{'name': 'mcp', 'args': [{'name': '--direct'}]}]})
            if args == ('--help',): return '--no-overlay'
            if args == ('describe', 'click'): return 'input_schema:\n' + json.dumps(self.schema)
            self.fail('Unexpected candidate operation: ' + str(args))
        with tempfile.TemporaryDirectory() as folder, patch('check_driver_compatibility.read_cli', side_effect=cli):
            driver = Path(folder) / 'driver.exe'; driver.write_bytes(b'candidate')
            report = inspect_candidate(driver, {'tools': {'click': self.schema}})
            self.assertTrue(report['input_contract_matches'])
            self.assertFalse(report['live_app_behavior_verified'])
            self.assertFalse(report['installed_driver_changed'])

    def test_bad_checksum_never_executes_candidate(self):
        with tempfile.TemporaryDirectory() as folder, patch('check_driver_compatibility.read_cli') as cli:
            driver = Path(folder) / 'driver.exe'; driver.write_bytes(b'candidate')
            with self.assertRaisesRegex(ValueError, 'checksum'):
                inspect_candidate(driver, {'tools': {}}, '0' * 64)
            cli.assert_not_called()

    def test_property_names_and_literal_defaults_are_not_annotations(self):
        schema = {'properties': {'title': {'type': 'string'}, 'value': {'default': {'description': 'old'}}}}
        self.assertTrue(differences(schema, {'properties': {'value': {'default': {'description': 'new'}}}}))

    def test_baseline_covers_every_supported_driver_tool(self):
        from background_guard import INPUTS, READS, LIFECYCLE
        baseline = json.loads((Path(__file__).resolve().parents[1] / 'source/driver-contract.json').read_text())
        self.assertEqual(set(baseline['tools']), INPUTS | READS | LIFECYCLE)

    def test_missing_tools_and_launch_flags_are_reported(self):
        with tempfile.TemporaryDirectory() as folder, patch('check_driver_compatibility.read_cli', side_effect=[
                json.dumps({'subcommands': []}), '', 'Unknown tool']):
            driver = Path(folder) / 'driver.exe'; driver.write_bytes(b'candidate')
            report = inspect_candidate(driver, {'tools': {'click': self.schema}})
            self.assertFalse(report['input_contract_matches'])
            self.assertEqual(len(report['differences']), 3)


if __name__ == '__main__': unittest.main()
