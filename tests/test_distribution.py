import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from mcp_server import Server


class DistributionTests(unittest.TestCase):
    def test_tool_and_instruction_scope(self):
        name = json.loads((ROOT / '.codex-plugin/plugin.json').read_text())['name']
        server = Server()
        cad = {t['name'] for t in server.tools if t['name'].startswith('cad_')}
        expected = {'cad_inspect', 'cad_prepare', 'cad_execute', 'cad_result'} if name == 'autocad-cua' else set()
        self.assertEqual(cad, expected)
        self.assertEqual(len(server.tools), 18 if expected else 14)
        topics = server.by_name['instructions']['inputSchema']['properties']['topic']['enum']
        for topic in topics:
            self.assertTrue(server.call('instructions', {'topic': topic})['structuredContent']['instructions'])
        self.assertEqual({p.parent.name for p in (ROOT / 'skills').glob('*/SKILL.md')},
                         {'work', 'setup'} if expected else {'computer-use', 'setup'})
        if not expected:
            with self.assertRaises(ValueError): server.call('cad_inspect', {})
            with self.assertRaises(ValueError): server.call('instructions', {'topic': 'autocad'})
            self.assertFalse((ROOT / 'scripts/cad_bridge.py').exists())

    def test_skill_relative_links_resolve(self):
        for file in (ROOT / 'skills').rglob('*.md'):
            for link in re.findall(r'\]\(([^)]+)\)', file.read_text(encoding='utf-8')):
                if '://' in link or link.startswith('#'):
                    continue
                with self.subTest(file=file, link=link):
                    self.assertTrue((file.parent / link.split('#')[0]).resolve().exists())


if __name__ == '__main__': unittest.main()
