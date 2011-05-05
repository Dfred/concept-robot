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
echo PYTHONPATH is %PYTHONPATH%

set BASE_DIR=%cd%
set PYTHONPATH=%PYTHONPATH%\site-packages;%BASE_DIR%\HRI;%BASE_DIR%\HRI\face;%BASE_DIR%\common\;

IF "%HOME%" == "" (
    set LIGHTHEAD=common\lightHead.conf
) ELSE (
    set LIGHTHEAD=%HOME%\lightHead.conf
)
echo LIGHTHEAD is %LIGHTHEAD%

rem lightHead-window.exe
 HALA-window.exe
:END
pause
