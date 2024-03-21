//v27 adding ability to start a new game
//Mar 2024 - modified hint interrupt call to a function to facilitate doing processing within the function
//  and added a routine to show the board layout.  Fixed issues with checkmate and pawn promotion handling
#include <Adafruit_GFX.h>
#include <Adafruit_NeoMatrix.h>
#include <Adafruit_NeoPixel.h>


//setup control panel LEDs
#define controlPanelLED_PIN 4
#define controlPanelLED_COUNT 22
Adafruit_NeoPixel controlPanelLED(controlPanelLED_COUNT, controlPanelLED_PIN, NEO_GRB + NEO_KHZ800);

//chessboard LEDs
Adafruit_NeoMatrix chessboardLEDS = Adafruit_NeoMatrix(8, 8, A5,
  NEO_MATRIX_BOTTOM     + NEO_MATRIX_RIGHT +    //either top left or bottom right
  NEO_MATRIX_ROWS + NEO_MATRIX_ZIGZAG,
  NEO_GRB            + NEO_KHZ800);

const uint16_t colors[] = {
chessboardLEDS.Color(255, 0, 0), chessboardLEDS.Color(0, 255, 0), chessboardLEDS.Color(0, 0, 255) };

  
// const int inputButtons[] = {3,5,6,7,8,9,10,11,12,A1}; // this is for an Arduino Nano
const int inputButtons[] = {3,13,2,7,A3,9,10,11,12,A1};  //hint,1,2,3,4,5,6,7,8,OK (used for Adafruit M0 SAMD21)
const int buttonDebounceTime  = 300;

int currentBoard[8][8]; //an array to track the current state of the board
String piStarted = "No";

String humansMove;
String pisMove;
String boardPos;
String pisSuggestedBestMove;
String gameMode = "0";  // can be either 'Stockfish' or 'OnlineHuman' once set
String colourChoice; // can be either 'black' or 'white'
bool legalOrNot;

// Color definitions
#define BLACK    0x0000
#define BLUE     0x001F
#define RED      0xF800
#define GREEN    0x07E0
#define CYAN     0x07FF
#define ORANGE   0xFC00
#define MAGENTA  0xF81F
#define YELLOW   0xFFE0 
#define WHITE    0xFFFF 

// Serial port definitions for SAMD21 board
#define SerialUSB SERIAL_PORT_USBVIRTUAL

uint32_t cpWHITE = controlPanelLED.Color(255, 255, 255);
uint32_t cpDimWHITE = controlPanelLED.Color(10, 10, 10);
uint32_t cpBLACK = controlPanelLED.Color(0, 0, 0);

void setup() {
  // put your setup code here, to run once:
  Serial1.begin(9600);
  SerialUSB.begin(115200);

  //setup the buttons for inputting moves
  for (int i=0; i<10; i++)  //the less then value needs to represent how many buttons we are using for this to complete enough loops
  {
    pinMode(inputButtons[i], INPUT_PULLUP);
  }

  setUpBoard();

  //setup for the control panels neopixels
  controlPanelLED.begin();           // INITIALIZE NeoPixel strip object (REQUIRED)
  controlPanelLED.show();            // Turn OFF all pixels ASAP
  controlPanelLED.setBrightness(150); // Set BRIGHTNESS (max = 255)

  //setup for chessboard neopixels
  chessboardLEDS.begin();
  chessboardLEDS.setTextWrap(false);
  chessboardLEDS.setBrightness(120);
  chessboardLEDS.setTextColor(colors[0]);
  chessboardLEDS.show();
  
  waitForPiToStart();
  setUpGame();
  showChessboardMarkings();
}

