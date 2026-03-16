$ErrorActionPreference = "Stop"

Write-Host "Building portable (one-file) EXE..."
pyinstaller --clean --noconfirm `
  --distpath "dist\portable" `
  --workpath "build\pyi\portable" `
  "SalonInvoiceSystem_portable.spec"

Write-Host "Building installer (one-dir) EXE..."
pyinstaller --clean --noconfirm `
  --distpath "dist\installer" `
  --workpath "build\pyi\installer" `
  "SalonInvoiceSystem_installer.spec"

Write-Host "Build complete."
Write-Host "Portable EXE: dist\portable\United Agencies karachi.exe"
Write-Host "Installer folder: dist\installer\United Agencies karachi\"
