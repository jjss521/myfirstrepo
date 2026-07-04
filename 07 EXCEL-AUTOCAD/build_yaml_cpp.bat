@echo off
cd /d D:\qoderwork\07 EXCEL-AUTOCAD\yaml-cpp
if not exist build mkdir build
cd build
cmake -G "Visual Studio 16 2019" -A x64 -DCMAKE_INSTALL_PREFIX=..\third_party\yaml-cpp -DYAML_CPP_BUILD_TESTS=OFF -DYAML_CPP_BUILD_TOOLS=OFF ..
cmake --build . --config Release --target install
pause
