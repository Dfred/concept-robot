@echo off
echo.

set EXPT_DIR=%cd%
cd ../..

IF "%PYTHON%" == "" (
 echo you must define PYTHON environment variable.
 GOTO :END
)
echo PYTHON is %PYTHON%

rem Bloody hell I *HATE* the lack of symlinks in Windows...
set PYTHONPATH=%PYTHONPATH%;%cd%;%cd%\extern\pyvision_0.9.0\src
echo PYTHONPATH is %PYTHONPATH%

IF NOT "%HOME%" == "" (IF EXIST "%HOME%\.lightHead.conf" set LIGHTHEAD=%HOME%\.lightHead.conf)
IF "%LIGHTHEAD%" == "" set LIGHTHEAD=common\lightHead.conf
echo LIGHTHEAD is %LIGHTHEAD%

set PLAYER=player_monologue.py
rem set PLAYER=player_interactive.py

%PYTHON% %EXPT_DIR%\player_monologue.py %EXPT_DIR%\monologue.txt

:END
pause
