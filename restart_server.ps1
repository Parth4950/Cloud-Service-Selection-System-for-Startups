# Stop any process using port 5001, then start the Flask app
$conn = Get-NetTCPConnection -LocalPort 5001 -ErrorAction SilentlyContinue
if ($conn) {
    $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}
Write-Host "Starting server on http://127.0.0.1:5001 ..."
Set-Location $PSScriptRoot
python run.py
