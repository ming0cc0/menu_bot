# 밥봇 JB 단일 exe 빌드 (PyInstaller)
# 사용법: .venv 활성화 없이 그냥  powershell -File scripts\build.ps1
$root = Split-Path $PSScriptRoot -Parent
$py = Join-Path $root ".venv\Scripts\python.exe"

& $py -m PyInstaller `
    --onefile --noconsole --clean --noconfirm `
    --name "BapBotJB" `
    --icon (Join-Path $root "assets\jb.ico") `
    --add-data "$(Join-Path $root 'assets');assets" `
    --paths (Join-Path $root "src") `
    --hidden-import "pystray._win32" `
    --collect-data "customtkinter" `
    --distpath (Join-Path $root "dist") `
    --workpath (Join-Path $root "build") `
    --specpath (Join-Path $root "build") `
    (Join-Path $root "scripts\launcher.py")

if ($LASTEXITCODE -eq 0) {
    Write-Host "빌드 완료: $root\dist\BapBotJB.exe"
    Write-Host "배포: exe + data\ 폴더를 함께 복사하세요 (data가 없으면 첫 실행 시 샘플 생성)."
}
