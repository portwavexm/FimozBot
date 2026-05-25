$b = [System.IO.File]::ReadAllBytes('start_bot.ps1')
$found = $false
for ($i = 0; $i -lt $b.Length; $i++) {
    if ($b[$i] -gt 127) {
        Write-Host "Byte[$i] = $($b[$i])"
        $found = $true
    }
}
if (-not $found) { Write-Host 'No non-ASCII bytes found.' }
