"""Stdio MCP access to the existing guarded Cua client; no shell tool exposed."""
import json
import os
from pathlib import Path
import sys
import uuid
from run_sequence import Client
from runtime import ROOT, driver_path
from cad_bridge import CadBridge


def result(data):
    return {'content': [{'type': 'text', 'text': json.dumps(data, ensure_ascii=False)}],
            'structuredContent': data}


def schema(name, description, properties=None, required=None):
    return {'name': name, 'description': description, 'inputSchema': {
        'type': 'object', 'properties': properties or {}, 'required': required or [],
        'additionalProperties': False}}


class Server:
    def __init__(self):
        self.client = None
        self.session = None
        self.tools = json.loads((ROOT / 'scripts/mcp-tools.json').read_text(encoding='utf-8'))
        for tool in self.tools:
            mode = tool['inputSchema']['properties'].get('delivery_mode')
            if mode is not None:
                mode.pop('const', None)
                mode['enum'] = ['background', 'foreground']
                mode['description'] = 'Foreground requires a session explicitly authorized for interruption; default to background.'
        self.tools += [
            schema('status', 'Verify this plugin and its pinned driver; no app interaction.'),
            schema('instructions', 'Read bundled instructions without filesystem or shell access.',
                   {'topic': {'type': 'string', 'enum': ['computer-use', 'autocad', 'setup']}}, ['topic']),
            schema('start_session', 'Acquire one GUI workflow. Only set allow_interruption when the user explicitly permits foreground control.',
                   {'allow_interruption': {'type': 'boolean', 'default': False}}),
            schema('launch_app', 'Launch an exact executable minimized, observing startup focus. Discover and verify the resulting window before input.',
                   {'session': {'type': 'string'}, 'path': {'type': 'string'},
                    'start_minimized': {'type': 'boolean'}}, ['session', 'path', 'start_minimized']),
            schema('end_session', 'Release this workflow without closing or modifying the app.',
                   {'session': {'type': 'string'}}, ['session'])]
        self.tools += [
            schema('cad_inspect','Read live AutoCAD identity, units and optional bounded geometry. Does not launch AutoCAD.',
                   {'pid':{'type':'integer'},'max_entities':{'type':'integer','minimum':0,'maximum':10000},'handles':{'type':'array','items':{'type':'string'}}}),
            schema('cad_prepare','Freeze task-specific, noninteractive AutoLISP and a drawing precondition. Returns exact hash; does not execute. Trusted code, not a sandbox.',
                   {'target':{'type':'object'},'code':{'type':'string'},'precondition':{'type':'string'},'description':{'type':'string'},'undo_group':{'type':'boolean','default':True}},['target','code','precondition','description']),
            schema('cad_execute','Execute one prepared native job once. Requires its exact hash. Inspect geometry afterward; execution is not acceptance.',
                   {'job':{'type':'string'},'sha256':{'type':'string'},'allow_interruption':{'type':'boolean','default':False}},['job','sha256']),
            schema('cad_result','Retrieve native outcome without replay. After inspecting/recovering an uncertain job, resolve_after_inspection checks idle target and permits a new job; it does not mark the old job successful.',{'job':{'type':'string'},'resolve_after_inspection':{'type':'boolean','default':False}},['job'])]
        self.by_name = {t['name']: t for t in self.tools}

    def call(self, name, args):
        if name not in self.by_name:
            raise ValueError('Unknown plugin tool.')
        shape = self.by_name[name]['inputSchema']
        if not isinstance(args, dict) or set(args) - set(shape['properties']) or set(shape['required']) - set(args):
            raise ValueError('Unexpected or missing tool arguments.')
        if name.startswith('cad_'):
            if name=='cad_execute' and self.client is not None:
                raise RuntimeError('End the Cua session before native execution; both routes share ownership.')
            bridge=CadBridge()
            return result(getattr(bridge,name[4:])(**args))
        if name == 'status':
            pinned = driver_path()
            return result({'plugin_version': json.loads((ROOT / '.codex-plugin/plugin.json').read_text())['version'],
                'driver': pinned, 'runtime': json.loads((ROOT / 'runtime.json').read_text()),
                'active_session': self.client is not None, 'agent_shell_required': False})
        if name == 'instructions':
            topics = {'computer-use': ['work/references/gui.md', 'work/references/gui-recovery.md'],
                      'autocad': ['work/SKILL.md', 'work/references/native.md'], 'setup': ['setup/SKILL.md']}
            if args['topic'] not in topics:
                raise ValueError('Unknown instruction topic.')
            return result({'instructions': '\n\n'.join((ROOT / 'skills' / p).read_text(encoding='utf-8') for p in topics[args['topic']])})
        if name == 'start_session':
            if type(args.get('allow_interruption', False)) is not bool:
                raise ValueError('allow_interruption must be a boolean.')
            if self.client is not None:
                raise RuntimeError('A workflow already owns this connection; finish it before starting another.')
            session = uuid.uuid4().hex
            output = Path(os.environ['LOCALAPPDATA']) / 'AutoCAD-Cua/evidence' / session
            output.mkdir(parents=True, exist_ok=False)
            self.client = Client(driver_path(), output, allow_interruption=args.get('allow_interruption', False))
            self.session = session
            return result({'session': session, 'evidence': str(output)})
        if self.client is None or args.get('session') != self.session:
            raise RuntimeError('Use the session returned by start_session for this workflow.')
        if name == 'end_session':
            self.close()
            return result({'ended': True, 'app_closed': False})
        forwarded = {k: v for k, v in args.items() if k != 'session'}
        return self.client.call(name, forwarded)[0]

    def close(self):
        if self.client:
            try:
                self.client.close()
            finally:
                self.client = None
                self.session = None


def main():
    server = Server()
    try:
        for line in sys.stdin:
            request = {}
            try:
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError('Expected a JSON-RPC object.')
                if 'id' not in request:
                    continue
                method = request.get('method')
                if method == 'initialize':
                    response = {'protocolVersion': '2024-11-05', 'capabilities': {'tools': {}},
                                'serverInfo': {'name': 'autocad-cua', 'version': '1'}}
                elif method == 'ping':
                    response = {}
                elif method == 'tools/list':
                    response = {'tools': server.tools}
                elif method == 'tools/call':
                    params = request['params']
                    try:
                        response = server.call(params['name'], params.get('arguments', {}))
                    except Exception as error:
                        response = {'isError': True, 'content': [{'type': 'text', 'text': str(error)}]}
                else:
                    raise ValueError('Unsupported MCP method.')
                envelope = {'jsonrpc': '2.0', 'id': request['id'], 'result': response}
            except Exception as error:
                envelope = {'jsonrpc': '2.0', 'id': request.get('id') if isinstance(request, dict) else None,
                            'error': {'code': -32600, 'message': str(error)}}
            print(json.dumps(envelope, ensure_ascii=False), flush=True)
    finally:
        server.close()


if __name__ == '__main__':
    main()
