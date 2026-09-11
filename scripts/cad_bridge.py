"""Small native AutoCAD bridge: inspect, freeze a job, execute once, retrieve evidence."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import uuid
from desktop_lease import DesktopLease
from background_guard import BackgroundWatch
from runtime import ROOT

def digest(data):
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

def lisp_string(text):
    return '"'+text.replace('\\','\\\\').replace('"','\\"').replace('\r','\\r').replace('\n','\\n')+'"'

def validate_code(code):
    if not isinstance(code,str) or not code.strip() or len(code)>100000:
        raise ValueError('Supply 1–100000 characters of noninteractive AutoLISP.')
    depth=0;string=False;escape=False;comment=False
    for ch in code:
        if comment:
            if ch in '\r\n':comment=False
        elif string:
            if escape:escape=False
            elif ch=='\\':escape=True
            elif ch=='"':string=False
        elif ch==';':comment=True
        elif ch=='"':string=True
        elif ch=='(':depth+=1
        elif ch==')':
            depth-=1
            if depth<0:raise ValueError('Unbalanced AutoLISP parentheses.')
    if depth or string:raise ValueError('Unbalanced AutoLISP expression/string.')

def completion(folder):
    """Only a complete receipt releases an uncertain job; old receipts still work."""
    try:
        text = (folder/'completion.txt').read_text(encoding='utf-8', errors='replace')
    except (FileNotFoundError, PermissionError):
        return None
    lines = text.splitlines()
    if len(lines) < 2 or lines[0] not in ('ok', 'error') or not text.endswith('\n'):
        return None
    return lines

IDENTITY=('prog_id','pid','window','document_window','process_started','path')

class CadBridge:
    def __init__(self, root=None, task=None):
        self.root=Path(root) if root else Path(os.environ['LOCALAPPDATA'])/'AutoCAD-Cua/native'
        self.root.mkdir(parents=True,exist_ok=True)
        self.task=None
        self.bound=None
        if task:self.resume(task)

    def resume(self,task):
        if not isinstance(task,str) or not re.fullmatch('[0-9a-f]{32}',task):raise ValueError('Invalid native task token.')
        bound=json.loads((self.root/'tasks'/(task+'.json')).read_text(encoding='utf-8'))
        if self.task and self.task!=task:raise RuntimeError('Another drawing task owns this bridge. Start a new task explicitly.')
        self.task=task;self.bound=bound

    def bind(self,target):
        if self.bound:
            for key in IDENTITY:
                if self.bound[key]!=target[key]:raise RuntimeError('Task drawing changed: '+key+'. Return to the original drawing; do not adopt the active file.')
        else:
            self.task=uuid.uuid4().hex;self.bound=dict(target)
            directory=self.root/'tasks';directory.mkdir(exist_ok=True)
            (directory/(self.task+'.json')).write_text(json.dumps(self.bound),encoding='utf-8')

    def host(self, request, folder, timeout=20):
        tag=uuid.uuid4().hex
        req=folder/(tag+'-request.json');out=folder/(tag+'-response.json')
        req.write_text(json.dumps(request,ensure_ascii=False),encoding='utf-8')
        ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
        try:
            run=subprocess.run([str(ps),'-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/cad_host.ps1'),'-RequestPath',str(req),'-OutputPath',str(out)],capture_output=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError('Native call timed out; execution may continue in AutoCAD. Inspect the job result; do not replay.') from error
        if not out.exists():raise RuntimeError('Native host produced no receipt: '+run.stderr.decode(errors='replace')[:1000])
        response=json.loads(out.read_text(encoding='utf-8-sig'))
        if not response['ok']:raise RuntimeError(response['error'])
        return response['state']

    def inspect(self,pid=None,max_entities=0,handles=None,task=None,new_task=False,detailed=False):
        if type(detailed) is not bool:raise ValueError('detailed must be boolean.')
        if type(new_task) is not bool:raise ValueError('new_task must be boolean.')
        if task and new_task:raise ValueError('Choose resume or new_task, not both.')
        if new_task:self.task=None;self.bound=None
        if task:self.resume(task)
        if type(max_entities) is not int or not 0<=max_entities<=10000:raise ValueError('max_entities must be 0–10000; 0 reads identity only.')
        if pid is not None and (type(pid) is not int or pid<=0):raise ValueError('Invalid PID.')
        if handles is not None and (not isinstance(handles,list) or len(handles)>10000 or any(not isinstance(h,str) or not re.fullmatch('[0-9A-Fa-f]+',h) for h in handles)):raise ValueError('Handles must be hexadecimal strings.')
        folder=self.root/('inspect-'+uuid.uuid4().hex);folder.mkdir()
        state=self.host(dict(operation='inspect',pid=pid,target=self.bound,refresh_file_hash=True,max_entities=max_entities or (len(handles) if handles else 0),handles=handles,detailed=detailed),folder)
        self.bind(state['target'])
        state['task']=self.task
        return state

    def prepare(self,target,code,precondition,description,undo_group=True,task=None,helpers=False,replace_model=False,backup_path=None,setup_code='T'):
        if type(undo_group) is not bool:raise ValueError('undo_group must be boolean.')
        validate_code(code);validate_code(precondition);validate_code(setup_code)
        required={'prog_id','pid','window','document_window','process_started','path','file_sha256'}
        if not isinstance(target,dict) or set(target)!=required:raise ValueError('Use the complete target returned by cad_inspect.')
        if not re.fullmatch(r'AutoCAD\.Application\.\d+(\.\d+)?',target['prog_id']) or any(type(target[k]) is not int or target[k]<=0 for k in ('pid','window','document_window')):raise ValueError('Invalid AutoCAD target.')
        if not isinstance(description,str) or not description.strip():raise ValueError('Describe the intended drawing changes.')
        if task:self.resume(task)
        self.bind(target)
        if type(helpers) is not bool or type(replace_model) is not bool:raise ValueError('helpers and replace_model must be boolean.')
        if replace_model and (not helpers or not isinstance(backup_path,str) or not Path(backup_path).is_absolute()):raise ValueError('Model replacement requires helpers and an absolute new backup_path.')
        if backup_path and not replace_model:raise ValueError('backup_path is only used for replace_model.')
        if backup_path and (Path(backup_path).exists() or os.path.normcase(os.path.abspath(backup_path))==os.path.normcase(os.path.abspath(target['path']))):raise ValueError('Backup must be a new file, separate from the drawing.')
        job=uuid.uuid4().hex;folder=self.root/job;folder.mkdir()
        plan=dict(target=target,code=code,precondition=precondition,description=description,undo_group=undo_group,task=self.task,replace_model=replace_model,backup_path=backup_path,setup_code=setup_code)
        if helpers:plan['helper_source']=(ROOT/'scripts/native_helpers.lsp').read_text(encoding='utf-8')
        (folder/'plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
        return dict(job=job,sha256=digest(plan),plan=plan,evidence=str(folder),note='Prepared only; generated Lisp is trusted code, not sandboxed. Check task scope before execution.')

    def folder(self,job):
        if not isinstance(job,str) or not re.fullmatch('[0-9a-f]{32}',job):raise ValueError('Invalid job ID.')
        folder=self.root/job
        if not (folder/'plan.json').is_file():raise ValueError('Unknown job ID.')
        return folder

    def result(self,job,resolve_after_inspection=False):
        if type(resolve_after_inspection) is not bool:raise ValueError('Resolution flag must be boolean.')
        folder=self.folder(job);state=folder/'execution.json';lines=completion(folder)
        answer=json.loads(state.read_text()) if state.exists() else {'status':'prepared'}
        if resolve_after_inspection and state.exists() and lines is None:
            plan=json.loads((folder/'plan.json').read_text(encoding='utf-8'))
            lease=DesktopLease()
            try:
                fresh=self.host(dict(operation='inspect',pid=plan['target']['pid'],max_entities=0),folder)
                for key in ('pid','window','document_window','process_started','path'):
                    if fresh['target'][key]!=plan['target'][key]:raise RuntimeError('Recovery target changed; inspect the original drawing.')
                if fresh['cmdactive'] or fresh['cmdnames']:raise RuntimeError('Cannot resolve a job while AutoCAD is busy.')
                answer['resolved_after_inspection']=True
                answer['resolution_state']=fresh
                state.write_text(json.dumps(answer,indent=2))
            finally:lease.close()
        lines=completion(folder)
        if lines is not None:
            answer['status']='executed' if lines and lines[0]=='ok' else 'failed'
            answer['native_result']='\n'.join(lines[1:])[:12000]
            try:answer['data']=json.loads('\n'.join(lines[1:]))
            except (ValueError,TypeError):pass
        answer.update(job=job,evidence=str(folder),geometry_verified=False)
        return answer

    def commands(self,plan,marker,job):
        source=self.command(plan,marker);symbol='cbj'+job
        commands=[f'(progn (setq {symbol} "") (princ))\n']
        for i in range(0,len(source),192):
            commands.append(f'(progn (setq {symbol} (strcat {symbol} {lisp_string(source[i:i+192])})) (princ))\n')
        commands.append(f'(eval (read {symbol}))\n')
        commands.append(f'(progn (setq {symbol} nil) (princ))\n')
        return commands

    def command(self,plan,marker):
        t=plan['target']
        binding=f'(and (= (strcase (strcat (getvar "DWGPREFIX") (getvar "DWGNAME"))) (strcase {lisp_string(t["path"])})) (= (vla-get-HWND (vla-get-ActiveDocument (vlax-get-acad-object))) {t["document_window"]}))'
        # Evaluate the source as one Lisp form: no multiline command/prompt guessing.
        setup=plan.get('helper_source','')
        if setup:setup+='\n(acua:init)\n'
        setup+='\n'+plan.get('setup_code','T')+'\n'
        erase='(acua:clear-model)\n' if plan.get('replace_model') else ''
        body='(progn\n'+erase+plan['code']+'\n)'
        pre='(progn\n'+plan['precondition']+'\n)'
        start_undo='(vla-StartUndoMark cb-doc) (setq cb-started T)' if plan['undo_group'] else ''
        return f'''(progn (vl-load-com) ((lambda (/ cb-doc cb-value cb-file cb-started cb-phase)
 (setq cb-value (vl-catch-all-apply '(lambda ()
  (setq cb-phase "drawing binding") (if (not {binding}) (exit))
  (setq cb-phase "precondition") (if (not {pre}) (exit))
  (setq cb-phase "execution")
  (setq cb-doc (vla-get-ActiveDocument (vlax-get-acad-object)))
  (setq cb-phase "prerequisites") {setup}
  {start_undo}
  (setq cb-phase "execution")
  {body}) nil))
 (if cb-started (vl-catch-all-apply 'vla-EndUndoMark (list cb-doc)))
 (setq cb-file (open {lisp_string(str(marker)+".tmp")} "w"))
 (if cb-file (progn (write-line (if (vl-catch-all-error-p cb-value) "error" "ok") cb-file)
  (write-line (if (vl-catch-all-error-p cb-value) (strcat cb-phase ": " (vl-catch-all-error-message cb-value)) (vl-princ-to-string cb-value)) cb-file) (close cb-file)
  (vl-file-rename {lisp_string(str(marker)+".tmp")} {lisp_string(str(marker))})))
 )) (princ))\n'''

    def execute(self,job,sha256,allow_interruption=False):
        if type(allow_interruption) is not bool:raise ValueError('allow_interruption must be boolean.')
        folder=self.folder(job);plan=json.loads((folder/'plan.json').read_text(encoding='utf-8'))
        if sha256!=digest(plan):raise ValueError('Prepared job hash mismatch; nothing dispatched.')
        if plan.get('task'):self.resume(plan['task'])
        self.bind(plan['target'])
        lease=DesktopLease();watch=None;state=folder/'execution.json'
        try:
            if state.exists():return self.result(job)
            for other in self.root.glob('*/execution.json'):
                if other.parent!=folder and completion(other.parent) is None and not json.loads(other.read_text()).get('resolved_after_inspection'):
                    raise RuntimeError('A previous native job has no completion receipt: '+other.parent.name+'. Inspect its outcome before another job; no replay.')
            fresh=self.host(dict(operation='inspect',target=plan['target'],pid=plan['target']['pid'],max_entities=0),folder)
            if fresh['cmdactive'] or fresh['cmdnames']:raise RuntimeError('AutoCAD has an active command; inspect it before execution.')
            watch=BackgroundWatch().start()
            if not allow_interruption:watch.check_target(plan['target']['pid'],plan['target']['window'])
            receipt=dict(status='uncertain',sha256=sha256,allow_interruption=allow_interruption,started=time.time(),note='Job will never be automatically dispatched twice. Failure may leave partial drawing changes; inspect before Undo/recovery.')
            with state.open('x') as file:json.dump(receipt,file)
            dispatched=False
            try:
                dispatch_target=plan['target']
                if plan.get('replace_model'):
                    backup=self.host(dict(operation='backup',target=dispatch_target,pid=dispatch_target['pid'],backup_path=plan['backup_path']),folder)
                    receipt['backup']=backup['backup'];dispatch_target=backup['target']
                commands=self.commands(plan,folder/'completion.txt',job)
                receipt['command_chunks']=len(commands)
                dispatched=True
                self.host(dict(operation='execute',target=dispatch_target,pid=dispatch_target['pid'],commands=commands),folder)
                deadline=time.monotonic()+5
                while completion(folder) is None and time.monotonic()<deadline:time.sleep(.05)
            except Exception as error:
                receipt['error']=str(error)
                if not dispatched:
                    pending=folder/'completion.txt.tmp';pending.write_text('error\nBefore code dispatch: '+str(error)+'\n',encoding='utf-8');pending.rename(folder/'completion.txt')
            receipt['code_dispatch_attempted']=dispatched
            receipt['elapsed_seconds']=time.time()-receipt['started']
            receipt['focus_change']=watch.finish();watch=None
            state.write_text(json.dumps(receipt,indent=2))
            return self.result(job)
        finally:
            if watch:watch.finish()
            lease.close()
