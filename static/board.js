

// setup game constants
var chars = {
    1: 'a',
    2: 'b',
    3: 'c',
    4: 'd',
    5: 'e',
    6: 'f',
    7: 'g',
    8: 'h'
}
var pieces = {
    'pawn': '<i class="fas fa-chess-pawn fa-3x"></i>',
    'rook' : '<i class="fas fa-chess-rook fa-3x"></i>',
    'knight' : '<i class="fas fa-chess-knight fa-3x"></i>',
    'bishop' : '<i class="fas fa-chess-bishop fa-3x"></i>',
    'queen' : '<i class="fas fa-chess-queen fa-3x"></i>',
    'king' : '<i class="fas fa-chess-king fa-3x"></i>'
}

var def = { // default sizes
    'boardWidth': 480, // board width and height must be equal
    'paddingWidth': ( (parseInt($('.game-wrapper').css('padding')) * 2) + (parseInt($('.board-wrapper').css('padding')) * 2)  + (parseInt($('.info-cont').css('margin-left'))) ), 
    'maxPieceWidth': 60,
    'infoContWidth': $('.info-cont').width()
}
def.gameWidth = def.boardWidth + def.paddingWidth + def.infoContWidth;


/*
 create game board and squares
*/
function makeBoard() {
    var tmp = -1
    for (x=7;x>-1; x--) { // make the board squares
        for (y=0;y<8; y++) {
            if (tmp == -1) {
                $('.board').append($(`<div id='${y+1}-${x+1}' x='${y+1}' y='${x+1}' class="square ${ ((y+1)%2) ? 'light' : 'dark'}"><div class='pos'>${chars[y+1]}${x+1}</div> <div class='indicator'></div> </div>`))
                
            }
            else {
                $('.board').append($(`<div id='${y+1}-${x+1}' x='${y+1}' y='${x+1}' class="square ${ (y%2) ? 'light' : 'dark'}"><div class='pos'>${chars[y+1]}${x+1}</div> <div class='indicator'></div> </div>`))
            }
        }
        tmp = tmp*-1;
        
    }
    gameSize(); // set game size on page load
}
makeBoard(); // create board

// flip board for black player
function reverse() {
    ul = $('.board'); // your parent ul element
    ul.children().each(function(i,li){ul.prepend(li)})
}



// set game size to fit screen
function gameSize() {
    var sW = window.innerWidth;
    var sH = window.innerHeight;

    var extraW = (sW - def.gameWidth) - def.paddingWidth;
    var extraH = (sH - def.boardWidth) - (def.paddingWidth-15) - 140;

    var adjust;

    // if there is extra width space on screen
    if (extraW > 0 && extraH > 0) { // desktop version

        $('body').removeClass('mobile');
        $('.info-cont').detach().appendTo('.game-wrapper');
        $('.info-bottom').detach().appendTo('.info-cont');
        
        adjust = Math.min(extraW, extraH) + def.boardWidth; // get the smaller of the two var 

        // set board width and height
        $('.board').css({
            'width': adjust,
            'height': adjust
        })

        // set info cont height 
        $('.info-cont').css('height', (adjust + 60 + 100));
    }
    else { // switch to mobile version

        $('body').addClass('mobile');
        $('.info-cont').detach().prependTo('.game-wrapper');
        $('.info-bottom').detach().appendTo('.game-wrapper');
        
        var newW = sW;
        var newH = sH - (100 + 165 + 70);

        adjust = Math.min(newW, newH);

        $('.board').css({
            'width': adjust,
            'height': adjust
        })
    }

    // set max piece width (when dragging piece the piece needs a max size when its position absolute and has no parent)
    def.maxPieceWidth = adjust/8;
}

// on screen resize, wait till stop resizing for 200ms then call board resize func
var resizeEnd;
window.onresize = function(){
    clearTimeout(resizeEnd);
    resizeEnd = setTimeout(gameSize, 200);
};





// ------------------------------------- board interactions