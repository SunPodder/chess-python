


def getPiecesBetweenStraightLine(cx, cy, x, y, board):
    pieces = []

    if x != cx and y == cy: ## moving on x axis
        if x > cx:
            for i in range(cx+1, x):
                if piece := board[ (i, y) ]:
                    pieces.append(piece)
        else:
            for i in range(x+1, cx):
                if piece := board[ (i, y) ]:
                    pieces.append(piece)
        
    elif y != cy and x == cx: ## moving on y axis
        if y > cy:
            for i in range(cy+1, y):
                if piece := board[ (x, i) ]:
                    pieces.append(piece)
        else:
            for i in range(y+1, cy):
                if piece := board[ (x, i) ]:
                    pieces.append(piece)
        
    return pieces


def getPiecesBetweenDiagLine(cx, cy, x, y, board):
    pieces = []
    
    cnt = 1
    if x > cx:
        for xs in range(cx+1, x):
    
            if cy > y:
                if piece := board[ (xs, cy-cnt) ]:
                    pieces.append(piece)
            elif y > cy:
                if piece := board[ (xs, cy+cnt) ]:
                    pieces.append(piece)

            cnt+=1
    elif cx > x:
        for xs in range(x+1, cx):

            if cy > y:
                if piece := board[ (xs, cy-cnt) ]:
                    pieces.append(piece)
            elif y > cy:
                if piece := board[ (xs, y-cnt) ]:
                    pieces.append(piece)
            
            cnt+=1
        
    return pieces


def targetHasSameColor(color, x, y, board):
    ## check if theres any piece at target
    if piece := board[ (x, y) ]:
        if piece.color == color: ## if there is then check if piece is same color
            return True
    
    return False


### ------------------------------- piece classes


class Piece:
    def __init__(self, color, pos):
        self.color = color
        self.name = None
        self.pos = pos

        self.setName()

    def getData(self, board, lastMove):
        return ({
            'color': self.color,
            'name': self.name,
            'x': self.pos[0],
            'y': self.pos[1],
            'availableMoves': self.getAvailableMoves(board)
        })

    def setName(self):
        pass

    def withinBounds(self, x, y):
        '''
            checks if target coordinates are valid
        '''
        return ( 1 <= x <= 8 and  1 <= y <= 8 )

    def setPos(self, x, y):
        self.pos = (x, y)

    def canMoveTo(self, x, y, board):
        '''
            returns true or false depending on piece can move to target x and y
        '''
        if (x, y) in self.getAvailableMoves(board):
            return True

        return False

    def getTargets(self, board):
        '''
            returns all positions on board that are being threatened by this piece
        '''
        return self.getAvailableMoves(board)

    def enemyChecked(self, board):
        '''
            returns whether or not this piece is threatening opponent king
        '''
        return any([ board[ (pos[0], pos[1]) ].name == 'king' for pos in self.getTargets(board) if board[ (pos[0], pos[1]) ] != None ]) 



class Rook(Piece):
    def setName(self):
        self.name = 'rook'

        self.hasMoved = False


    def getAvailableMoves(self, board):
        moves = []

        ## x axis available moves
        for i in range(0, 9):
            if self.withinBounds(i, self.pos[1]) and not targetHasSameColor(self.color, i, self.pos[1], board):
                if len(getPiecesBetweenStraightLine(self.pos[0], self.pos[1], i, self.pos[1], board)) == 0:
                    moves.append( (i, self.pos[1]) )

        ## y axis available moves
        for i in range(0, 9):
            if self.withinBounds(self.pos[0], i) and not targetHasSameColor(self.color, self.pos[0], i, board):
                if len(getPiecesBetweenStraightLine(self.pos[0], self.pos[1], self.pos[0], i, board)) == 0:
                    moves.append( (self.pos[0], i) )

        return moves

        

class Knight(Piece):
    def setName(self):
        self.name = 'knight'

        self.hasMoved = False


    def getAvailableMoves(self, board):
        moves = []

        ## all the possible moves of knight
        lMoves = [(-1, 2), (1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1)]

        for i in lMoves:
            tmpX = i[0] + self.pos[0]
            tmpY = i[1] + self.pos[1]

            if self.withinBounds(tmpX, tmpY) and not targetHasSameColor(self.color, tmpX, tmpY, board):
                moves.append( (tmpX, tmpY) )

        return moves


