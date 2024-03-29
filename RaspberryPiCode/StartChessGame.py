# Interactive Chessboard - www.DIYmachines.co.uk
# This codes includes large sections kindly shared on www.chess.fortherapy.co.uk, which itself incorporates alot of other peoples code.
# Please feel free to modify, adapt and share. Any excisting licenses included must remain intact as well as including acknowledgment to those who have contribued.
# This program plays chess using Stockfish the open source chess engine, using the ChessBoard library to manage the board.
# It is written in Python 2.7 because chessboard is.
# It assumes you have got the python libraries chessboard, subprocess and time

# Modified March 2024 - add show board layout functions, and allow player to play as black
# improved hint routine, and issues with checkmate and pawn promotion detection
# changed new game routine to allow player to change computer level & move time


# initiate chessboard
from ChessBoard import ChessBoard
import subprocess, time, serial
maxchess = ChessBoard()

if __name__ == '__main__':
    ser = serial.Serial('/dev/ttyAMA0', 9600, timeout=1)   # for Pi Zero use '/dev/ttyAMA0' and for others use '/dev/ttyUSB0'.
    ser.flush()

# initiate stockfish chess engine

engine = subprocess.Popen(
    'stockfish',
    universal_newlines=True,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE
    )

def get():

    # using the 'isready' command (engine has to answer 'readyok')
    # to indicate current last line of stdout
    engine.stdin.write('isready\n')
    # print('\nengine:')
    while True :
        text = engine.stdout.readline().strip()
        if text == 'readyok':
            break
        if text !='':
            tmpx = 0
            # print('\t'+text)
        if text[0:8] == 'bestmove':
            return text

def putAdafruit(command):
    print('\nTrying to send to AdafruitIO:\n\t'+command)
    remotePlayer.stdin.write("send\n")
    remotePlayer.stdin.write(colourChoice+'\n')
    remotePlayer.stdin.write(command+'\n')
    while True :
        text = remotePlayer.stdout.readline().strip()
        if text[6:17] == 'piece moved':
            print(text)
            break


def getAdafruit():
    print('\nTrying to read remote boards move from AdafruitIO:\n\t')
    remotePlayer.stdin.write("receive\n")
    remotePlayer.stdin.write(colourChoice+'\n')
    while True :
        text = remotePlayer.stdout.readline().strip()
        #if text[0:11] == 'Piece moved':
        print('The remote move was: ' + text)
        return text


def sget():

    # using the 'isready' command (engine has to answer 'readyok')
    # to indicate current last line of stdout
    mtext=''
    engine.stdin.write('isready\n')
    # print('\nengine:')
    while True :
        text = engine.stdout.readline().strip()
        if text !='':
             tmpx = 0
            # print('\t'+text)
        if text[0:8] == 'bestmove':
            mtext=text
            break
    return mtext

def getboard():
    """ gets a text string from the board """
    print("\n Waiting for command from the Board")
    while True:
        if ser.in_waiting > 0:
            btxt = ser.readline().decode('utf-8').rstrip().lower()
            if btxt.startswith('heypixshutdown'):
                shutdownPi()
                break
            if btxt.startswith('heypi'):
                btxt = btxt[len('heypi'):]
                print(btxt)
                return btxt
                break
            else:
                continue


def sendtoboard(stxt):
    """ sends a text string to the board """
    print("\n Sent to board: heyArduino" + stxt)
    stxt = bytes(str(stxt).encode('utf8'))
    time.sleep(2)
    ser.write(b"heyArduino" + stxt + "\n".encode('ascii'))

def sendtoboardsht(stxt):
    """ same as sendtoboard except after only 0.5s delay """
    print("\n Sent to board: heyArduino" + stxt)
    stxt = bytes(str(stxt).encode('utf8'))
    time.sleep(0.5)
    ser.write(b"heyArduino" + stxt + "\n".encode('ascii'))

def sendtoboardnd(stxt):
    """ same as sendtoboard except no delay """
    stxt = bytes(str(stxt).encode('utf8'))
    ser.write(b"heyArduino" + stxt + "\n".encode('ascii'))

