@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

where git >nul 2>nul
if errorlevel 1 (
  echo Git was not found in PATH.
  pause
  exit /b 1
)

git rev-parse --is-inside-work-tree >nul 2>nul
if errorlevel 1 (
  echo This folder is not a Git repository.
  pause
  exit /b 1
)

for /f "delims=" %%B in ('git branch --show-current') do set "BRANCH=%%B"
if not defined BRANCH (
  echo Could not determine the current branch.
  pause
  exit /b 1
)

set "UPSTREAM="
for /f "delims=" %%U in ('git rev-parse --abbrev-ref --symbolic-full-name @{u} 2^>nul') do set "UPSTREAM=%%U"

if not defined UPSTREAM (
  echo No upstream branch found for %BRANCH%.
  call :select_remote
  if errorlevel 1 (
    pause
    exit /b 1
  )
  echo Fetching from !REMOTE!...
  git fetch "!REMOTE!"
  if errorlevel 1 (
    echo Fetch failed.
    pause
    exit /b 1
  )
  git rev-parse --verify --quiet "refs/remotes/!REMOTE!/%BRANCH%" >nul
  if errorlevel 1 (
    echo Remote branch !REMOTE!/%BRANCH% was not found.
    pause
    exit /b 1
  )
  echo Setting upstream to !REMOTE!/%BRANCH%...
  git branch --set-upstream-to="!REMOTE!/%BRANCH%" "%BRANCH%"
  if errorlevel 1 (
    echo Failed to set upstream.
    pause
    exit /b 1
  )
  set "UPSTREAM=!REMOTE!/%BRANCH%"
)

echo Pulling from %UPSTREAM%...
git pull --rebase --autostash
if errorlevel 1 (
  echo Pull failed. Resolve any conflicts, then run pull.bat again.
  pause
  exit /b 1
)

echo Pull complete.
pause
exit /b 0

:select_remote
set "REMOTE="
set "REMOTE_COUNT=0"
for /f "delims=" %%R in ('git remote') do (
  set /a REMOTE_COUNT+=1
  set "REMOTE_!REMOTE_COUNT!=%%R"
)

if "%REMOTE_COUNT%"=="0" (
  echo No Git remote found.
  echo Add one first, for example:
  echo   git remote add origin ^<url^>
  exit /b 1
)

if "%REMOTE_COUNT%"=="1" (
  set "REMOTE=!REMOTE_1!"
  echo Using remote !REMOTE!.
  exit /b 0
)

echo Available remotes:
for /l %%I in (1,1,%REMOTE_COUNT%) do echo   %%I. !REMOTE_%%I!
set /p "REMOTE_CHOICE=Select remote [1-%REMOTE_COUNT%]: "

if not defined REMOTE_CHOICE (
  echo Remote selection is required.
  exit /b 1
)

for /f "delims=0123456789" %%C in ("%REMOTE_CHOICE%") do (
  echo Invalid remote selection.
  exit /b 1
)

if %REMOTE_CHOICE% LSS 1 (
  echo Invalid remote selection.
  exit /b 1
)

if %REMOTE_CHOICE% GTR %REMOTE_COUNT% (
  echo Invalid remote selection.
  exit /b 1
)

set "REMOTE=!REMOTE_%REMOTE_CHOICE%!"
echo Using remote !REMOTE!.
exit /b 0