class Bishop(Piece):
    def setName(self):
        self.name = 'bishop'

        self.hasMoved = False


    def getAvailableMoves(self, board):
        moves = []

        def iterate(x, y):
            for i in range(1, 9):
                pos = (self.pos[0] + (x*i), self.pos[1]+ (y*i))

                ## if coord is within bounds 
                if self.withinBounds(*pos):
                    if not targetHasSameColor(self.color, pos[0], pos[1], board):
                        moves.append(pos)
                        if board[ (pos[0], pos[1]) ]:
                            break
                    else:
                        break
                else:
                    break
            return
        iterate(-1,1) ## top left diagonal
        iterate(1,1) ## top right diagonal
        iterate(-1,-1) ## bottom left diagonal
        iterate(1,-1) ## bottom right diagonal

        return moves
        

class Queen(Piece):
    def setName(self):
        self.name = 'queen'

        self.hasMoved = False


    def getAvailableMoves(self, board):
        moves = []

        #### -------------------- straight line moves
        ## x axis available moves
        for i in range(0, 9):
            if self.withinBounds(i, self.pos[1]) and not targetHasSameColor(self.color, i, self.pos[1], board):
                if len(getPiecesBetweenStraightLine(self.pos[0], self.pos[1], i, self.pos[1], board)) == 0:
                    moves.append( (i, self.pos[1]) )

        ## y axis available moves
        for i in range(0, 9):
            if self.withinBounds(self.pos[0], i) and not targetHasSameColor(self.color, self.pos[0], i, board):
                if len(getPiecesBetweenStraightLine(self.pos[0], self.pos[1], self.pos[0], i, board)) == 0:
                    moves.append( (self.pos[0], i) )


        #### -------------------- diagonal moves
        def iterate(x, y):
            for i in range(1, 9):
                pos = (self.pos[0] + (x*i), self.pos[1]+ (y*i))

                ## if coord is within bounds 
                if self.withinBounds(*pos):
                    if not targetHasSameColor(self.color, pos[0], pos[1], board):
                        moves.append(pos)
                        if board[ (pos[0], pos[1]) ]:
                            break
                    else:
                        break
                else:
                    break
            return
        iterate(-1,1) ## top left diagonal
        iterate(1,1) ## top right diagonal
        iterate(-1,-1) ## bottom left diagonal
        iterate(1,-1) ## bottom right diagonal


        return moves


class King(Piece):
    def setName(self):
        self.name = 'king'

        self.hasMoved = False


    def getTargets(self, board): ### dont count castling as a target
        moves = []

        for x in range(-1,2):
            for y in range(-1,2):
                if self.withinBounds(x+self.pos[0], y+self.pos[1]) and not targetHasSameColor(self.color, x+self.pos[0], y+self.pos[1], board):
                    moves.append( (x+self.pos[0], y+self.pos[1]) )

        return moves


    def getAvailableMoves(self, board):
        moves = []

        for x in range(-1,2):
            for y in range(-1,2):
                if self.withinBounds(x+self.pos[0], y+self.pos[1]) and not targetHasSameColor(self.color, x+self.pos[0], y+self.pos[1], board):
                    moves.append( (x+self.pos[0], y+self.pos[1]) )

        
        ## ------------------------------- castling func
        def castlingFunc(longways=False):
            i = 1
            inbetween = [6,7]
            rook = 8
            target = 7
            if longways:
                i = -1
                inbetween = [4,3,2]
                rook = 1
                target = 3

            ## checks rook is at right coord
            if rook := board[ (rook, self.pos[1]) ]:
                ## checks if rook is hasnt moved and is on players' team
                if rook.name == 'rook' and rook.hasMoved == False and rook.color == self.color:
                    ## makes sure two squares between rook and king are empty
                    if board[ (inbetween[0], self.pos[1]) ] == None and board[ (inbetween[1], self.pos[1]) ] == None:
                        if longways:
                            if board[ (inbetween[2], self.pos[1]) ] != None:
                                return False

                        checkSafe = False

                        ## checks if the pieces inbetween the king and rook are safe for the king to be in (x = 6, 7 for shortways)
                        for cnt in range(3):
                            tmp = board.copy()
                            tmpKing = tmp[ (self.pos[0], self.pos[1])  ]
                            tmp[ (self.pos[0], self.pos[1])  ] = None
                            tmp[ (self.pos[0]+(i*cnt), self.pos[1]) ] = tmpKing

                            if any([ i.enemyChecked(tmp) for i in tmp.values() if (i != None and i.color != self.color) ]):
                                break

                            if cnt == 2:
                                checkSafe = True

                        if checkSafe: ## if both squares are safe for king then add (7, pos[1]) to moveList
                            moves.append( (target, self.pos[1]) )
                            return True

            return False

        if not self.hasMoved:
            castlingFunc(); ## castle shortways
            castlingFunc(longways=True) ## castle longways
        
        return moves

    def canMoveTo(self, x, y, board):
        '''
            returns true or false depending on piece can move to target x and y
        '''
        ### check if king has not moved and his target x is 3 or 7
        if self.hasMoved == False and x in [3, 7]:
            if (x, y) in self.getAvailableMoves(board):
                if x == 3: ## castles longways
                    return ['castles', (1, self.pos[1]), (4, self.pos[1]), (3, self.pos[1]), 'o-o-o']
                elif x == 7: ## castles shortways
                    return ['castles', (8, self.pos[1]), (6, self.pos[1]), (7, self.pos[1]), 'o-o']

            elif (x, y) in check[0]:
                return True
        else:
            if (x, y) in self.getAvailableMoves(board):
                return True

        return False