void loop() {
  // put your main code here, to run repeatedly:
  humansMove = humansGo();
  sendToPi(humansMove, "M");
  printBoard();
  lightUpMove(humansMove,'Y');
  SerialUSB.println("Lighting up move");
  legalOrNot = checkPiForError();
  SerialUSB.println("Checking legality");
  if (legalOrNot == false ){
    // do nothing and start the human request again
    SerialUSB.println("Move discarded, please return the pieces and try another move");
    printBoard();
  } else {
    SerialUSB.println("Move is legal");
    updateBoard(humansMove);
    printBoard();
    showChessboardMarkings();
    pisMove = receiveMoveFromPi();
    if (pisMove == "checkmated") {
      controlPanelLED.fill(cpBLACK, 0, 6);
      controlPanelLED.setPixelColor(4, 255, 255, 255); // light up the OK button on the control panel
      controlPanelLED.show();
      int buttonPressed = 0;
      while (buttonPressed == 0) {
        int buttonPressed = detectButton();
        delay(buttonDebounceTime);
        if (buttonPressed == 9) {
          //new game start
          sendToPi("","n");
          setUpBoard(); //reset all the chess piece positions
          controlPanelLED.setPixelColor(5, 0, 0, 0); //turn off the hint button on the control panel
          controlPanelLED.fill(cpWHITE, 0, 5);
          controlPanelLED.show();
          int var1 = 0;
            while (var1 < 64){
              var1 = loadingStatus(var1);
              delay(25);
            }
          delay(1000);
          showChessboardMarkings();
          break;
        } else {
          buttonPressed = 0;
        }
      }
    } else {
      if (gameMode != "OnlineHuman"){
      pisSuggestedBestMove = pisMove.substring(5);
      SerialUSB.println("Suggested next move = " + pisSuggestedBestMove);
      }
      lightUpMove(pisMove,'N');
      SerialUSB.println(pisMove);
      updateBoard(pisMove);
      printBoard();
      if (gameMode != "OnlineHuman"){
        controlPanelLED.setPixelColor(5, 255, 255, 255); //light up the hint button on the control panel
        controlPanelLED.show();
        checkForComputerCheckMate(pisSuggestedBestMove, pisMove);
      }
      showChessboardMarkings();
    }
  }
}

String humansGo(){
  bool moveConfirmed = false;
  int buttonPressed = 0;
  while (moveConfirmed == false){ 
    controlPanelLED.fill(cpWHITE, 0, 4); //turn on the control panels co-ordinate lights
    controlPanelLED.show();
    String moveFrom = getCoordinates(buttonPressed); //get move from the player via the buttons
    controlPanelLED.fill(cpBLACK, 0, 21);  // turn off the control panel lights
    controlPanelLED.fill(cpWHITE, 0, 4); //turn on the control panels co-ordinate lights
    controlPanelLED.show();
    String moveTo = getCoordinates(11);
    controlPanelLED.fill(cpBLACK, 0, 21);  // turn off the control panel lights
    controlPanelLED.fill(cpWHITE, 0, 4); //turn on the control panels co-ordinate lights
    buttonPressed = 0;
    SerialUSB.println("You're moving the piece on " + moveFrom + " to " + moveTo);
    String humansMove = moveFrom + moveTo; //combine the moves into one four character command
    controlPanelLED.setPixelColor(4, 255, 255, 255); //light up the OK button on the control panel
    controlPanelLED.setPixelColor(5, 0, 0, 0); //turn off the hint button on the control panel
    controlPanelLED.show();
    lightUpMove(humansMove,'Y'); //and show the move entered to the player
    while (buttonPressed == 0){  //wait for them to approve it by pressing OK or enter new co-ordinates
      buttonPressed = detectButton();
    }
    if (buttonPressed == 9){
      controlPanelLED.fill(cpBLACK, 0, 6);; //once OK'ed proceed as normal and switch of the OK, hint light and co-ordinates lights
      controlPanelLED.show();
      moveConfirmed = true;
      return humansMove;
    } else {
      showChessboardMarkings();
    }
  }
  return " ";
}

void sendToPi(String message, String messageType){
  String messageToSend = message;
  Serial1.println("heypi" + messageType + messageToSend);
}