def newgame():
    sendToScreen ('NEW','GAME','','30')
    get ()
    put('uci')
    get ()
    put('setoption name Skill Level value ' +skill)
    get ()
    put('setoption name Hash value 128')
    get ()
    put('ucinewgame')
    maxchess.resetBoard()
    maxchess.setPromotion(maxchess.QUEEN)
    fmove=""
    brdmove=""
    time.sleep(2)
    return fmove

def newgameOnline():
    maxchess.resetBoard()
    maxchess.setPromotion(maxchess.QUEEN)
    print("Promotion set to ")
    print(maxchess.getPromotion())
    fmove=""
    brdmove=""
    return fmove



def bmove(fmove):
    """ assume we get a command of the form ma1a2 from board"""
    fmove=fmove
    global compWins
    # Get a move from the board
    brdmove = bmessage[1:5].lower()
    movefrom = brdmove[0:2]
    torank = int(brdmove[3:4])
    pieceType = pieceAtPos(movefrom) # check to see if pawn is being moved (for promotion check)
    # now validate move
    # if invalid, get reason & send back to board
    if maxchess.addTextMove(brdmove) == False :
                        etxt = "error"+ str(maxchess.getReason())+pdispCoord
                        maxchess.printBoard()
                        sendToScreen ('Illegal move!','Enter new','move...','14')
                        sendtoboard(etxt)
                        return fmove

#  elif valid  make the move and send coordinate notation to board

    else:
        maxchess.printBoard()
        print ("brdmove")
        print(brdmove)
        sendToScreen (pdispCoord[0:2] + '->' + pdispCoord[2:4] ,'','Thinking...','20')
        if pcolorFromArduino == 'w':
             if ((pieceType == 'P') and (torank == 8)):
                 print("Pawn is being promoted")
                 brdmove = brdmove + "Q"  # Stockfish needs pawn promotion piece value as part of move notation
        else:
             if ((pieceType == 'p') and (torank == 1)):
                  print("Pawn is being promoted")
                  brdmove = brdmove + "q" # lower case for Stockfish if player is black
        fmove =fmove+" " +brdmove

        cmove = "position startpos moves "+fmove
        # print (cmove)
        put(cmove)  
        put("go movetime " +movetime) # send move sequence to engine & get engine's move
        # sget() gets best next move and subsequent hint move from Stockfish
        # standard return format: bestmove a1a2 ponder b1b2 (b1b2 = hint for move after bestmove)
        # for pawn promotion: bestmove a1a2q ponder b1b2 (this example promotes to queen)
        # if computer is checkmated, format is:  bestmove (none)
        # if player is checkmated, then no ponder move
        text = sget()
        print (text)
        smove = text[9:13]  # the bestmove from Stockfish
        hint = text[21:25]  # the ponder move from Stockfish
        if ((text[13:14] != " ") and (text[13:14] != "e")) :  # checking for pawn promotion character
             smove = text[9:14]  # standard format bestmove a1a2q ponder b1b2 for pawn promotion
             hint = text[22:26]
        dispsmove = smove  # used to display the computer's move
        disphint = hint  # used to display the hint move
        if ((pcolorFromArduino == 'b') and (dispsmove != '(non')):
             tmpdispsmove1 = coordTranspose(dispsmove[0:2]) # need to transpose if player is black
             tmpdispsmove2 = coordTranspose(dispsmove[2:4])
             if len(dispsmove) > 4 :
                  tmpdispsmove3 = dispsmove[4:5]
             else :
                  tmpdispsmove3 = ""
             dispsmove = tmpdispsmove1 + tmpdispsmove2 + tmpdispsmove3
        if ((pcolorFromArduino == 'b') and (disphint != '')):
             tmpdisphint1 = coordTranspose(disphint[0:2])
             tmpdisphint2 = coordTranspose(disphint[2:4])
             disphint = tmpdisphint1 + tmpdisphint2
        if hint == "" :
             time.sleep(2) # computer has checkmated player - need to wait
             compWins = 1 
        if text[9:15] == "(none)":  # computer is checkmated - i.e. no bestmove
             time.sleep(2)
             print ("Computer checkmated!")
             sendToScreen ('PLAYER','WINS!','','30')
             sendtoboard("checkmated" + pdispCoord)
             compWins = 0
             smove = ""
        if ((maxchess.addTextMove(smove) != True) and (text[9:15] != "(none)")) :
                        stxt = "e"+ str(maxchess.getReason())+dispsmove
                        maxchess.printBoard()
                        sendtoboard(stxt)

        else:
                        if text[9:15] == "(none)":
                             fmove = ""
                             return fmove
                        else:
                             temp=fmove
                             fmove =temp+" " +smove
                             maxchess.printBoard()
                             print ("computer move: " +smove)
                             if len(dispsmove) > 4:
                                  sendToScreen (dispsmove[0:2] + '->' + dispsmove[2:4] ,'Promote: ' + dispsmove[4:5],'Your move...','20')
                             else:
                                  sendToScreen (dispsmove[0:2] + '->' + dispsmove[2:4] ,'','Your move...','20')
                             dispsmove ="m"+dispsmove[0:4]
                             sendtoboard(dispsmove +"-"+ disphint)
                             return fmove

