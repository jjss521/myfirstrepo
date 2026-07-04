@echo off
call "D:\Microsoft Visual Studio\2019\Professional\VC\Auxiliary\Build\vcvars64.bat"
set CMAKE_EXE=D:\Microsoft Visual Studio\2019\Professional\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe

echo ========== Building yaml-cpp ==========
cd /d D:\qoderwork\07 EXCEL-AUTOCAD\yaml-cpp
if not exist build mkdir build
cd build
"%CMAKE_EXE%" -G "Visual Studio 16 2019" -A x64 -DCMAKE_INSTALL_PREFIX=..\..\third_party\yaml-cpp -DYAML_CPP_BUILD_TESTS=OFF -DYAML_CPP_BUILD_TOOLS=OFF .
"%CMAKE_EXE%" --build . --config Release --target install
if errorlevel 1 echo yaml-cpp build FAILED && exit /b 1
echo yaml-cpp installed to D:\qoderwork\07 EXCEL-AUTOCAD\third_party\yaml-cpp

echo ========== Building xlnt ==========
cd /d D:\qoderwork\07 EXCEL-AUTOCAD\xlnt
if not exist build mkdir build
cd build
"%CMAKE_EXE%" -G "Visual Studio 16 2019" -A x64 -DCMAKE_INSTALL_PREFIX=..\..\third_party\xlnt -DXLNT_BUILD_TESTS=OFF -DXLNT_BUILD_BENCHMARKS=OFF .
"%CMAKE_EXE%" --build . --config Release --target install
if errorlevel 1 echo xlnt build FAILED && exit /b 1
echo xlnt installed to D:\qoderwork\07 EXCEL-AUTOCAD\third_party\xlnt

echo ========== All done ==========
