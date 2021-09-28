from flask import Flask, render_template, session, request, url_for, redirect, jsonify
from flask_socketio import SocketIO, join_room, leave_room, send, emit
import os, uuid, time, json
from chess import Piece, Rook, Knight, Bishop, Queen, King, Pawn

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

socketio = SocketIO(app, cors_allowed_origins='*')

channels = []
channels_cnt = {}

games = {}
users = {}

## ------------------------------------------- game

class Game:
    def __init__(self, p1, p2, gameId):
        self.p1 = {
            'team': 'white',
            'id': p1['userId'],
            'name': p1['name'],
            'countryCode': p1['countryCode'],
            'pass': p1['pass'],
            'checked': False
        }
        self.p2 = {
            'team': 'black',
            'id': p2['userId'],
            'name': p2['name'],
            'countryCode': p2['countryCode'],
            'pass': p2['pass'],
            'checked': False
        }
        self.p = {
            self.p1['id']: self.p1,
            self.p2['id']: self.p2
        }

        self.lastMove = None

        self.gameId = gameId

        self.movesList = {}
        self.count = 0
        self.takes = False

        self.board = {}
        self.setupBoard()

        self.turn = self.p1['id']

        self.gameState = 1 ## 1 means game in progress, 0 means game over

        self.pReady = []

        self.emit_game_state()


    def setupBoard(self):
        '''
            sets up pieces to starting positions on board
        '''
        for x in range(1,9):
            for y in range(1,9):
                self.board[(x, y)] = None

        pieceOrder = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for i in self.board:

            ## place white pawns
            if i[1] == 2:
                self.board[i] = Pawn('white', i, 'pos')

            ## place black pawns
            if i[1] == 7:
                self.board[i] = Pawn('black', i, 'neg')

            ## place white bottom row
            if i[1] == 1:
                self.board[i] = pieceOrder[ (i[0]-1) ]('white', i)
            
            ## place black bottom row
            if i[1] == 8:
                self.board[i] = pieceOrder[ (i[0]-1) ]('black', i)
            

    def check(self, userId, userPass):
        '''
            returns true if userId is p1 or p2, otherwise False
        '''

        ## check if user is in players list
        if userId in self.p:
            
            ## check if user pass is valid
            if self.p[userId]['pass'] == userPass:
                return True
        else:
            return False


    def checkMate(self, allMoves, team):
        '''
            returns true if the team (color) in question has no (legal) moves
            otherwise False
        '''
        return True not in [ len(v['availableMoves']) != 0 for v in allMoves if v['color'] == team ]


    def emit_game_state(self):
        '''
            emits the current game state
        '''
        
        allAvailableMoves = self.getAllAvailableMoves()
        team = self.p[self.turn]['team']

        if self.checkMate(allAvailableMoves, team):
            self.gameOver()

        emit('game_state', {
            'turn': self.turn,
            self.p1['id']: {
                **{ i: v for (i,v) in self.p[self.p1['id']].items() if i not in ['id', 'pass', 'checked'] }
            },
            self.p2['id']: {
                **{ i: v for (i,v) in self.p[self.p2['id']].items() if i not in ['id', 'pass', 'checked'] }
            },
            'board': allAvailableMoves,
            'players': [self.p1['id'], self.p2['id']],
            'lastMove': self.lastMove,
            'movesList': self.movesList
        }, to=self.gameId)


    def noteMove(self, move, specialNotation=None):
        '''
            tracks move
        '''
        chars = {
            1: 'a',
            2: 'b',
            3: 'c',
            4: 'd',
            5: 'e',
            6: 'f',
            7: 'g',
            8: 'h'
        }
        names = {
            'pawn': '',
            'rook': 'R',
            'bishop': 'B',
            'knight': 'N',
            'queen': 'Q',
            'king': 'K'
        }
        m = str(names[move['name']])

        if self.takes: ## notation for taking a piece
            if m == '': ## if pawn and taking piece, add x coord to notation
                m += str(chars[int(move['startPos'][0])])
            m += 'x'

        m +=  str(chars[int(move['newPos'][0])]) + str(move['newPos'][1])

        if self.p[self.turn]['checked']: ## notation for check
            m += '+'

        if type(specialNotation) == str: ## castles notation
            m = specialNotation

        elif type(specialNotation) == list: ## promotion notation
            if specialNotation[0] == 'promotion':
                m = str(chars[int(move['newPos'][0])]) + str(move['newPos'][1]) + specialNotation[1][0].upper()

        if self.count not in self.movesList:
            self.movesList[self.count] = [m]
        else:
            self.movesList[self.count].append(m)

        self.takes = False


    def movePiece(self, piece, startPos, targetPos, specialNotation=None, pawnPromotion=False):
        '''
            moves piece from start to target and adds move to move tracker
        '''

        if self.board[ (int(targetPos[0]), int(targetPos[1])) ] != None:
            self.takes = True

        self.board[ (int(targetPos[0]), int(targetPos[1])) ] = piece # set target position piece to curr piece
        self.board[ (int(startPos[0]), int(startPos[1])) ] = None # set old pos of piece to None on board
        piece.setPos( int(targetPos[0]), int(targetPos[1])) ## set piece pos attribute
        piece.hasMoved = True

        ## switch turn to other player
        if self.p1['id'] == self.turn: ## p1 moved
            self.turn = self.p2['id']

            self.count += 1

            ## after move, check if move checks enemy king
            if piece.enemyChecked(self.board):
                self.p2['checked'] = True ## set enemy player to checked
        else: ## p2 moved
            self.turn = self.p1['id']

            ## after move, check if move checks enemy king
            if piece.enemyChecked(self.board):
                self.p1['checked'] = True ## set enemy player to checked
            

        self.lastMove = {
            'name': piece.name,
            'startPos': (int(startPos[0]), int(startPos[1])),
            'newPos': (int(targetPos[0]), int(targetPos[1]))
        }

        data = {
            'turn': self.turn,
            self.p1['id']: {
                'team': self.p1['team']
            },
            self.p2['id']: {
                'team': self.p2['team']
            },
            'players': [self.p1['id'], self.p2['id']],
            'oldPos': startPos,
            'newPos': targetPos
        }

        ## if pawn promotion add it to the emit
        if pawnPromotion:
            data['promotion'] = pawnPromotion.name
            self.board[ (int(targetPos[0]), int(targetPos[1])) ] = pawnPromotion

        emit('move_piece', data, to=self.gameId)


        self.noteMove(self.lastMove, specialNotation)

        self.emit_game_state()

        self.p[self.turn]['checked'] = False ## remove checked        
    

    def getAllAvailableMoves(self):
        '''
            returns a list of all available moves for each player 

            also removes any illegal moves (such as opening your own king up to check)
        '''
        allAllowedMoves = []

        for (i, v) in self.board.items(): ## iterate through every piece on board
            if v != None:
                legalVMoves = []
                if v.name == 'pawn':
                    vMoves = v.getAvailableMoves(self.board, self.lastMove)
                else:
                    vMoves = v.getAvailableMoves(self.board)

                for count in range(len(vMoves)): ## remove any coords from piece available moves that are illegal
                    coord = vMoves[count]
                    if not self.checkCauseSelfCheck( v, (v.pos[0], v.pos[1]), (coord[0], coord[1]) ):
                        legalVMoves.append( (coord[0], coord[1]) )
                
                data = v.getData(self.board, self.lastMove)
                data['availableMoves'] = legalVMoves
                allAllowedMoves.append(data)
        
        return allAllowedMoves

    
    def checkCauseSelfCheck(self, piece, startPos, targetPos):
        '''
            returns true if move would open players' own king to check or doesnt protect king from current check

            otherwise return False

            (false means the move is legal, true means the move is illegal)
        '''

        team = piece.color
        tmp = self.board.copy()

        tmp[ (int(targetPos[0]), int(targetPos[1])) ] = piece # set target position piece to curr piece
        tmp[ (int(startPos[0]), int(startPos[1])) ] = None # set old pos of piece to None on board

        return any([ i.enemyChecked(tmp) for i in tmp.values() if (i != None and i.color != team) ])
    

    def move(self, userId, piece, target, promoteTo=False):
        '''
            check if piece can move to target and return True or False.

            if True then emit the piece move.
        '''
    
        if userId == self.turn: ## check if its the user's turn
            p = self.board[ (int(piece[0]), int(piece[1])) ]
            if (self.p1['team'] == p.color and self.p1['id'] == userId) or (self.p2['team'] == p.color and self.p2['id'] == userId): # check if the piece is the user's
                if p.name == 'pawn':
                    check = p.canMoveTo(int(target[0]), int(target[1]), self.board, self.lastMove) ## check if the piece can move to target
                else:
                    check = p.canMoveTo(int(target[0]), int(target[1]), self.board) ## check if the piece can move to target

                ## check if move is illegal
                if self.checkCauseSelfCheck(p, piece, target):
                    return False


                ### if piece type is pawn and check is a list object, then do en passant or promotion
                if p.name == 'pawn' and type(check) == list:

                    ### en passant
                    if check[0] == 'en passant':

                        ## removes target pawn that is victim in en passant
                        targetPawn = check[1]
                        targetSquare = check[2]

                        self.board[ targetPawn ] = None
                        emit('en_passant', {
                            'targetPawn': [*targetPawn]
                        }, to=self.gameId)

                        self.takes = True

                        self.movePiece(p, piece, targetSquare)

                        return True

                    ### pawn promotion
                    elif check[0] == 'promotion':
                        if promoteTo == False: ## if no parameter is given for what the pawn will promote into, then return False
                            return False 
                        else:
                            acceptedPieces = {
                                'rook': Rook,
                                'bishop': Bishop,
                                'knight': Knight,
                                'queen': Queen,
                            }
                            if promoteTo not in acceptedPieces: ## make sure promoton piece is valid
                                return False
                            else:
                                newPiece = acceptedPieces[promoteTo]( p.color, (int(target[0]), int(target[1])) )
                                self.movePiece(p, piece, target, specialNotation=['promotion', promoteTo], pawnPromotion=newPiece)

                                return True

                ### if piece is king and check is a list object then do castles
                elif p.name == 'king' and type(check) == list:
                    if check[0] == 'castles':

                        ## moves rook from start to target pos
                        rookStart = check[1]
                        rookTarget = check[2]
                        rookPiece = self.board[ rookStart ]

                        self.board[ rookStart ] = None
                        
                        emit('castles', {
                            'rookPos': [rookStart[0], rookStart[1]],
                            'targetPos': [rookTarget[0], rookTarget[1]]
                        }, to=self.gameId)

                        self.board[ rookTarget ] = rookPiece # set target position piece to curr piece
                        self.board[ rookStart ] = None # set old pos of piece to None on board
                        rookPiece.setPos( rookTarget[0], rookTarget[1] ) ## set piece pos attribute
                        rookPiece.hasMoved = True

                        ### move piece func moves king
                        kingTarget = check[3]
                        self.movePiece(p, piece, kingTarget, specialNotation=check[4])

                        return True

                elif check:
                    self.movePiece(p, piece, target)
                
                    return True    

        return False
    
    
    def readyUp(self, userId):
        '''
            if userId is not in self.pReady then add it add it and return True otherwise False
        '''
        if self.gameState == 0:

            if userId not in self.pReady:
                self.pReady.append(userId)

                emit('user_ready', {
                    'ready': len(self.pReady)
                }, to=self.gameId)

                return True

        return False


    def gameOver(self, gameEndType=None):
        ''' 
            ends game, emits to players game end type (like checkmate, stalemate draw or resign) the winner and loser and prepares game for rematch option
        '''
        #print('GAME OVER')
        self.gameState = 0


        data = {
            'ready': len(self.pReady)
        }
        if gameEndType == None:
            currP = self.p[self.turn]
            otherP = [ v for (i, v) in self.p.items() if i != self.turn ][0]

            if currP['checked']:
                data['gameEndType'] = '%s won' % (otherP['team'])
                data['by'] = 'by checkmate'
            elif otherP['checked']:
                data['gameEndType'] = '%s won' % (currP['team'])
                data['by'] = 'by checkmate'
            else:
                data['gameEndType'] = 'Stalemate'
                data['by'] = ''
        else:
            otherP = [ v for (i, v) in self.p.items() if i != gameEndType['id'] ][0]

            data['gameEndType'] = '%s won' % (otherP['team'])

            data['by'] = 'by resignation'


        emit('game_over', data, to=self.gameId)

