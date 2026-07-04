@echo off
cd /d D:\qoderwork\07 EXCEL-AUTOCAD\xlnt
if not exist build mkdir build
cd build
cmake -G "Visual Studio 16 2019" -A x64 -DCMAKE_INSTALL_PREFIX=..\third_party\xlnt -DXLNT_BUILD_TESTS=OFF -DXLNT_BUILD_BENCHMARKS=OFF ..
cmake --build . --config Release --target install
pause
