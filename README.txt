Zodiac Version 1.1.2

Last update of this mod: 25th December October 2023; Tested with version 1.50.22 improved

What is it?
A tool to manually 'draw' galaxies that can then be used in Master of Orion 2 games

How to use it:
1. Ensure your Master Of Orion 2 is using Version 1.50 (patch can be found at https://moo2mod.com/)
2. Copy this folder (zodiac) into the mod-folder of 150, e.g. C:\DOSBox-0.74\Orion2\150\mods\
3. In the copied folder, run zodiac.exe (or zodiac_core.py if you are using Python)
4. Draw a galaxy
    - First, choose a galaxy size (if you change it later on it will delete everything you have drawn!)
    - Place star systems with a left click
    - Right-click star systems to delete them
    - Left-click two different star systems to create wormholes between them
    - Right-click empty space to deselect a star system
5. Save the galaxy in one of the 10 slots, e.g. press 'Save ZODIAC0' to export it as a special LUA mod
6. In the 150 launcher, enable your Zodiac galaxy via checkbox (or dropdown in case you saved multiple Zodiac galaxies)
7. Start the game with the launcher as usual; ensure galaxy size in MOO2 is the same as was set for the Zodiac galaxy

Multiple homeworld and Orion locations:
You can place more than one Orion location in which case one of these designated locations will be picked at random
whenever a new game starts. The same principle applies when having more homeworld locations than players.

Compatibility:
Zodiac is, in general, not properly compatible with other mods that move star systems around, such as Full Mirror.
It should be compatible with mods that swap or modify homeworlds, such as HW_APART, HW_CLOSE or Mirror Home Systems,
as long as these mods have a mod order greater than 150 (which is the case for the three given examples).
Zodiac is compatible with map mods because it will not interfere with the chances of star systems having specific
colors, planets, monsters or specials.
An exception to this are the chances for additional black holes and wormholes, these will be set to zero.
Also, the amount of stars allowed per galaxy is currently hard-coded.

Using ENABLE.CFG directly:
To enable a Zodiac galaxy directly in the ENABLE.CFG of 150 you need to provide the save slot number from 0 to 9, e.g.
enable ZODIAC6;

Resources:
- Executable version for Windows is available at https://moo2mod.com/
- Source-code is available at https://github.com/Epirasque/moo2zodiac and it is known to run with Python 3.8

Contact:
Join the MOO2 discord server (https://discord.gg/45BnvY4) and contact Epirasque, or write an email to romanhable@web.de