class Pawn(Piece):
    def __init__(self, color, pos, direction):
        self.color = color
        self.name = 'pawn'
        self.pos = pos
        self.direction = direction ## can be "pos" or "neg"

        self.hasMoved = False


    def getAvailableMoves(self, board, lastMove, doingEnPassant=False):
        moves = []

        steps = 1

        upOrDown = 1 if self.direction == 'pos' else -1

        if not self.hasMoved:
            steps = 2

        cnt = 0
        ## gets all forward available moves (1 usually or 2 if on starting pos)
        for i in range(steps): 
            cnt += upOrDown
            tmpY = self.pos[1] + cnt

            if self.withinBounds(self.pos[0], tmpY) and not targetHasSameColor(self.color, self.pos[0], tmpY, board):

                ## check if any pieces inbetween target and piece on straight line
                if len(getPiecesBetweenStraightLine(self.pos[0], self.pos[1], self.pos[0], tmpY, board)) == 0:
                    
                    if not board[ (self.pos[0], tmpY) ]:
                        moves.append((self.pos[0], tmpY))

        ## gets all available moves for taking diagonally
        diagonals = [(-1, 1), (1, 1)] if self.direction == 'pos' else [(-1, -1), (1, -1)]
        for item in diagonals:
            tmpX = item[0] + self.pos[0]
            tmpY = item[1] + self.pos[1]

            if self.withinBounds(tmpX, tmpY) and not targetHasSameColor(self.color, tmpX, tmpY, board):

                if b := board[ (tmpX, tmpY) ]:
                    if b.color != self.color:
                        moves.append((tmpX, tmpY))

        enPassantMove = {}
        ## en passant 
        if lastMove:
            if lastMove['name'] == 'pawn': ## if last move was a pawn

                ## if the last move (by a pawn) was 2 steps
                if abs(lastMove['startPos'][1] - lastMove['newPos'][1]) == 2:

                    ## if last move by pawn is right beside the pawn
                    if (lastMove['newPos'][1] == self.pos[1]) and (abs(lastMove['newPos'][0] - self.pos[0]) == 1):
                        
                        step = 1 if self.direction == 'pos' else -1
                        moves.append( (lastMove['newPos'][0], (self.pos[1]+step)) )
                        enPassantMove = {
                            'targetPawn': lastMove['newPos'],
                            'targetSquare': (lastMove['newPos'][0], (self.pos[1]+step))
                        }
        
        if doingEnPassant:
            return moves, enPassantMove

        return moves
        
    def canMoveTo(self, x, y, board, lastMove):
        '''
            returns true or false depending on piece can move to target x and y
        '''
        if lastMove:
            check = self.getAvailableMoves(board, lastMove, doingEnPassant=True)

            ### en passant
            if 'targetPawn' in check[1]:
                return ['en passant', check[1]['targetPawn'], check[1]['targetSquare']]

            ### promotion
            elif (self.direction == 'pos' and y == 8) or (self.direction == 'neg' and y == 1) and (x, y) in check[0]:
                return ['promotion']

            ### normal move
            elif (x, y) in check[0]:
                return True

        else:
            ### normal move
            if (x, y) in self.getAvailableMoves(board, lastMove):
                return True

        return False

    def getData(self, board, lastMove):
        return ({
            'color': self.color,
            'name': self.name,
            'x': self.pos[0],
            'y': self.pos[1],
            'availableMoves': self.getAvailableMoves(board, lastMove)
        })

    def getTargets(self, board):
        moves = []

        ## gets all available moves for taking diagonally
        diagonals = [(-1, 1), (1, 1)] if self.direction == 'pos' else [(-1, -1), (1, -1)]
        for item in diagonals:
            tmpX = item[0] + self.pos[0]
            tmpY = item[1] + self.pos[1]

            if self.withinBounds(tmpX, tmpY) and not targetHasSameColor(self.color, tmpX, tmpY, board):

                if b := board[ (tmpX, tmpY) ]:
                    if b.color != self.color:
                        moves.append((tmpX, tmpY))

        return moves