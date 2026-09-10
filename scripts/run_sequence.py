"""Prompt-checked AutoCAD GUI commands over one persistent Cua MCP connection."""
import argparse
import json
import os
from pathlib import Path
import queue
import re
import subprocess
import threading
import time
import uuid
from runtime import driver_path
from desktop_lease import DesktopLease
from background_guard import BackgroundWatch, window_process, INPUTS, READS, LIFECYCLE


def command_editor_present(result):
    return bool(re.search(r'\] Edit [^\n]*\[id=local:AutoCompleteEdit_1(?: |\])',
                          result.get('structuredContent', {}).get('tree_markdown', '')))


def prompt_of(result):
    data = result.get('structuredContent', {})
    tree = data.get('tree_markdown')
    if not tree:
        tree = '\n'.join(b.get('text', '') for b in result.get('content', []) if b.get('type') == 'text')
    parts = []
    for line in tree.splitlines():
        if re.search(r'\] Edit ', line):
            break
        match = re.match(r'\s*- Text "(.*)"$', line)
        if match:
            parts.append(match.group(1))
    return ' '.join(parts).strip(), data


class Client:
    def __init__(self, driver, output, *, show_overlay=False, allow_interruption=False):
        if type(allow_interruption) is not bool:
            raise ValueError('allow_interruption must be an explicit boolean.')
        self.allow_interruption = allow_interruption
        pinned = driver_path()
        if Path(driver).resolve() != Path(pinned).resolve():
            raise ValueError('Use this plugin\'s verified bundled driver; no alternate driver was launched.')
        self.lease = DesktopLease()
        self.log = None
        self.process = None
        try:
            self.log = (output / 'driver-stderr.log').open('x', encoding='utf-8')
            (output / 'runtime.json').write_text(json.dumps({
                'driver': pinned,
                'identity': json.loads((Path(pinned).parent.parent / 'runtime.json').read_text(encoding='utf-8')),
                'process_owner': os.getpid(), 'allow_interruption': allow_interruption}, indent=2), encoding='utf-8')
            self.process = subprocess.Popen(
                [pinned, 'mcp', '--direct'] + ([] if show_overlay else ['--no-overlay']),
                stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=self.log, text=True, encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
        except BaseException:
            if self.log:
                self.log.close()
            self.lease.close()
            raise
        self.lines = queue.Queue()
        def read():
            for line in self.process.stdout:
                self.lines.put(line)
            self.lines.put(None)
        threading.Thread(target=read, daemon=True).start()
        self.serial = 0
        self.output = output
        self.session = 'autocad-' + uuid.uuid4().hex[:12]
        self.background_fault = None
        self.input_fault = None
        try:
            self.rpc('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                                   'clientInfo': {'name': 'autocad-cua-sequence', 'version': '1'}})
            self.process.stdin.write(json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) + '\n')
            self.process.stdin.flush()
            self.call('start_session', {})
        except BaseException:
            self.stop_process()
            raise

    def rpc(self, method, params):
        self.serial += 1
        ident = self.serial
        self.process.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': ident, 'method': method, 'params': params}) + '\n')
        self.process.stdin.flush()
        deadline = time.monotonic() + 30
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:
                raise TimeoutError('Cua response timed out; no input was replayed.')
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as error:
                raise TimeoutError('Cua response timed out; no input was replayed.') from error
            if line is None:
                raise RuntimeError('Cua MCP exited; no input will be repeated.')
            response = json.loads(line)
            if response.get('id') == ident:
                if response.get('error'):
                    raise RuntimeError(str(response['error']))
                return response['result']

    def call(self, name, arguments):
        interactive = getattr(self, 'allow_interruption', False)
        if name not in INPUTS | READS | LIFECYCLE:
            raise ValueError('This background client accepts guarded window input, observations and session lifecycle only.')
        if name in INPUTS:
            if getattr(self, 'input_fault', None):
                raise RuntimeError('Earlier input failed or is uncertain; further input blocked. Observe the app before recovery.')
            if self.background_fault:
                raise RuntimeError('Background context changed earlier; further input blocked. Observe before choosing a different supported route.')
            if name == 'launch_app':
                path = arguments.get('path')
                if not isinstance(path, str) or not Path(path).is_absolute() or not Path(path).is_file() or Path(path).suffix.lower() != '.exe' or type(arguments.get('start_minimized')) is not bool or (not arguments['start_minimized'] and not interactive) or set(arguments) - {'path', 'start_minimized'}:
                    raise ValueError('Launch requires an existing absolute executable path and explicit start_minimized:true, without extra arguments.')
            elif arguments.get('delivery_mode') not in ({'background', 'foreground'} if interactive else {'background'}) or not all(
                type(arguments.get(k)) is int and arguments[k] > 0 for k in ('pid', 'window_id')
            ) or arguments.get('target') is not None or arguments.get('scope', 'window') != 'window' or any(
                k in arguments for k in ('desktop_id', 'display_id', 'screen_id')
            ):
                raise ValueError('Client input requires exact PID/HWND and explicit background delivery without target overrides.')
        args = dict(arguments, session=self.session)
        started = time.perf_counter()
        watch = BackgroundWatch().start() if name in INPUTS else None
        if name in INPUTS:
            self.input_fault = 'Input outcome or evidence is incomplete'
        dispatched = False
        try:
            if watch and name != 'launch_app':
                if interactive:
                    if window_process(arguments['window_id']) != arguments['pid']:
                        raise RuntimeError('Target window ownership changed; no input sent.')
                else:
                    watch.check_target(arguments['pid'], arguments['window_id'])
            dispatched = True
            result = self.rpc('tools/call', {'name': name, 'arguments': args})
            if name == 'launch_app':
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline and not watch.change:
                    time.sleep(.1)
        except BaseException as error:
            if name in INPUTS:
                self.input_fault = str(error) or type(error).__name__
            (self.output / f'{self.serial:04d}-{name}-error.json').write_text(json.dumps({
                'tool': name, 'arguments': args,
                'elapsed_ms': (time.perf_counter() - started) * 1000,
                'error': str(error), 'input_uncertain': name in INPUTS and dispatched,
                'note': 'No replay. Inspect application state before recovery.'}, indent=2), encoding='utf-8')
            raise
        finally:
            if watch:
                change = watch.finish()
                self.background_fault = change if not interactive else None
                if change:
                    (self.output / 'background-change.json').write_text(json.dumps(
                        {'tool': name, 'arguments': args, 'observation': change, 'allow_interruption': interactive,
                         'note': 'Action may have executed. No focus restoration or replay.'}, indent=2), encoding='utf-8')
        elapsed = (time.perf_counter() - started) * 1000
        evidence = {'tool': name, 'arguments': args, 'elapsed_ms': elapsed, 'result': result}
        (self.output / f'{self.serial:04d}-{name}.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding='utf-8')
        if self.background_fault and name in INPUTS:
            raise RuntimeError('Foreground window or keyboard focus changed during input; further input blocked. Action may have executed; inspect evidence, do not replay.')
        data = result.get('structuredContent') or {}
        if result.get('isError') or data.get('status') in ('refused', 'failed', 'error') or data.get('code') == 'background_unavailable':
            if name in INPUTS:
                self.input_fault = f'{name} refused or failed'
            raise RuntimeError(f'{name} refused or failed; inspect {self.output}. No retry was sent.')
        if name in INPUTS:
            self.input_fault = None
        return result, elapsed

    def close(self):
        try:
            self.call('end_session', {})
        except Exception as error:
            (self.output / 'cleanup-error.txt').write_text(str(error), encoding='utf-8')
        finally:
            self.stop_process()

    def stop_process(self):
        try:
            try:
                self.process.stdin.close()
            except (OSError, ValueError):
                pass
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.terminate()
                self.process.wait(timeout=5)
        finally:
            # A timed-out termination is still an owner, even during cleanup.
            if self.process.poll() is not None:
                self.log.close()
                self.lease.close()


def title_key(title):
    return re.sub(r'\*(?=\]?$)', '', title.strip()).casefold()


def read_prompt(client, palette, expected, full=False):
    """A shallow prompt is usable only when its known command edit is present.

    Missing editor or unexpected text falls back to the original depth before
    the caller decides whether to wait or stop. Both observations are logged.
    """
    if not full:
        result, elapsed = client.call('get_window_state', dict(palette, max_depth=2))
        prompt, data = prompt_of(result)
        if command_editor_present(result) and re.search(expected, prompt, re.IGNORECASE):
            return result, elapsed
    else:
        elapsed = 0
    result, wide_ms = client.call('get_window_state', dict(palette, max_depth=5))
    if not command_editor_present(result):
        raise RuntimeError('AutoCAD command editor missing from full snapshot; no further input sent.')
    return result, elapsed + wide_ms


def run(options, client=None):
    wall_started = time.perf_counter()
    if min(options.pid, options.window, options.command_window) <= 0:
        raise ValueError('PID and both window handles must be positive.')
    if not options.expected_title.strip() or not 0 < options.prompt_timeout <= 30:
        raise ValueError('Require a nonempty drawing title and a prompt timeout in (0, 30].')
    spec = json.loads(Path(options.sequence).read_text(encoding='utf-8-sig'))
    steps = spec['steps']
    if not isinstance(steps, list) or not steps:
        raise ValueError('Require a nonempty steps list.')
    initial = spec['initial_prompt']
    if not initial:
        raise ValueError('Require an explicit, observed initial prompt.')
    re.compile(initial, re.IGNORECASE)
    # Validate the entire sequence before any input. A line is one prompt answer,
    # not a multi-command script that races AutoCAD's asynchronous transitions.
    for step in steps:
        if not isinstance(step['text'], str) or any(ord(c) < 32 or ord(c) == 127 for c in step['text']):
            raise ValueError('Each step must contain exactly one line, without a newline.')
        if not step['after']:
            raise ValueError('Every step requires a nonempty expected prompt.')
        re.compile(step['after'], re.IGNORECASE)
        if 'before' in step:
            re.compile(step['before'], re.IGNORECASE)
    output = Path(options.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    target = {'pid': options.pid, 'window_id': options.window}
    palette = {'pid': options.pid, 'window_id': options.command_window,
               'include_screenshot': False, 'max_elements': 100, 'max_depth': 5}
    owns_client = client is None
    if owns_client:
        client = Client(driver_path(), output)
    records = []
    started = time.perf_counter()
    status = 'incomplete'
    failure = None
    try:
        result, _ = read_prompt(client, palette, initial, getattr(options, 'full_prompts', False))
        current, _ = prompt_of(result)
        if not re.search(initial, current, re.IGNORECASE):
            raise RuntimeError(f'Initial prompt mismatch: {current!r}; no input sent.')
        for index, step in enumerate(steps, 1):
            tick = time.perf_counter()
            # Recheck after any previous work: the user or app may have changed
            # command phase since the prior postcondition was observed.
            expected_before = step.get('before', initial if index == 1 else steps[index - 2]['after'])
            if index > 1:
                result, _ = read_prompt(client, palette, expected_before, getattr(options, 'full_prompts', False))
                current, _ = prompt_of(result)
            if not re.search(expected_before, current, re.IGNORECASE):
                raise RuntimeError(f'Unexpected prompt before step {index}: {current!r}; no input sent.')
            # A cheap root snapshot rechecks the exact live window and DWG title
            # immediately before input. No cached element index is used.
            binding, _ = client.call('get_window_state', dict(target, include_screenshot=False, max_elements=1, max_depth=1))
            _, metadata = prompt_of(binding)
            title = metadata.get('window_title', '')
            if title_key(options.expected_title) != title_key(title):
                raise RuntimeError(f'Drawing title changed: {title!r}; stopped before input.')
            _, input_ms = client.call('type_text', dict(target, delivery_mode='background', text=step['text'] + '\n'))
            deadline = time.monotonic() + options.prompt_timeout
            while True:
                result, read_ms = read_prompt(client, palette, step['after'], getattr(options, 'full_prompts', False))
                current, _ = prompt_of(result)
                if re.search(step['after'], current, re.IGNORECASE):
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError(f'Step {index} prompt mismatch: {current!r}; input was not replayed.')
                time.sleep(.1)
            record = {'step': index, 'text': step['text'], 'prompt': current,
                      'input_ms': round(input_ms, 2), 'last_read_ms': round(read_ms, 2),
                      'total_ms': round((time.perf_counter() - tick) * 1000, 2)}
            records.append(record)
            if getattr(options, 'verbose', False):
                print(json.dumps(record, ensure_ascii=True), flush=True)
        status = 'prompts_verified'
    except BaseException as error:
        failure = str(error) or type(error).__name__
        client.input_fault = failure
        raise
    finally:
        summary = {'status': status, 'steps_completed': len(records), 'steps_requested': len(steps),
                   'total_ms': round((time.perf_counter() - started) * 1000, 2), 'steps': records,
                   'geometry_verified': False,
                   'error': failure,
                   'note': 'Prompt checks are not geometry acceptance. Verify the resulting DWG separately.'}
        if owns_client:
            client.close()
        summary['wall_ms'] = round((time.perf_counter() - wall_started) * 1000, 2)
        summary['client_reused'] = not owns_client
        summary['call_evidence'] = str(client.output) if isinstance(client.output, Path) else str(output)
        (output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({'status':status, 'steps_completed':len(records), 'steps_requested':len(steps),
                          'wall_ms':summary['wall_ms'], 'geometry_verified':False,
                          'evidence':str(output / 'summary.json')}, ensure_ascii=True), flush=True)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int)
    parser.add_argument('--window', required=True, type=int)
    parser.add_argument('--command-window', required=True, type=int)
    parser.add_argument('--expected-title', required=True)
    parser.add_argument('--sequence', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--prompt-timeout', type=float, default=8)
    parser.add_argument('--full-prompts', action='store_true', help='Use the original depth-5 prompt scan for diagnosis or comparison.')
    parser.add_argument('--verbose', action='store_true', help='Print every answer; full per-answer evidence is always saved.')
    run(parser.parse_args())
