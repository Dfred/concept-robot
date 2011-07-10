@echo off
echo.

IF "%PYTHON%" == "" (
    echo you must define PYTHON environment variable.
    GOTO :END
)
echo PYTHON is %PYTHON%

IF "%PYTHONPATH%" == "" (
    echo you must define PYTHONPATH environment variable.
    GOTO :END
)
set PYTHONPATH=%PYTHONPATH%;%cd%;%cd%\HRI\face;%cd%\common\;%cd%\extern\pyvision_0.9.0\src;
echo PYTHONPATH is %PYTHONPATH%

IF "%HOME%" == "" (
    set LIGHTHEAD=common\lightHead.conf
) ELSE (
    set LIGHTHEAD=%HOME%\lightHead.conf
)
echo LIGHTHEAD is %LIGHTHEAD%

lightHead-window.exe
rem HALA-window.exe
:END
pause