void updateBoard(String moveToUpdate){
  SerialUSB.print("Function:updateBoard - Piece to update: ");
  SerialUSB.println(moveToUpdate);
  
  int columnMovedFrom = columnNumber(moveToUpdate[0]);
  char rowMovedFrom = moveToUpdate[1];
  int irowMovedFrom = 7-(rowMovedFrom - '1');
  currentBoard[irowMovedFrom][columnMovedFrom] = 0;

  int columnMovedTo = columnNumber(moveToUpdate[2]);
  char rowMovedTo = moveToUpdate[3];
  int irowMovedTo = 7-(rowMovedTo - '1');
  currentBoard[irowMovedTo][columnMovedTo] = 1;
}

int columnNumber(char column){
  SerialUSB.println("Function: columnNumber");
  SerialUSB.println(column);
  switch (column){
    case 'a':
    //SerialUSB.println("Column A converted to number 0.");
    return 0;
    case 'b':
    return 1;
    case 'c':
    return 2;
    case 'd':
    //SerialUSB.println("Column D converted to number 3.");
    return 3;
    case 'e':
    //SerialUSB.println("Column E converted to number 4.");
    return 4;
    case 'f':
    return 5;
    case 'g':
    return 6;
    case 'h':
    return 7;
    default:
    return 0;
    //SerialUSB.println("No case statement found!");
  }
}

String receiveMoveFromPi(){
    SerialUSB.print("Function:receiveMoveFromPi...   ");
    SerialUSB.println("Waiting for response from Raspberry Pi");
    while (true){
      if (Serial1.available() > 0){
        String data = Serial1.readStringUntil('\n');
        SerialUSB.println(data);
        if (data.startsWith("heyArduinom")){
          SerialUSB.print("Move received from Pi: ");
          data = data.substring(11);
          SerialUSB.println(data);
          return data;
        } else if (data.startsWith("heyArduinoerror")){
          errorFromPi();
          return "error";
        } else if (data.startsWith("heyArduinob")){
          //put board return text here
          data = data.substring(11);
          return data;
        } else if (data.startsWith("heyArduinocheckmated")){
          checkForComputerCheckMate("", data.substring(20));
          return "checkmated";
        }
      }
    }
  }

void waitForPiToStart(){
    SerialUSB.println("Function:waitForPiToStart...   ");
    showChessboardOpeningMarkings();
    int chessSquaresLit = 0;
    while (true){
      chessSquaresLit = loadingStatus(chessSquaresLit);
      delay(1000);
      if (Serial1.available() > 0){
        String data = Serial1.readStringUntil('\n');
        if (data.startsWith("heyArduinoChooseMode")){
          while (chessSquaresLit < 64){
            chessSquaresLit = loadingStatus(chessSquaresLit);
            delay(15);
          }
          //turn on the control panels lights
          controlPanelLED.fill(cpWHITE, 0, 5);
          controlPanelLED.show();
          while (true) {
            gameMode = detectButton();
            delay(buttonDebounceTime);
              if (gameMode == "1"){
                gameMode = "Stockfish";
                sendToPi(gameMode, "G");
                SerialUSB.print("Pi is going to start a game with Stockfish.");
                chessboardLEDS.drawPixel(0,0,GREEN);
                chessboardLEDS.show();
                delay(500);
                chessboardLEDS.drawPixel(0,0,BLACK);
                chessboardLEDS.show();
                delay(500);
                chessboardLEDS.drawPixel(0,0,GREEN);
                chessboardLEDS.show();
                delay(500);
                chessboardLEDS.drawPixel(0,0,BLACK);
                chessboardLEDS.show();
                delay(500);
                break;
              } else if (gameMode == "2"){
                gameMode = "OnlineHuman";
                sendToPi(gameMode, "G");
                SerialUSB.print("Pi is going to start a game playing online against another board.");
                SerialUSB.println(gameMode);
                break;
              }    
            }
          }
          if (gameMode != "0"){
            break;
          }
        }
      }
    }

