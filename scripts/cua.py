"""Small Cua adapter: exact background calls, full local evidence, compact output."""
import argparse
import base64
import json
import re
from pathlib import Path
import subprocess
from runtime import driver_path
from run_sequence import Client, prompt_of
from background_guard import READS, INPUTS

def invocation_match(state, selector):
    data=state.get('structuredContent',{})
    ids={int(m.group(1)):m.group(2) for m in re.finditer(r'\[(\d+)\].*?\[id=([^\s\]]+)', data.get('tree_markdown',''))}
    matches=[e for e in data.get('elements',[]) if e.get('label')==selector['label']
        and e.get('role')==selector['role'] and e.get('enabled') and 'invoke' in e.get('actions',[])
        and ids.get(e.get('element_index'))==selector['automation_id']]
    if len(matches)!=1:
        raise RuntimeError('Need exactly one enabled Invoke match in the fresh bounded snapshot; no click sent.')
    return matches[0]['element_token']

def check_call(name, args):
    if name in READS:
        return
    if name not in INPUTS:
        raise ValueError('Adapter supports observations and exact background input only. Inspect describe; use a separately authorized Cua route for other operations.')
    if args.get('delivery_mode') != 'background':
        raise ValueError('Explicit background delivery is required.')
    if type(args.get('pid')) is not int or args['pid'] <= 0 or type(args.get('window_id')) is not int or args['window_id'] <= 0:
        raise ValueError('Input requires a positive exact PID and HWND.')
    if any(k in args for k in ('desktop_id', 'display_id', 'screen_id')):
        raise ValueError('Desktop-wide input is unsupported by this adapter.')
    if args.get('scope', 'window') != 'window' or args.get('target') is not None:
        raise ValueError('Use the exact top-level PID/HWND fields, without target overrides.')
    if any(k in args for k in ('element_index', 'element_token', 'snapshot_id')):
        raise ValueError('Snapshot-bound element references cannot cross adapter sessions. Use a persistent Cua MCP connection for indexed accessibility input.')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['describe', 'call', 'invoke'])
    parser.add_argument('tool')
    parser.add_argument('--arguments')
    parser.add_argument('--output')
    options = parser.parse_args()
    if options.mode == 'describe':
        subprocess.run([driver_path(), 'describe', options.tool], check=True)
        return
    if not options.output:
        parser.error('--output NEW_DIRECTORY is required for calls')
    args = json.loads(Path(options.arguments).read_text(encoding='utf-8-sig')) if options.arguments else {}
    if options.mode == 'invoke':
        if options.tool != 'click' or not all(args.get(k) for k in ('label','role','automation_id')):
            parser.error('invoke click requires an observed exact label, role and automation_id')
        check_call('click', {k:v for k,v in args.items() if k not in ('label','role','automation_id')})
    else:
        check_call(options.tool, args)
    output = Path(options.output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    client = Client(driver_path(), output)
    try:
        if options.mode == 'invoke':
            state, _ = client.call('get_window_state', dict(pid=args['pid'], window_id=args['window_id'],
                include_screenshot=False, max_elements=120, max_depth=8))
            token=invocation_match(state,args)
            args = dict(pid=args['pid'], window_id=args['window_id'], delivery_mode='background',
                        element_token=token)
        result, elapsed = client.call(options.tool, args)
        images = []
        for index, block in enumerate(result.get('content', [])):
            if block.get('type') == 'image':
                suffix = '.png' if block.get('mimeType') == 'image/png' else '.jpg'
                path = output / f'capture-{index}{suffix}'
                path.write_bytes(base64.b64decode(block['data'], validate=True))
                images.append(str(path))
        prompt, data = prompt_of(result)
        text = '\n'.join(b.get('text', '') for b in result.get('content', []) if b.get('type') == 'text')
        print(json.dumps({'elapsed_ms':round(elapsed,2), 'evidence':str(output), 'images':images,
            'prompt':prompt, 'window_title':data.get('window_title'), 'text':text[:16000],
            'output_truncated':len(text)>16000}, ensure_ascii=True))
    finally:
        client.close()

if __name__ == '__main__':
    main()