## ------------------------------------------- /game




### ------------------- pages

@app.route('/', methods=['GET', 'POST'])
def app_index():
    return render_template('home.html')


@app.route('/game/<gameId>', methods=['GET', 'POST'])
def app_game(gameId):
    return render_template('game.html', gameId=gameId, userId=str(uuid.uuid4()), ipdataco_api_key=os.getenv('IPDATACO_API_KEY'))

### ------------------- /pages


@app.route('/create/', methods=['GET', 'POST'])
def create():
    gameId = str(uuid.uuid4())

    channels.append(gameId)
    channels_cnt[gameId] = {}

    return jsonify({'res': gameId})


### join room if exists, if 2 players in room after joining, start game. if game has started, check if user and pass is valid, if so then put user back in game
@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    name = data['name']
    countryCode = data['countryCode']

    if room in channels: ## check if user can join (only let two clients in a room)
        l = len(channels_cnt[room].keys())

        ## if user is already in when game is still in waiting room (this occurs when user refreshes page while in waiting room)
        if any([ v['userId'] == username for (i,v) in channels_cnt[room].items() ]):
            join_room(room)
            return {'status': True}

        if l < 2:
            join_room(room)

            if 'userpass' in data:
                userpass = data['userpass']
            else:
                userpass = str(uuid.uuid4())
            
            channels_cnt[room]['p%s' % (l+1)] = {
                'userId': username,
                'name': name,
                'countryCode': countryCode,
                'pass': userpass
            }

            ## both players joined start game
            if l+1 == 2:
                games[room] = Game(channels_cnt[room]['p1'], channels_cnt[room]['p2'], room)

                channels.remove(room)
                del channels_cnt[room]

            return {'status': True, 'userpass': userpass}
    elif room in games: ## check if user is in game (game started)
        if games[room].check(username, data['userpass']):
            join_room(room)
            games[room].emit_game_state()
            return {'status': True}

    
    return {'status': False}