bool checkPiForError(){  //check five times during the next 03 seconds to see if we received an error from maxchess on the pi - if so run errorFromPi()
    SerialUSB.print("Function:checkPiForError...   ");
    SerialUSB.println("Waiting for response from Raspberry Pi");
    int checked = 0;
    while (checked<30){
      if (Serial1.available() > 0){
        String data = Serial1.readStringUntil('\n');
        SerialUSB.println(data);
        if (data.startsWith("heyArduinoerror")){
          SerialUSB.print("Error received from Pi: ");
          SerialUSB.println(data);
          errorFromPi();
          return false;
         } 
       } else {
        delay(100);
        SerialUSB.println(checked);
        checked++;
      }
    }
    return true;
  }

void errorFromPi(){
  SerialUSB.println("Error received from Raspberry Pi");
  int times = 0;
  while (times < 3){
    chessboardLEDS.fillRect(0,0,8,8, BLUE);
    chessboardLEDS.show(); 
    delay(500);
    chessboardLEDS.drawLine(0, 7, 7, 0, RED);
    chessboardLEDS.drawLine(0, 0, 7, 7, RED);
    chessboardLEDS.show();
    delay(500);
    times++;   
  }
  showChessboardMarkings();
}

void showBoardLayout() {
  uint16_t pieceColor;
  uint16_t sqColor;
  uint16_t currsqColor;
  SerialUSB.println("Showing board layout");
  // This first part lights up occupied spaces

  while (true) {
    String piecePos = receiveMoveFromPi();  // this is used to get each board square info from the RPi
    if (piecePos == "done") {
      break;
    }
    int x = piecePos.substring(0,1).toInt();
    int y = piecePos.substring(1,2).toInt();
    if (piecePos[2] == 'b') {
      chessboardLEDS.drawPixel(y,x,BLUE);
    }
    if (piecePos[2] == 'w') {
      chessboardLEDS.drawPixel(y,x,YELLOW);
    }
    chessboardLEDS.show();
    sendToPi("next" , "b");
  }
  controlPanelLED.fill(cpBLACK, 0, 6);
  controlPanelLED.setPixelColor(4, 255, 255, 255); // light up the OK button on the control panel
  controlPanelLED.setPixelColor(0, 255, 255, 255); // light up the 1-2 button on the control panel
  controlPanelLED.show();
  
  while (true) {
    int chkExit = detectButton();
    if (chkExit == 9) {  // OK pressed to continue on to identify pieces
      sendToPi("ok","b");
      break;
    }
    else if (chkExit == 1) { // 1 pressed for exit routine
      while (digitalRead(13) == LOW) {
        int x = 0;  // wait for A1 button to be released
      }
      sendToPi("exit","b");
      break;
    }
  }
  SerialUSB.println("Identifying Pieces");
  // This second part steps through the pieces on the board
  while (true) {
    String piecePos = receiveMoveFromPi();
    if (piecePos == "done") {
      break;
    }
    int x = piecePos.substring(0,1).toInt();
    int y = piecePos.substring(1,2).toInt();
    if (((x % 2) ^ (y % 2)) == 0) {  //determining if board square is white or black underneath the piece
      sqColor = WHITE;
    }
    else {
      sqColor = BLACK;
    }
    if (piecePos[2] == 'b') {
      pieceColor = BLUE;
    }
    else {
      pieceColor = YELLOW;
    }
    unsigned long currTime = millis();
    currsqColor = pieceColor;
    while (true) {
      if (digitalRead(A1) == LOW) {
        delay(buttonDebounceTime);
        chessboardLEDS.drawPixel(y,x,pieceColor);
        chessboardLEDS.show();
        sendToPi("next" , "b");
        break;
      }
      if (digitalRead(13) == LOW) {
        delay(buttonDebounceTime);
        while (digitalRead(13) == LOW) {
          int x = 0;  // wait for A1 button to be released
        }
        sendToPi("exit" , "b");
        break;
      }
      if ((millis() - currTime) > 200) {
        currTime = millis();
        if (currsqColor == pieceColor) {
          currsqColor = sqColor;
          chessboardLEDS.drawPixel(y,x,currsqColor);
          chessboardLEDS.show();
        }
        else {
          currsqColor = pieceColor;
          chessboardLEDS.drawPixel(y,x,currsqColor);
          chessboardLEDS.show();
        }
      }
    }
  }
}

