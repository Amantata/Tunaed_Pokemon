@echo off
REM ─────────────────────────────────────────────────────────────────────────────
REM  build_windows.bat — Windows .exe 빌드 스크립트 (F-03)
REM
REM  사전 준비:
REM    Python 3.11+ 설치 (https://python.org)
REM    이 파일과 같은 디렉터리에서 실행
REM
REM  실행:
REM    build_windows.bat
REM
REM  결과물: dist\TunaedPokemon.exe
REM ─────────────────────────────────────────────────────────────────────────────

setlocal

echo [1/3] 빌드 의존성 설치 중...
pip install -e ".[build]" --quiet
if errorlevel 1 (
    echo 오류: pip install 실패
    exit /b 1
)

echo [2/3] PyInstaller 빌드 실행 중...
pyinstaller tunaed_pokemon.spec --noconfirm
if errorlevel 1 (
    echo 오류: PyInstaller 빌드 실패
    exit /b 1
)

echo [3/3] 완료!
echo 실행 파일 위치: dist\TunaedPokemon.exe

endlocal
