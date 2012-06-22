@echo off
echo.

set PYTHONPATH=%PYTHONPATH%;%cd%\RAS\face;%cd%\extern\pyvision_0.9.0\src;
echo PYTHONPATH is %PYTHONPATH%

IF NOT "%HOME%" == "" (IF EXIST "%HOME%\.lightHead.conf" set LIGHTHEAD=%HOME%\.lightHead.conf)
IF "%LIGHTHEAD%" == "" set LIGHTHEAD=common\lightHead.conf
echo LIGHTHEAD is %LIGHTHEAD%

rem lightHead.exe
 lightHead.exe
rem HALA.exe
rem GIZMO.exe
:END
pause