String getCoordinates(int buttonAlreadyPressed) {
  SerialUSB.println("Getting co-ordinates...");
  int temp;
  String coordinates;
  String column = "x";
  String row = "x";
  int coordLt = 0;
  
  while (column == "x"){
    SerialUSB.println("Waiting for user to input column via button press...");
    if ((buttonAlreadyPressed != 0) && (buttonAlreadyPressed < 9)) {
      temp = buttonAlreadyPressed;
    } else {
      temp = detectButton();
    }
    switch (temp){
      case 1:
      column = "a";
      coordLt = 13;
      break;
      case 2:
      column = "b";
      coordLt = 12;
      break;
      case 3:
      column = "c";
      coordLt = 11;
      break;
      case 4:
      column = "d";
      coordLt = 10;
      break;
      case 5:
      column = "e";
      coordLt = 9;
      break;
      case 6:
      column = "f";
      coordLt = 8;
      break;
      case 7:
      column = "g";
      coordLt = 7;
      break;
      case 8:
      column = "h";
      coordLt = 6;
      break;
      case 10:
      if (buttonAlreadyPressed == 0) {
        hint(); // only accept hint before any buttons are pressed for move
        }
      else {
        continue;
      }
      default:
      break;
    }
  }
  
  controlPanelLED.setPixelColor(coordLt, 0, 255, 0); // light up letter coordinate in green
  controlPanelLED.show();
  delay(buttonDebounceTime);
  coordLt = 0;

  while (row == "x"){
    SerialUSB.println("Waiting for user to input row via button press...");
    temp = detectButton();
    switch (temp){
      case 1:
      row = "1";
      coordLt = 14;
      break;
      case 2:
      row = "2";
      coordLt = 15;
      break;
      case 3:
      row = "3";
      coordLt = 16;
      break;
      case 4:
      row = "4";
      coordLt = 17;
      break;
      case 5:
      row = "5";
      coordLt = 18;
      break;
      case 6:
      row = "6";
      coordLt = 19;
      break;
      case 7:
      row = "7";
      coordLt = 20;
      break;
      case 8:
      row = "8";
      coordLt = 21;
      break;
      default:
      break;
    }
  }
  controlPanelLED.setPixelColor(coordLt, 0, 255, 0); // light up number coordinate in green
  controlPanelLED.show();
  coordinates = column + row;
  SerialUSB.println("Co-ordinates are " + coordinates);
  delay(buttonDebounceTime);
  return coordinates;
}

int detectButton(){
  int val;
  SerialUSB.println("Waiting for a button to be detected...");
  while (true) {  
    if (digitalRead(13) == LOW){
      SerialUSB.println("Button 1 (for A/1) detected");
      delay(buttonDebounceTime);
      while (digitalRead(13) == LOW){
        int x = 0;
      }
      val = 1;
      break;
    } else if (digitalRead(2) == LOW){
      SerialUSB.println("Button 2 (for B/2) detected");
      delay(buttonDebounceTime);
      while (digitalRead(2) == LOW){
        int x = 0;
      }
      val = 2;
      break;
    } else if (digitalRead(7) == LOW){
      SerialUSB.println("Button 3 (for C/3) detected");
      delay(buttonDebounceTime);
      while (digitalRead(7) == LOW){
        int x = 0;
      }
      val = 3;
      break;
    } else if (digitalRead(A3) == LOW){
      SerialUSB.println("Button 4 (for D/4) detected");
      delay(buttonDebounceTime);
      while (digitalRead(A3) == LOW){
        int x = 0;
      }
      val = 4;
      break;
    } else if (digitalRead(9) == LOW){
      SerialUSB.println("Button 5 (for E/5) detected");
      delay(buttonDebounceTime);
      while (digitalRead(9) == LOW){
        int x = 0;
      }
      val = 5;
      break;
    } else if (digitalRead(10) == LOW){
      SerialUSB.println("Button 6 (for F/6) detected");
      delay(buttonDebounceTime);
      while (digitalRead(10) == LOW){
        int x = 0;
      }
      val = 6;
      break;
    } else if (digitalRead(11) == LOW){
      SerialUSB.println("Button 7 (for G/7) detected");
      delay(buttonDebounceTime);
      while (digitalRead(11) == LOW){
        int x = 0;
      }
      val = 7;
      break;
    } else if (digitalRead(12) == LOW){
      SerialUSB.println("Button 8 (for H/8) detected");
      delay(buttonDebounceTime);
      while (digitalRead(12) == LOW){
        int x = 0;
      }
      val = 8;
      break;
    } else if (digitalRead(A1) == LOW){
      SerialUSB.println("Button connected to OK detected");
      delay(buttonDebounceTime);
      while (digitalRead(A1) == LOW){
        int x = 0;
      }
      val = 9;
      break;
    } else if (digitalRead(3) == LOW){
      SerialUSB.println("Button connected to HINT detected");
      val = 10;
      break;
    }
  }
  return val;
}

