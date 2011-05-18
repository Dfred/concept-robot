@echo off
echo.

cd ../..

IF "%PYTHON%" == "" (
 echo you must define PYTHON environment variable.
 GOTO :END
)
echo PYTHON is %PYTHON%

rem Bloody hell I *HATE* the lack of symlinks in Windows...
set PYTHONPATH=%PYTHONPATH%;%cd%;%cd%\HRI\face;%cd%\common\;%cd%\ext\pyvision_0.9.0\src
echo PYTHONPATH is %PYTHONPATH%

%PYTHON% experiments/blink-influence/expression-player.py

:END
pause
