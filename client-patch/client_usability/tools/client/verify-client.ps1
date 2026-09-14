[CmdletBinding()]
param([string]$ClientRoot, [string]$Manifest, [string]$ReportPath)

$ErrorActionPreference = 'Stop'
$checked = 0
$failures = [System.Collections.Generic.List[string]]::new()
$passed = $false
try {
    if (-not $ClientRoot) { $ClientRoot = Join-Path $PSScriptRoot '../..' }
    $root = (Resolve-Path -LiteralPath $ClientRoot).Path.TrimEnd('\', '/')
    if (-not $Manifest) {
        $Manifest = Join-Path $root 'client-manifest.json'
        # Full releases keep the manifest beside PN-Client; cumulative updates
        # put it inside. Prefer the installed manifest when both are present.
        if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) {
            $Manifest = Join-Path (Split-Path -Parent $root) 'client-manifest.json'
        }
    }
    if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) {
        throw 'Place the client-manifest.json supplied with your current release in the game folder, then run Verify Client again.'
    }
    $raw = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8
    if (-not $raw.TrimStart().StartsWith('[')) { throw 'The release manifest must be a nonempty JSON array.' }
    $rows = ConvertFrom-Json -InputObject $raw
    if ($rows.Count -eq 0) { throw 'The release manifest is empty.' }
    $names = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::OrdinalIgnoreCase)
    $validated = [System.Collections.Generic.List[object]]::new()
    foreach ($row in $rows) {
        $name = [string]$row.path
        if (-not $name -or $name -match '(^[/\\]|:|(^|[/\\])\.\.?([/\\]|$)|[\x00-\x1f])') {
            throw "Invalid manifest path: $name"
        }
        $name = $name.Replace('/', '\')
        if (-not $names.Add($name)) { throw "Duplicate manifest path: $name" }
        if ([string]$row.sha256 -notmatch '^[0-9a-fA-F]{64}$' -or [string]$row.bytes -notmatch '^\d+$') {
            throw "Invalid size or SHA-256 for: $name"
        }
        $path = [System.IO.Path]::GetFullPath((Join-Path $root $name))
        if (-not $path.StartsWith($root+'\', [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Path leaves the game folder: $name"
        }
        # Never follow a junction/symlink to hash files outside the installation.
        $cursor = $path
        while ($cursor.Length -gt $root.Length) {
            if (Test-Path -LiteralPath $cursor) {
                $entry = Get-Item -LiteralPath $cursor -Force
                if ($entry.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
                    throw "Linked manifest path is not supported: $name"
                }
            }
            $cursor = Split-Path -Parent $cursor
        }
        $validated.Add([pscustomobject]@{name=$name; path=$path; bytes=[long]$row.bytes; sha256=[string]$row.sha256})
    }
    Write-Host 'Verifying release files. Large GRF archives can take a few minutes.'
    foreach ($row in $validated) {
        if (-not (Test-Path -LiteralPath $row.path -PathType Leaf)) { $failures.Add("Missing: $($row.name)"); continue }
        if ((Get-Item -LiteralPath $row.path).Length -ne $row.bytes) { $failures.Add("Size differs: $($row.name)"); continue }
        # Use the runtime directly; module auto-loading can leave Get-FileHash
        # unavailable in child Windows PowerShell sessions.
        $sha = [System.Security.Cryptography.SHA256]::Create()
        try {
            $stream = [System.IO.File]::OpenRead($row.path)
            try { $actual = [System.BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-', '') }
            finally { $stream.Dispose() }
        } finally { $sha.Dispose() }
        if ($actual -ne $row.sha256) { $failures.Add("Checksum differs: $($row.name)"); continue }
        $checked++
    }
    if ($failures.Count) {
        foreach ($failure in $failures) { Write-Host $failure }
        Write-Host 'Restore mismatched files from the matching release. An intentional settings change can also cause a mismatch.'
        exit 1
    }
    Write-Host "PASS: $checked release files match their sizes and SHA-256 checksums."
    Write-Host 'Extra screenshots and saves are allowed. This verifies the supplied manifest, not gameplay or publisher authenticity.'
    $passed = $true
    exit 0
} catch {
    $failures.Add($_.Exception.Message)
    Write-Host ('Verification failed: '+$_.Exception.Message)
    exit 1
} finally {
    if ($ReportPath) {
        [pscustomobject]@{
            passed=$passed; checked=$checked; client=$root; manifest=$Manifest
            failures=@($failures.ToArray()); checked_at_utc=[DateTime]::UtcNow.ToString('o')
            scope='Supplied manifest sizes and hashes only; not gameplay or publisher authenticity.'
        } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $ReportPath -Encoding UTF8
    }
}