void printBoard(){
  for(int i = 0; i < 8; i++) {
    for(int j = 0; j < 8; j++) {
      SerialUSB.print(currentBoard[i][j]);
      SerialUSB.print(",");
    }
    SerialUSB.println();
  }
}

void setUpGame(){
  //turn on the control panels lights
  controlPanelLED.fill(cpWHITE, 0, 4);
  controlPanelLED.show();

 if (gameMode == "Stockfish"){
  String gameDifficulty;
  String gameTimeout;
  
  SerialUSB.print("Set difficulty level: ");
  chessboardLEDS.fill(BLACK, 0);
  chessboardLEDS.drawFastVLine(2,2,4,MAGENTA);
  chessboardLEDS.drawFastHLine(2,6,4,MAGENTA);
  chessboardLEDS.show();
  
  gameDifficulty = map(detectButton(), 1, 8, 0, 20);
  delay(buttonDebounceTime);
  if (gameDifficulty.length() < 2){
    SerialUSB.println("Single digit");
    gameDifficulty = ("0" + gameDifficulty);
  }
  SerialUSB.println(gameDifficulty);
  sendToPi(gameDifficulty, "-");

  SerialUSB.print("Set computers move timout setting: ");
  chessboardLEDS.fill(BLACK, 0);
  chessboardLEDS.drawFastVLine(3,2,5,MAGENTA);
  chessboardLEDS.drawFastHLine(2,2,3,MAGENTA);
  chessboardLEDS.show();
  
  gameTimeout = map(detectButton(), 1, 8, 3000 ,12000);
  delay(buttonDebounceTime);
  SerialUSB.println(gameTimeout);
  sendToPi(gameTimeout, "-");
 } else if (gameMode == "OnlineHuman"){
  while (true){
    colourChoice = detectButton();
    delay(buttonDebounceTime);
    if (colourChoice == "1"){
      colourChoice = "White";
      SerialUSB.println("Chosen colour is white");
      sendToPi(colourChoice, "C");
      break;
    } else if (colourChoice == "2"){
      colourChoice = "Black";
      SerialUSB.println("Chosen colour is black");
      sendToPi(colourChoice, "C");
      break;
    }
  }
 }
  controlPanelLED.fill(cpDimWHITE, 6, 16);
  controlPanelLED.show();
}


