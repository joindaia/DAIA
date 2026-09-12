# Read-only prerequisite check; this does not create or validate a worker VM.
$ErrorActionPreference = 'Stop'
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class DaiaWhpProbe {
    [DllImport("WinHvPlatform.dll", ExactSpelling=true)]
    public static extern int WHvGetCapability(uint code, out ulong value,
                                             uint size, out uint written);
}
'@
[UInt64]$value = 0
[UInt32]$written = 0
$hr = [DaiaWhpProbe]::WHvGetCapability(0, [ref]$value, 8, [ref]$written)
[pscustomobject]@{
    HResult = $hr
    HypervisorPresent = ($value -ne 0)
    WrittenBytes = $written
} | ConvertTo-Json -Compress
if ($hr -ne 0 -or $written -ne 4 -or $value -eq 0) { exit 1 }