def cfirstmove(fmove):
     # if player is black, computer moves first routine
     fmove=fmove
     # maxchess.printBoard()
     sendToScreen ('','','Thinking...','20')
     cmove = "position startpos moves "
     print(cmove)
     put(cmove) # put initial starting position into Stockfish for initial best move for computer
     put("go movetime " +movetime)
     text = sget()
     print (text)
     smove = text[9:13]
     hint = text[21:25]
     dispsmove = smove  # used to display the computer's move
     disphint = hint  # used to display the hint move
     if pcolorFromArduino == 'b':
         tmpdispsmove1 = coordTranspose(dispsmove[0:2]) # need to transpose if player is black
         tmpdispsmove2 = coordTranspose(dispsmove[2:4])
         dispsmove = tmpdispsmove1 + tmpdispsmove2
         tmpdisphint1 = coordTranspose(disphint[0:2])
         tmpdisphint2 = coordTranspose(disphint[2:4])
         disphint = tmpdisphint1 + tmpdisphint2
     fmove = smove
     maxchess.addTextMove(smove)
     maxchess.printBoard()
     print ("computer move: " +smove)
     sendToScreen (dispsmove[0:2] + '->' + dispsmove[2:4] ,'','Your move...','20')
     dispsmove ="m"+dispsmove[0:4]
     sendtoboard(dispsmove +"-"+ disphint)
     return fmove

def bmoveOnline(fmove):
    """ assume we get a command of the form ma1a2 from board"""
    fmove=fmove
    print ("F move is now set to ")
    print(fmove)
    # Extract the move from the message received from the chessboard
    brdmove = bmessage[1:5].lower()
    print ("Brdmove is now set to ")
    print(brdmove)
    # now validate move
    # if invalid, get reason & send back to board
    #  maxchess.addTextMove(move)
    if maxchess.addTextMove(brdmove) == False :
        print("The move is illegal")
        etxt = "error"+ str(maxchess.getReason())+brdmove
        maxchess.printBoard()
        sendtoboard(etxt)
        return fmove

#  elif valid  make the move and send to AdafruitIO

    else:
        print("The move is legal")
        maxchess.printBoard()
        print ("brdmove")
        print(brdmove)
        putAdafruit(brdmove)

        fmove =fmove+" " +brdmove

        cmove = "position startpos moves"+fmove
        print (cmove)
        sendToScreen ('Waiting for' ,'the other','Player...','20')


        #Wait for remote player move to be posted online.
        text = getAdafruit()
        print (text)
        smove = text
        hint = "xxxx"
        temp=fmove
        fmove =temp+" " +smove
        stx = smove+hint
        maxchess.printBoard()
        print ("Remote players move: " +smove)

        if maxchess.addTextMove(smove) != True :
                stxt = "e"+ str(maxchess.getReason())+smove
                maxchess.printBoard()
                sendtoboard(stxt)

        else:
                temp=fmove
                fmove =temp+" " +smove
                stx = smove+hint
                maxchess.printBoard()
                sendToScreen (smove[0:2] + '->' + smove[2:4] ,'','Your move...','20')
                smove ="m"+smove
                sendtoboard(smove +"-"+ hint)

        return fmove


