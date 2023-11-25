pyinstaller -F zodiac_core.py
RMDIR /S /Q zodiac
mkdir zodiac_vX
cd zodiak_vX
mkdir zodiac
robocopy C:\Users\roman\PycharmProjects\moo2_zodiac\dist\ C:\Users\roman\PycharmProjects\moo2_zodiac\zodiac_vX\zodiac\ zodiac_core.exe
robocopy C:\Users\roman\PycharmProjects\moo2_zodiac\ C:\Users\roman\PycharmProjects\moo2_zodiac\zodiac_vX\zodiac\ zodiac_core.py
robocopy C:\Users\roman\PycharmProjects\moo2_zodiac\ C:\Users\roman\PycharmProjects\moo2_zodiac\zodiac_vX\zodiac\ ZODIAC_TEMPLATE.CFG
robocopy C:\Users\roman\PycharmProjects\moo2_zodiac\ C:\Users\roman\PycharmProjects\moo2_zodiac\zodiac_vX\zodiac\ ZODIAC_TEMPLATE.LUA
robocopy C:\Users\roman\PycharmProjects\moo2_zodiac\ C:\Users\roman\PycharmProjects\moo2_zodiac\zodiac_vX\zodiac\ LICENSE.txt
robocopy C:\Users\roman\PycharmProjects\moo2_zodiac\ C:\Users\roman\PycharmProjects\moo2_zodiac\zodiac_vX\zodiac\ README.txt
cd zodiac_vX
cd zodiac
del  zodiac.exe
ren zodiac_core.exe zodiac.exe
cd ..
cd ..
"C:\Program Files\7-Zip\7z.exe" a -y "C:\Users\roman\PycharmProjects\moo2_zodiac\Zodiac_vX.zip" "C:\Users\roman\PycharmProjects\moo2_zodiac\zodiac_vX\*"