void hint() {
 delay(buttonDebounceTime);
 int hintRequest = 1; // set initial value for hint
 while (digitalRead(3) == LOW) {
  if (digitalRead(A1) == LOW) {  // if "OK" button is pressed while HINT is pressed
    delay(buttonDebounceTime);
    while (digitalRead(A1) == LOW) {
      int x = 0; // kill time while wait for button to be released
    }
    //new game start
    sendToPi("","n");
    setUpBoard(); //reset all the chess piece positions
    controlPanelLED.setPixelColor(5, 0, 0, 0); //turn off the hint button on the control panel
    controlPanelLED.fill(cpWHITE, 0, 5);
    controlPanelLED.show();
    int var1 = 0;
      while (var1 < 64){
        var1 = loadingStatus(var1);
        delay(25);
      }
    delay(1000);
    showChessboardMarkings();
    hintRequest = 0;
    break;
  }
  if (digitalRead(12) == LOW) {  // if "H8" button is pressed while HINT is pressed
    delay(buttonDebounceTime);
    while (digitalRead(12) == LOW) {
      int x = 0; // kill time while wait for button to be released
    }
    sendToPi("shutdown", "x");
    hintRequest = 0;
    break;
  }
  if (digitalRead(13) == LOW) { // if "A1" button is pressed while HINT is pressed
    delay(buttonDebounceTime);
    SerialUSB.println("Sending board layout request to RPi...");
    while (digitalRead(13) == LOW) {
      int x = 0; // kill time while wait for button to be released
    }
    sendToPi("", "b");
    showBoardLayout();
    delay(buttonDebounceTime);
    showChessboardMarkings();
    controlPanelLED.fill(cpWHITE, 0, 6);
    controlPanelLED.setPixelColor(4, 0, 0, 0); //turn off the OK button on the control panel
    controlPanelLED.show();
    hintRequest = 0;
    break;
  }
  
  hintRequest = 1;
 }
 if ((hintRequest == 1) && (pisSuggestedBestMove.length() != 1)) {
  SerialUSB.println("Suggested best move= " + pisSuggestedBestMove);
  controlPanelLED.fill(cpBLACK, 0, 4);
  controlPanelLED.setPixelColor(5, 0, 0, 255); //light up the hint button on the control panel in blue
  controlPanelLED.show();
  lightUpMove(pisSuggestedBestMove,'H');
  showChessboardMarkings();
  controlPanelLED.setPixelColor(5, 255, 255, 255); //light up the hint button on the control panelin white again
  controlPanelLED.fill(cpWHITE, 0, 4);
  controlPanelLED.show();
 }
 else {
  SerialUSB.println("No hint provided by Pi yet.");
 }
}

void checkForComputerCheckMate(String hint, String attacker){
  SerialUSB.println("Checking if the Pi has check mated you....");
  SerialUSB.println("Attacker=" + attacker);
  int attackerColumn = columnNumber(attacker[2]);
  SerialUSB.println(attackerColumn);
  char attackerRow = attacker[3];
  SerialUSB.println(attackerRow);

  
  int iattackerRow = 7-(attackerRow - '1');
  SerialUSB.println(attackerColumn);
  SerialUSB.println(iattackerRow);

  
  if (hint.length() < 3){
    chessboardLEDS.drawRect(0,0,8,8,RED);
    chessboardLEDS.show();
    delay(1000);
    chessboardLEDS.drawRect(1,1,6,6,RED);
    chessboardLEDS.show();
    delay(1000);
    chessboardLEDS.drawRect(2,2,4,4,RED);
    chessboardLEDS.show();
    delay(1000);
    chessboardLEDS.drawRect(3,3,2,2,RED);
    chessboardLEDS.show();
    delay(1000);

    int times = 0;
    while (times < 5) {
      showChessboardMarkings();
      delay(1000);
      chessboardLEDS.drawPixel(attackerColumn,iattackerRow,RED);
      chessboardLEDS.show();
      delay(1000);
      times++;
    }
  }
}

void setUpBoard(){
    //set up the inital starting positions of chess pieces in the array
  for(int i = 0; i < 2; i++) {
    for(int j = 0; j < 8; j++) {
      currentBoard[i][j] = 1;
    }
  }
  for(int i = 2; i < 6; i++) {
    for(int j = 0; j < 8; j++) {
      currentBoard[i][j] = 0;
    }
  }
   for(int i = 6; i < 8; i++) {
    for(int j = 0; j < 8; j++) {
      currentBoard[i][j] = 1;
    }
  }
}
