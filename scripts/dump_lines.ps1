# Print file with line numbers using an indexed for-loop to avoid analyzer warnings
$lines = Get-Content .\start_bot.ps1
for ($lineIndex = 0; $lineIndex -lt $lines.Count; $lineIndex++) {
	$lineNumber = $lineIndex + 1
	Write-Host ("{0,4}: {1}" -f $lineNumber, $lines[$lineIndex])
}
