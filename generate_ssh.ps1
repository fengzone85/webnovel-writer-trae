$sshDir = "$env:USERPROFILE\.ssh"
if (!(Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Output "Created .ssh directory"
}

$keyPath = "$sshDir\id_ed25519_github"

$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = "ssh-keygen.exe"
$processInfo.Arguments = "-t ed25519 -C `"fengzone85@github.com`" -f `"$keyPath`" -N `"`""
$processInfo.RedirectStandardInput = $true
$processInfo.RedirectStandardOutput = $true
$processInfo.RedirectStandardError = $true
$processInfo.UseShellExecute = $false
$processInfo.CreateNoWindow = $true

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $processInfo
$process.Start() | Out-Null

$process.WaitForExit()
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$exitCode = $process.ExitCode

Write-Output "Exit Code: $exitCode"
Write-Output $stdout
if ($stderr) { Write-Output "Error: $stderr" }

if ($exitCode -eq 0) {
    Write-Output "`n=== Public Key ===" ; Get-Content "$keyPath.pub"
}