def put(command):
    print('\nyou:\n\t'+command)
    engine.stdin.write(command+'\n')

def shutdownPi():
    sendToScreen ('Shutting down...','Wait 20s then','disconnect power.')
    time.sleep(5)
    from subprocess import call
    call("sudo nohup shutdown -h now", shell=True)
    time.sleep(10)

def sendToScreen(line1,line2,line3,size = '14'):
    """Send three lines of text to the small OLED screen"""
    screenScriptToRun = ["python3", "/home/pi/SmartChess/RaspberryPiCode/printToOLED.py", '-a '+ line1, '-b '+ line2, '-c '+ line3, '-s '+ size]
    subprocess.Popen(screenScriptToRun)

# displays board layout for the user
def showLayout():
    bdlayout = maxchess.getBoard()
    
    # routine for lighting up occupied spaces
    for x in range(8):
         for y in range(8):
              layoutsymb = bdlayout[x][y]
              if layoutsymb != '.':
                     if layoutsymb == 'r':
                         sqColor = "b"
                     elif layoutsymb == 'n':
                         sqColor = "b"
                     elif layoutsymb == 'b':
                         sqColor = "b"
                     elif layoutsymb == 'q':
                         sqColor = "b"
                     elif layoutsymb == 'k':
                         sqColor = "b"
                     elif layoutsymb == 'p':
                        sqColor = "b"
                     elif layoutsymb == 'R':
                         sqColor = "w"
                     elif layoutsymb == 'N':
                         sqColor = "w"
                     elif layoutsymb == 'B':
                         sqColor = "w"
                     elif layoutsymb == 'Q':
                         sqColor = "w"
                     elif layoutsymb == 'K':
                         sqColor = "w"
                     elif layoutsymb == 'P':
                         sqColor = "w"
                     else :
                         sqColor = ""
                     if pcolorFromArduino == 'w':
                          sendtoboardnd("b" + str(x) + str(y) + str(sqColor))
                     else:
                          sendtoboardnd("b" + str(pbLayoutList[x]) + str(pbLayoutList[y]) + str(sqColor))
                     while True :
                         nextPiece = getboard()
                         if nextPiece == 'bnext':
                             break
                         else :
                             continue
    sendtoboardsht("bdone")
    sendToScreen('Identify Pieces?','OK - Continue','1 - Exit','14')
    showPieces = getboard()
    bkFlag = False
    if showPieces == 'bok':
         # routine for stepping through pieces
         for x in range(8):
             for y in range(8):
                 layoutsymb = bdlayout[x][y]
                 if layoutsymb != '.':
                         if layoutsymb == 'r':
                             pColor = "Black"
                             pType = "Rook"
                             sqColor = "b"
                         elif layoutsymb == 'n':
                             pColor = "Black"
                             pType = "Knight"
                             sqColor = "b"
                         elif layoutsymb == 'b':
                             pColor = "Black"
                             pType = "Bishop"
                             sqColor = "b"
                         elif layoutsymb == 'q':
                             pColor = "Black"
                             pType = "Queen"
                             sqColor = "b"
                         elif layoutsymb == 'k':
                             pColor = "Black"
                             pType = "King"
                             sqColor = "b"
                         elif layoutsymb == 'p':
                             pColor = "Black"
                             pType = "Pawn"
                             sqColor = "b"
                         elif layoutsymb == 'R':
                             pColor = "White"
                             pType = "Rook"
                             sqColor = "w"
                         elif layoutsymb == 'N':
                             pColor = "White"
                             pType = "Knight"
                             sqColor = "w"
                         elif layoutsymb == 'B':
                             pColor = "White"
                             pType = "Bishop"
                             sqColor = "w"
                         elif layoutsymb == 'Q':
                             pColor = "White"
                             pType = "Queen"
                             sqColor = "w"
                         elif layoutsymb == 'K':
                             pColor = "White"
                             pType = "King"
                             sqColor = "w"
                         elif layoutsymb == 'P':
                             pColor = "White"
                             pType = "Pawn"
                             sqColor = "w"
                         else :
                             pColor = ""
                             pType = ""
                             sqColor = ""
                         if pcolorFromArduino == 'w':
                              print(str(x) + str(y) + str(sqColor))
                              sendtoboardsht("b" + str(x) + str(y) + str(sqColor))
                         else:
                              print(str(pbLayoutList[x]) + str(pbLayoutList[y]) + str(sqColor))
                              sendtoboardnd("b" + str(pbLayoutList[x]) + str(pbLayoutList[y]) + str(sqColor))
                         sendToScreen(pColor, pType, '', '20')
                         while True :
                             nextPiece = getboard()
                             if nextPiece == 'bnext':
                                 break
                             elif nextPiece == 'bexit':
                                 break
                             else :
                                 continue
                 if nextPiece == 'bexit':
                    bkFlag = True
                    break
             if bkFlag:
                break
    sendtoboardsht("bdone")
    sendToScreen('','','Your move...','20')

    # end of routine

