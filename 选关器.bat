@echo off
chcp 936 >nul
title Hazard Ball - 关卡选择
cd /d "%~dp0"
setlocal

if not exist "DATA\SAVE\BARRY.sav" goto noadv
if not exist "DATA\SAVE\2UP GAME.sav" goto nocoop

:menu
cls
echo ============================================================
echo                Hazard Ball  -  关卡选择
echo ============================================================
echo.
echo    [A] 冒险模式    level1 ~ level20
echo.
echo    [C] 双人模式    coop1  ~ coop10
echo.
echo    [Q] 退出
echo.
choice /c ACQ /n /m "请选择 A / C / Q: "
if errorlevel 3 goto bye
if errorlevel 2 goto coop
if errorlevel 1 goto adv
goto menu

:adv
cls
echo ============================================================
echo           冒险模式 ADVENTURE  -  关卡 1-20
echo ============================================================
echo.
echo     [1] MEMORIES              [11] AVALANCHE
echo     [2] BACKLASH              [12] PERILOUS SKI SLOPE
echo     [3] DESERT TOWER          [13] BOMB CHASE
echo     [4] HEAT WAVE             [14] METALLIC FORTRESS
echo     [5] SWAMP OUTPOST         [15] ACID LEAK
echo     [6] ELEMENTAL RACE        [16] CLOSED DOORS
echo     [7] FLOODED CITADEL       [17] LAVA NIGHT
echo     [8] ABANDONED STONGHOLD   [18] MARBLE ISLANDS
echo     [9] ICE BERG DILEMMA      [19] OBLIVIOUS SPEEDWAY
echo     [0] SNOW BALL CAPER (10)
echo.
echo     [M] 更多关卡 11-20        [R] 重置进度到第 1 关
echo     [D] 返回主菜单
echo.
choice /c 1234567890MRD /n /m "请选择: "
if errorlevel 12 goto adv
if errorlevel 11 goto clear
if errorlevel 10 goto advmap
if errorlevel 9 copy /y "DATA\SAVE\saves_adv\adv19.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok19
if errorlevel 8 copy /y "DATA\SAVE\saves_adv\adv18.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok18
if errorlevel 7 copy /y "DATA\SAVE\saves_adv\adv17.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok17
if errorlevel 6 copy /y "DATA\SAVE\saves_adv\adv16.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok16
if errorlevel 5 copy /y "DATA\SAVE\saves_adv\adv15.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok15
if errorlevel 4 copy /y "DATA\SAVE\saves_adv\adv14.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok14
if errorlevel 3 copy /y "DATA\SAVE\saves_adv\adv13.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok13
if errorlevel 2 copy /y "DATA\SAVE\saves_adv\adv12.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok12
if errorlevel 1 copy /y "DATA\SAVE\saves_adv\adv11.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok11
copy /y "DATA\SAVE\saves_adv\adv10.sav" "DATA\SAVE\BARRY.sav" >nul
goto ok10

:advmap
cls
echo ============================================================
echo           冒险模式 ADVENTURE  -  关卡 11-20
echo ============================================================
echo.
echo     [1] AVALANCHE              [9] OBLIVIOUS SPEEDWAY
echo     [2] PERILOUS SKI SLOPE     [0] WARPED TEMPLE OF DOOM
echo     [3] BOMB CHASE             [D] 返回上一层
echo     [4] METALLIC FORTRESS
echo     [5] ACID LEAK
echo     [6] CLOSED DOORS
echo     [7] LAVA NIGHT
echo     [8] MARBLE ISLANDS
echo.
choice /c 1234567890D /n /m "请选择: "
if errorlevel 11 goto adv
if errorlevel 10 copy /y "DATA\SAVE\saves_adv\adv20.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok20
if errorlevel 9 copy /y "DATA\SAVE\saves_adv\adv19.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok19
if errorlevel 8 copy /y "DATA\SAVE\saves_adv\adv18.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok18
if errorlevel 7 copy /y "DATA\SAVE\saves_adv\adv17.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok17
if errorlevel 6 copy /y "DATA\SAVE\saves_adv\adv16.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok16
if errorlevel 5 copy /y "DATA\SAVE\saves_adv\adv15.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok15
if errorlevel 4 copy /y "DATA\SAVE\saves_adv\adv14.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok14
if errorlevel 3 copy /y "DATA\SAVE\saves_adv\adv13.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok13
if errorlevel 2 copy /y "DATA\SAVE\saves_adv\adv12.sav" "DATA\SAVE\BARRY.sav" >nul & goto ok12
copy /y "DATA\SAVE\saves_adv\adv11.sav" "DATA\SAVE\BARRY.sav" >nul
goto ok11

