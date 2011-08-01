@echo off
echo.

cd ../..

IF "%PYTHON%" == "" (
 echo you must define PYTHON environment variable.
 GOTO :END
)
echo PYTHON is %PYTHON%

rem Bloody hell I *HATE* the lack of symlinks in Windows...
set PYTHONPATH=%PYTHONPATH%;%cd%;%cd%\RAS\face;%cd%\common\;%cd%\extern\pyvision_0.9.0\src
echo PYTHONPATH is %PYTHONPATH%

set PLAYER=player_monologue.py
rem set PLAYER=player_interactive.py

set EXP_DIR=%cd%\experiments\blink-influence\
set FILE=%EXP_DIR%\monologue.txt
rem set FILE=C:\Users\fred\Desktop\FDHD\overlay_concept-robot\player_scripts\GUI.txt

%PYTHON% %EXP_DIR%\player_monologue.py %FILE%

:END
pause
