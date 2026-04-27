<#
Helper script to quickly set the API key for local development
Run this from PowerShell: .\set_env.ps1
Create .env in the backend folder with GOOGLE_API_KEY.

This writes plaintext .env for local development. Do not commit this file to git.
#>

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$envPath = Join-Path $scriptDir ".env"

if (Test-Path $envPath) {
    Write-Host "Found existing .env file at $envPath" -ForegroundColor Cyan
}

Write-Host "This will create or update '$scriptDir\.env' with your Google Gemini API key." -ForegroundColor Yellow

$key = Read-Host -Prompt "Enter your Google Gemini API key" 
$key = $key.Trim()
if ([string]::IsNullOrWhiteSpace($key)) {
    Write-Host "No key entered. Aborting." -ForegroundColor Red
    exit 1
}

if (Test-Path $envPath) {
    $choice = Read-Host "'.env' already exists. Overwrite? (y/N)"
    if ($choice.ToLower() -ne 'y') {
        Write-Host "Aborted; existing .env left unchanged." -ForegroundColor Cyan
        exit 0
    }
}

# Write the key to .env
Set-Content -Path $envPath -Value ("GOOGLE_API_KEY=" + $key) -Encoding UTF8
Write-Host "Wrote GOOGLE_API_KEY to $envPath" -ForegroundColor Green
Write-Host "Reminder: do not commit .env to git. Use this file for local development only." -ForegroundColor Yellow
