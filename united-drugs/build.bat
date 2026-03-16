@echo off
setlocal

echo Building portable (one-file) EXE...
pyinstaller --clean --noconfirm ^
  --distpath "dist\portable" ^
  --workpath "build\pyi\portable" ^
  "SalonInvoiceSystem_portable.spec"

echo Building installer (one-dir) EXE...
pyinstaller --clean --noconfirm ^
  --distpath "dist\installer" ^
  --workpath "build\pyi\installer" ^
  "SalonInvoiceSystem_installer.spec"

echo Build complete.
echo Portable EXE: dist\portable\United Agencies karachi.exe
echo Installer folder: dist\installer\United Agencies karachi\
endlocal
