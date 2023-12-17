pyinstaller -F zodiac_core.py
RMDIR /S /Q zodiac_vX
mkdir zodiac_vX
cd zodiac_vX
mkdir zodiac
robocopy C:\Programming\gitProjects\pycharm\moo2_zodiac\dist\ C:\Programming\gitProjects\pycharm\moo2_zodiac\zodiac_vX\zodiac\ zodiac_core.exe
robocopy C:\Programming\gitProjects\pycharm\moo2_zodiac\ C:\Programming\gitProjects\pycharm\moo2_zodiac\zodiac_vX\zodiac\ zodiac_core.py
robocopy C:\Programming\gitProjects\pycharm\moo2_zodiac\ C:\Programming\gitProjects\pycharm\moo2_zodiac\zodiac_vX\zodiac\ ZODIAC_TEMPLATE.CFG
robocopy C:\Programming\gitProjects\pycharm\moo2_zodiac\ C:\Programming\gitProjects\pycharm\moo2_zodiac\zodiac_vX\zodiac\ ZODIAC_TEMPLATE.LUA
robocopy C:\Programming\gitProjects\pycharm\moo2_zodiac\ C:\Programming\gitProjects\pycharm\moo2_zodiac\zodiac_vX\zodiac\ LICENSE.txt
robocopy C:\Programming\gitProjects\pycharm\moo2_zodiac\ C:\Programming\gitProjects\pycharm\moo2_zodiac\zodiac_vX\zodiac\ README.txt
robocopy C:\Programming\gitProjects\pycharm\moo2_zodiac\ C:\Programming\gitProjects\pycharm\moo2_zodiac\zodiac_vX\zodiac\ CHANGELOG.txt
cd zodiac
del zodiac.exe
ren zodiac_core.exe zodiac.exe
cd ..
cd ..
"C:\Program Files\7-Zip\7z.exe" a -y "C:\Programming\gitProjects\pycharm\moo2_zodiac\Zodiac_vX.zip" "C:\Programming\gitProjects\pycharm\moo2_zodiac\zodiac_vX\*"