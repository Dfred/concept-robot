@echo off
echo.

IF "%PYTHON%" == "" (
 echo you must define PYTHON environment variable.
 GOTO :END
)
cd ../..
echo PYTHONPATH is %PYTHONPATH%

set PYTHONPATH=%PYTHONPATH%\site-packages;%cd%\HRI;%cd%\HRI\face;%cd%\common\;

%PYTHON% experiments/blink-influence/expression-player.py

:END
pause