def pieceAtPos(space):
     bdlayout = maxchess.getBoard()
     filespace = space[0:1]
     rankspace = space[1:2]
     ranknum = ord(filespace) - 97  # convert piece file position to integer number
     filenum = 8 - int(rankspace)
     return (bdlayout[filenum][ranknum]) # coordinate system is opposite for alg notation vs
        # board layout

     # end of routine

def coordTranspose(coord):
     # Transpose player-as-black coordinate to stockfish standard coordinate
     # coordinate must be in form of a7, b6, etc
     coltemp = pbColList[ord(coord[0:1]) - 97]
     rowtemp = pbRowList[int(coord[1:2]) - 1]
     return coltemp + rowtemp

     # end of routine

# Main routine start
# Choose a mode of gameplay on the Arduino
time.sleep(1)
sendtoboard("ChooseMode")
print ("Waiting for mode of play to be decided on the Arduino")
sendToScreen ('Choose opponent:','1) Against PC','2) Remote human')
gameplayMode = getboard()[1:].lower()
print ("Requested gameplay mode:")
print(gameplayMode)
newGameStart = 1
pcolorFromArduino = 'w'
pbColList = ["h","g","f","e","d","c","b","a"] # used for transposing coordinates when player = black
pbRowList = ["8","7","6","5","4","3","2","1"]
pbLayoutList = [7,6,5,4,3,2,1,0] # used for transposing board check position when player = black

if gameplayMode == 'stockfish':
    while True:
        if newGameStart == 1 :
 
             # get level setting
             print ("Waiting for level command to be received from Arduino")
             sendToScreen ('Choose computer','difficulty level:','(1 -> 8)')
             skillFromArduino = getboard()[1:3].lower()
             print ("Requested skill level:")
             print(skillFromArduino)

             # get move time setting
             print ("Waiting for move time command to be received from Arduino")
             sendToScreen ('Choose computer','move time:','(1 -> 8)')
             movetimeFromArduino = getboard()[1:].lower()
             print ("Requested time out setting:")
             print(movetimeFromArduino)

             # get player color setting
             print ("Waiting for player color selection to be received from Arduino")
             sendToScreen ('Player color:','1 = white','2 = black')
             pcolorFromArduino = getboard()[1:].lower()
             print ("Requested player color:")
             print (pcolorFromArduino)

             # assume new game
             print ("\n Chess Program \n")
             newGameStart = 0
             compWins = 0
             skill = skillFromArduino
             movetime = movetimeFromArduino
             fmove = newgame()
             if pcolorFromArduino == 'b' :
                 compFirstMove = 1
             else :
                 compFirstMove = 0
                 sendToScreen ('Please enter','your move:','')

        if compFirstMove == 1 :  # if player is black, computer moves first
             fmove=fmove
             compFirstMove = 0
             fmove = cfirstmove(fmove)
        if compWins == 1:
             sendToScreen ('COMPUTER','WINS!','','20')
        # Get message from board
        # PROGRAM POINT A (corresponds with Chess_Simp_forM0 sketch location A)
        bmessage = getboard()
        print ("Move command received from Arduino")
        print(bmessage)
        pdispCoord = bmessage[1:5].lower()
        # Message options   Move, start new game, board position
        code = bmessage[0]

        # decide which function to call based on first letter of txt
        fmove=fmove
        if code == 'm':
             if pcolorFromArduino == 'b':
                  bmessagetmp1 = coordTranspose(bmessage[1:3]) # need to transpose player black coords
                  bmessagetmp2 = coordTranspose(bmessage[3:5])
                  bmessage = "m" + bmessagetmp1 + bmessagetmp2
             fmove = bmove(fmove)
        elif code == 'n':
             sendToScreen ('NEW','GAME','','30')
             time.sleep(2)
             newGameStart = 1
        elif code == 'b':
             showLayout()
        else :
             sendtoboard('error at option')