:ok1
echo   冒险模式 -^> level 1   MEMORIES & goto fin
:ok2
echo   冒险模式 -^> level 2   BACKLASH & goto fin
:ok3
echo   冒险模式 -^> level 3   DESERT TOWER & goto fin
:ok4
echo   冒险模式 -^> level 4   HEAT WAVE & goto fin
:ok5
echo   冒险模式 -^> level 5   SWAMP OUTPOST & goto fin
:ok6
echo   冒险模式 -^> level 6   ELEMENTAL RACE & goto fin
:ok7
echo   冒险模式 -^> level 7   FLOODED CITADEL & goto fin
:ok8
echo   冒险模式 -^> level 8   ABANDONED STONGHOLD & goto fin
:ok9
echo   冒险模式 -^> level 9   ICE BERG DILEMMA & goto fin
:ok10
echo   冒险模式 -^> level 10  SNOW BALL CAPER & goto fin
:ok11
echo   冒险模式 -^> level 11  AVALANCHE & goto fin
:ok12
echo   冒险模式 -^> level 12  PERILOUS SKI SLOPE & goto fin
:ok13
echo   冒险模式 -^> level 13  BOMB CHASE & goto fin
:ok14
echo   冒险模式 -^> level 14  METALLIC FORTRESS & goto fin
:ok15
echo   冒险模式 -^> level 15  ACID LEAK & goto fin
:ok16
echo   冒险模式 -^> level 16  CLOSED DOORS & goto fin
:ok17
echo   冒险模式 -^> level 17  LAVA NIGHT & goto fin
:ok18
echo   冒险模式 -^> level 18  MARBLE ISLANDS & goto fin
:ok19
echo   冒险模式 -^> level 19  OBLIVIOUS SPEEDWAY & goto fin
:ok20
echo   冒险模式 -^> level 20  WARPED TEMPLE OF DOOM & goto fin

:coop
cls
echo ============================================================
echo         双人模式 CO-OPERATIVE  -  关卡 1-10
echo ============================================================
echo.
echo     [1] coop1     [6] coop6
echo     [2] coop2     [7] coop7
echo     [3] coop3     [8] coop8
echo     [4] coop4     [9] coop9
echo     [5] coop5     [0] coop10   ^<TEMPLE OF DOOM^>
echo.
echo     [D] 返回主菜单
echo.
choice /c 1234567890D /n /m "请选择: "
if errorlevel 11 goto coop
if errorlevel 10 copy /y "DATA\SAVE\saves\coop10.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok10
if errorlevel 9 copy /y "DATA\SAVE\saves\coop9.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok9
if errorlevel 8 copy /y "DATA\SAVE\saves\coop8.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok8
if errorlevel 7 copy /y "DATA\SAVE\saves\coop7.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok7
if errorlevel 6 copy /y "DATA\SAVE\saves\coop6.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok6
if errorlevel 5 copy /y "DATA\SAVE\saves\coop5.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok5
if errorlevel 4 copy /y "DATA\SAVE\saves\coop4.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok4
if errorlevel 3 copy /y "DATA\SAVE\saves\coop3.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok3
if errorlevel 2 copy /y "DATA\SAVE\saves\coop2.sav" "DATA\SAVE\2UP GAME.sav" >nul & goto cok2
copy /y "DATA\SAVE\saves\coop1.sav" "DATA\SAVE\2UP GAME.sav" >nul
goto cok1

:cok1
echo   双人模式 -^> coop1 & goto fin
:cok2
echo   双人模式 -^> coop2 & goto fin
:cok3
echo   双人模式 -^> coop3 & goto fin
:cok4
echo   双人模式 -^> coop4 & goto fin
:cok5
echo   双人模式 -^> coop5 & goto fin
:cok6
echo   双人模式 -^> coop6 & goto fin
:cok7
echo   双人模式 -^> coop7 & goto fin
:cok8
echo   双人模式 -^> coop8 & goto fin
:cok9
echo   双人模式 -^> coop9 & goto fin
:cok10
echo   双人模式 -^> coop10  TEMPLE OF DOOM & goto fin

:clear
copy /y "DATA\SAVE\saves_adv\adv1.sav" "DATA\SAVE\BARRY.sav" >nul
echo   冒险模式进度已重置到 level 1 & goto fin

:fin
echo.
echo 现在启动游戏, 主菜单选对应模式 -^> RESUME GAME
echo.
choice /c YN /n /m "返回主菜单? (Y=返回 N=退出): "
if errorlevel 2 goto bye
goto menu

:noadv
echo [错误] 缺少 DATA\SAVE\BARRY.sav
echo 请先在游戏里打通冒险模式第一关, 生成存档后再用。
pause
endlocal
exit /b 1

:nocoop
echo [错误] 缺少 DATA\SAVE\2UP GAME.sav
echo 请先在游戏里打通双人模式第一关, 生成存档后再用。
pause
endlocal
exit /b 1

:bye
endlocal
exit /b 0
