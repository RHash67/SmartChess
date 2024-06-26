- The HINT button will only work before any coordinate buttons are pressed during the player's turn.

- If you change your mind while entering the coordinates (or make an entry mistake), just finish up entering the coordinate pair, but DON'T hit "OK".  When you start entering another pair of coordinates, the game will disregard the previous coordinate pair.

- To view the board piece position, hold down HINT, and then press A/1 (before any coordinate buttons are pressed during your turn).  The game will illuminate the occupied squares - blue for black, and yellow for white.  If you hit OK, you can then step through the occupied squares, with the OLED displaying the occupying piece.  Keep pressing OK to step through all the pieces.  Pressing A/1 at any time will exit the routine.

- To start a new game, hold down HINT, and then press OK.

- To shutdown the game, hold down HINT, and then press H/8.  This will send a shutdown command to the RPi so you can safely unplug the unit (if you otherwise just unplug it while the RPi happens to be writing to the SD card, you could corrupt the data).
