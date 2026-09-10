param([int]$TargetPid,[long]$TargetHwnd,[string]$OutputPath)
$ErrorActionPreference='Stop'
Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Text;
public static class CuaInspectNative {
 public delegate bool EnumProc(IntPtr h,IntPtr p);
 [StructLayout(LayoutKind.Sequential)] public struct Rect { public int L,T,R,B; }
 [StructLayout(LayoutKind.Sequential)] public struct Gui { public uint Size,Flags; public IntPtr Active,Focus,Capture,MenuOwner,MoveSize,Caret; public Rect CaretRect; }
 [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc cb,IntPtr p);
 [DllImport("user32.dll")] public static extern bool EnumChildWindows(IntPtr h,EnumProc cb,IntPtr p);
 [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetClassName(IntPtr h,StringBuilder b,int n);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] public static extern int GetWindowText(IntPtr h,StringBuilder b,int n);
 [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h,out Rect r);
 [DllImport("user32.dll")] public static extern IntPtr GetParent(IntPtr h);
 [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
 [DllImport("user32.dll")] public static extern bool GetGUIThreadInfo(uint id,ref Gui g);
 public static object[] Inspect(uint pid,long root) {
  uint check;GetWindowThreadProcessId(new IntPtr(root),out check); if(check!=pid)throw new Exception("Target mismatch");
  var rows=new List<object>();var seen=new HashSet<long>();
  EnumProc cb=(h,p)=> {uint found;uint tid=GetWindowThreadProcessId(h,out found); if(!seen.Add(h.ToInt64()))return true;
   var c=new StringBuilder(256);var t=new StringBuilder(1024);GetClassName(h,c,256);GetWindowText(h,t,1024);Rect r;GetWindowRect(h,out r);
   var g=new Gui();g.Size=(uint)Marshal.SizeOf(g);GetGUIThreadInfo(tid,ref g);
   rows.Add(new { pid=found,hwnd=h.ToInt64(),parent=GetParent(h).ToInt64(),cls=c.ToString(),title=t.ToString(),visible=IsWindowVisible(h),left=r.L,top=r.T,width=r.R-r.L,height=r.B-r.T,thread=tid,focus=g.Focus.ToInt64()});return true;};
  EnumWindows((h,p)=>{uint found;GetWindowThreadProcessId(h,out found);if(found==pid){cb(h,p);EnumChildWindows(h,cb,p);}return true;},IntPtr.Zero);
  return rows.ToArray();
 }
}
'@
[CuaInspectNative]::Inspect($TargetPid,$TargetHwnd)|ConvertTo-Json -Depth 5|Set-Content -Encoding utf8 $OutputPath