### check if username and password is valid and is that player's turn, then try move piece
@socketio.on('move')
def move(data):
    username = data['username']
    userpass = data['userpass']
    room = data['room']
    if room in games:

        ## validate username and pass
        if games[room].check(username, userpass):
            
            ## check if game still running 
            if games[room].gameState == 1:
                
                ## check if promote paramater is there
                if 'promote' in data.keys():
                    if games[room].move(username, data['piece'], data['target'], promoteTo=data['promote']):
                        return True
                else: 
                    if games[room].move(username, data['piece'], data['target']):
                        return True
    
    return False


### readys up a user after gameover for rematch, and if both are ready then starts new game
@socketio.on('rematch')
def rematch(data):
    username = data['username']
    userpass = data['userpass']
    room = data['room']
    if room in games:

        ## validate username and pass
        if games[room].check(username, userpass):
            
            ## check if game still running 
            if games[room].gameState == 0:
                if games[room].readyUp(username):
                    
                    ## check if there are two players ready for rematch
                    if len(games[room].pReady) == 2: ## create new game instance with same room id - switch two players teams
                        tmp = games[room]

                        p1 = {
                            'userId': tmp.p2['id'],
                            'name': tmp.p2['name'],
                            'countryCode': tmp.p2['countryCode'],
                            'pass': tmp.p2['pass']
                        }
                        p2 = {
                            'userId': tmp.p1['id'],
                            'name': tmp.p1['name'],
                            'countryCode': tmp.p1['countryCode'],
                            'pass': tmp.p1['pass']
                        }

                        ## remove old game
                        del games[room]

                        ## create new game instance
                        games[room] = Game(p1, p2, room)

                    return True
    return False


### emote and phrases message
allowed = ['thumbs', 'angry', 'crying', 'laughing', 'Good luck!', 'Well played!', 'Wow!', 'Thanks!', 'Good game!', 'Oops']
@socketio.on('message')
def message(data):
    username = data['username']
    userpass = data['userpass']
    message = data['message']
    room = data['room']

    if not any( [ True for i in allowed if message == i] ):
        return False

    if room in games:
        if games[room].check(username, userpass):
            emit('emote', {
                'from': username,
                'message': message
            }, to=room)
            return True
    
    return False


### add check user disconnected 
@socketio.on('connect')
def disconnect():
    ##print('CONNECT')
    ##print(request.sid)
    pass

@socketio.on('disconnect')
def disconnect():
    ##print('DISCONNECT')
    ##print(request.sid)
    pass



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8080)