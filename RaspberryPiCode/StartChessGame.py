# Interactive Chessboard - www.DIYmachines.co.uk
# This codes includes large sections kindly shared on www.chess.fortherapy.co.uk, which itself incorporates alot of other peoples code.
# Please feel free to modify, adapt and share. Any excisting licenses included must remain intact as well as including acknowledgment to those who have contribued.
# This program plays chess using Stockfish the open source chess engine, using the ChessBoard library to manage the board.
# It is written in Python 2.7 because chessboard is.
# It assumes you have got the python libraries chessboard, subprocess and time

# Modified March 2024 - add show board layout functions, improved hint routine, and issues with checkmate and pawn promotion


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
    # stx=""
    engine.stdin.write('isready\n')
    print('\nengine:')
    while True :
        text = engine.stdout.readline().strip()
        if text == 'readyok':
            break
        if text !='':
            print('\t'+text)
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
    # stx=""
    mtext=''
    engine.stdin.write('isready\n')
    print('\nengine:')
    while True :
        text = engine.stdout.readline().strip()
        # if text == 'readyok':
            # break
        if text !='':
            print('\t'+text)
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
    #put('setoption name Best Book Move value true')
    #get()
    #put('setoption name OwnBook value true')
    #get()
    #put('uci')
    #get ()
    put('ucinewgame')
    maxchess.resetBoard()
    maxchess.setPromotion(maxchess.QUEEN)
    #print("Promotion set to ")
    #print(maxchess.getPromotion())
    fmove=""
    brdmove=""
    time.sleep(2)
    sendToScreen ('Please enter','your move:','')
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
    # Get a move from the board
    brdmove = bmessage[1:5].lower()
    movefrom = brdmove[0:2]
    torank = int(brdmove[3:4])
    pieceType = pieceAtPos(movefrom) # check to see if pawn is being moved (for promotion check)
    # now validate move
    # if invalid, get reason & send back to board
      #  maxchess.addTextMove(move)
    if maxchess.addTextMove(brdmove) == False :
                        etxt = "error"+ str(maxchess.getReason())+brdmove
                        maxchess.printBoard()
                        sendToScreen ('Illegal move!','Enter new','move...','14')
                        sendtoboard(etxt)
                        return fmove

#  elif valid  make the move and send Fen to board

    else:
        maxchess.printBoard()
        print ("brdmove")
        print(brdmove)
        sendToScreen (brdmove[0:2] + '->' + brdmove[2:4] ,'','Thinking...','20')
        if ((pieceType == 'P') and (torank == 8)):
             print("Pawn is being promoted")
             brdmove = brdmove + "Q"  # Stockfish needs pawn promotion piece value as part of move notation
        fmove =fmove+" " +brdmove

        cmove = "position startpos moves"+fmove
        print (cmove)

            #        if fmove == True :
            #                move = "position startpos moves "+move
            #        else:
            #               move ="position fen "+maxfen

        # put('ucinewgame')
        # get()


        put(cmove)
        # send move to engine & get engines move


        put("go movetime " +movetime)
        # time.sleep(6)
        # text = get()
        # put('stop')
        text = sget()
        print (text)
        smove = text[9:13]
        hint = text[21:25]
        if text[13:14] != " " :  # if computer pawn is promoted need to include the promotion piece
             smove = text[9:14]
             hint = text[22:26]
        blackWins = 0
        if hint == "" :
             time.sleep(2) # computer has checkmated player - need to wait
             blackWins = 1 
        if text[9:15] == "(none)":  # computer is checkmated
             print ("Computer checkmated!")
             sendToScreen ('WHITE','WINS!','','30')
             sendtoboard("checkmated" + brdmove)
             smove = ""
        if ((maxchess.addTextMove(smove) != True) and (text[9:15] != "(none)")) :
                        stxt = "e"+ str(maxchess.getReason())+smove
                        maxchess.printBoard()
                        sendtoboard(stxt)

        else:
                        if text[9:15] == "(none)":
                             fmove = ""
                             return fmove
                        else:
                             temp=fmove
                             fmove =temp+" " +smove
                             # stx = smove+hint
                             maxchess.printBoard()
                             # maxfen = maxchess.getFEN()
                             print ("computer move: " +smove)
                             if blackWins == 1:
                                  sendToScreen ('BLACK','WINS!','','30')
                             else:
                                  if len(smove) > 4:
                                       sendToScreen (smove[0:2] + '->' + smove[2:4] ,'Promote: ' + smove[4:5],'Your move...','20')
                                  else:
                                       sendToScreen (smove[0:2] + '->' + smove[2:4] ,'','Your move...','20')
                             smove ="m"+smove[0:4]
                             sendtoboard(smove +"-"+ hint)
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
                     sendtoboardnd("b" + str(x) + str(y) + str(sqColor))
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
                         sendtoboardsht("b" + str(x) + str(y) + str(sqColor))
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

#Choose a mode of gameplay on the Arduino
time.sleep(1)
sendtoboard("ChooseMode")
print ("Waiting for mode of play to be decided on the Arduino")
sendToScreen ('Choose opponent:','1) Against PC','2) Remote human')
gameplayMode = getboard()[1:].lower()
print ("Requested gameplay mode:")
print(gameplayMode)


if gameplayMode == 'stockfish':
    while True:
        sendtoboard("ReadyStockfish")

        # get intial settings (such as level)
        print ("Waiting for level command to be received from Arduino")
        sendToScreen ('Choose computer','difficulty level:','(1 -> 8)')
        skillFromArduino = getboard()[1:3].lower()
        print ("Requested skill level:")
        print(skillFromArduino)

        # get intial settings (such as move time)
        print ("Waiting for move time command to be received from Arduino")
        sendToScreen ('Choose computer','move time:','(1 -> 8)')
        movetimeFromArduino = getboard()[1:].lower()
        print ("Requested time out setting:")
        print(movetimeFromArduino)


        # assume new game
        print ("\n Chess Program \n")
        sendToScreen ('NEW','GAME','','30')
        time.sleep(2)
        sendToScreen ('Please enter','your move:','')
        skill = skillFromArduino
        movetime = movetimeFromArduino #6000
        fmove = newgame()

        while True:

            # Get  message from board
            bmessage = getboard()
            print ("Move command received from Arduino")
            print(bmessage)
            # Message options   Move, Newgame, level, style, board position
            code = bmessage[0]

	        # if code == 'b':
		        # print ("Sending board position to Arduino")
		        # sendtoboard("b" + maxchess.getBoard())


            # decide which function to call based on first letter of txt
            fmove=fmove
            if code == 'm':
            	fmove = bmove(fmove)
            elif code == 'n':
            	fmove = newgame()
            elif code == 'b':
                showLayout()
            #elif code == 'c':
            #    showLayout2()
            #elif code == 'l':
            #    level()
            #elif code == 's':
            #    style()
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
