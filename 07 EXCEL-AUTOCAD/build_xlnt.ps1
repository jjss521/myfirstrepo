# Build xlnt with VS2019
# This script must be run from VS2019 Developer Command Prompt

$ErrorActionPreference = "Stop"

# Set up VS2019 environment
$vcvars = "D:\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvars64.bat"
$cmake = "D:\Microsoft Visual Studio\2019\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"

# Build xlnt
Write-Host "==============================" -ForegroundColor Cyan
Write-Host "Building xlnt..." -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

$xlntDir = "D:\qoderwork\07 EXCEL-AUTOCAD\xlnt"
$buildDir = "$xlntDir\build"
$installDir = "D:\qoderwork\07 EXCEL-AUTOCAD\third_party\xlnt"

if (!(Test-Path $buildDir)) { New-Item -ItemType Directory -Path $buildDir | Out-Null }
Set-Location $buildDir

# Configure
& $cmake `
  -G "Visual Studio 16 2019" `
  -A x64 `
  -DCMAKE_INSTALL_PREFIX="$installDir" `
  -DXLNT_BUILD_TESTS=OFF `
  -DXLNT_BUILD_BENCHMARKS=OFF `
  "$xlntDir"

if ($LASTEXITCODE -ne 0) { throw "CMake configure failed" }

# Build and install
& $cmake --build . --config Release --target install

if ($LASTEXITCODE -ne 0) { throw "Build failed" }

Write-Host "xlnt built successfully!" -ForegroundColor Green
Write-Host "Installed to: $installDir" -ForegroundColor Yellow
