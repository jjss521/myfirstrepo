# Build yaml-cpp with VS2019
# This script must be run from a PowerShell session that has VS2019 environment

$ErrorActionPreference = "Stop"

# Set up VS2019 environment by running vcvars64.bat and capturing the environment
$vcvars = "D:\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvars64.bat"
$cmake = "D:\Microsoft Visual Studio\2019\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe"

# Run vcvars64.bat and then run our commands
$envScript = @"
call "$vcvars"
cd /d D:\qoderwork\07 EXCEL-AUTOCAD\yaml-cpp
if not exist build mkdir build
cd build
"$cmake" -G "Visual Studio 16 2019" -A x64 -DCMAKE_INSTALL_PREFIX=..\third_party\yaml-cpp -DYAML_CPP_BUILD_TESTS=OFF -DYAML_CPP_BUILD_TOOLS=OFF ..
"$cmake" --build . --config Release --target install
"@

# Write the environment script to a temp file
$envScriptPath = [System.IO.Path]::GetTempFileName() + ".bat"
$envScript | Out-File -FilePath $envScriptPath -Encoding ASCII

# Run the batch file
Write-Host "========== Building yaml-cpp ==========" -ForegroundColor Cyan
cmd.exe /c $envScriptPath

if ($LASTEXITCODE -ne 0) {
    Write-Error "yaml-cpp build failed"
    exit 1
}

Write-Host "yaml-cpp built successfully!" -ForegroundColor Green
Write-Host "Installed to: D:\qoderwork\07 EXCEL-AUTOCAD\third_party\yaml-cpp" -ForegroundColor Yellow

# Clean up
Remove-Item $envScriptPath -Force -ErrorAction SilentlyContinue