elif gameplayMode == 'onlinehuman':
        print("Playing online chossen")

        updateScriptToRun = ["python3", "/home/pi/SmartChess/RaspberryPiCode/update-online.py"]


        remotePlayer = subprocess.Popen(updateScriptToRun,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
                                )
        while True:
            time.sleep(1)
            sendtoboard("ReadyOnlinePlay")

            sendToScreen ('Select a colour:','1 = White/First','2 = Black/Second')


            # get colour choice so we know if we are going first or second
            print ("Waiting for colour choice to be received from Arduino")
            colourChoice = getboard()

            print ("Colour choice received from Arduino")
            print(colourChoice)
            if colourChoice == "cblack":
                skipFirstGo = "Yes"
            elif colourChoice == "cwhite":
                skipFirstGo = "No"

            #Let adafruitIO know we are ready by labelling ou colour as that online
            putAdafruit("ready")


            # assume new game
            print ("\n Chess Program \n")
            fmove = newgameOnline()
            while True:

                if skipFirstGo == "Yes":
                    text = getAdafruit()
                    print (text)
                    smove = text
                    hint = "xxxx"
                    temp=fmove
                    fmove =temp+" " +smove
                    stx = smove+hint
                    maxchess.printBoard()
                    print ("Remote players move: " +smove)

                    if maxchess.addTextMove(smove) != True :
                            stxt = "e"+ str(maxchess.getReason())+smove
                            maxchess.printBoard()
                            sendtoboard(stxt)

                    else:
                            temp=fmove
                            fmove =temp+" " +smove
                            stx = smove+hint
                            maxchess.printBoard()
                            sendToScreen (smove[0:2] + '->' + smove[2:4] ,'','Your move...','20')
                            smove ="m"+smove
                            sendtoboard(smove +"-"+ hint)
                            skipFirstGo = "NoMore"
                    #print ("Waiting for first white players move...")
                    #firstWhiteMove = getAdafruit()
                    #print ('Whites first move is ' + firstWhiteMove)
                    #firstWhiteMove = 'm' + firstWhiteMove
                    #print(firstWhiteMove)
                    #bmoveOnline(firstWhiteMove)
                # Get  message from chessboard
                bmessage = getboard()
                print ("Command received from Arduino")
                print(bmessage)
                # Take the fist character as a message code:
                # Message options   Move, Newgame, level, style
                code = bmessage[0]



                # decide which function to call based on first letter of txt
                fmove=fmove
                if code == 'm': #the arduino has submitted a move to the Pi
                    print("Fmove is currently: ")
                    print(fmove)
                    fmove = bmoveOnline(fmove) #Process the move
                elif code == 'n':
                    fmove = newgameOnline()
                #elif code == 'l':
                #    level()
                #elif code == 's':
                #    style()
                else :
                    sendtoboard('error at option')
