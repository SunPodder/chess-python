
function setProfile(code, target, name, color) {
    var html = `<i style='color: ${color}; margin: 0 6px;' class="fas fa-crown fa-lg"></i> <div class='profile-name'>${name}</div><img src="https://ipdata.co/flags/${code.toLowerCase()}.png">`;

    target.html( $(html) );
}


// setup socketio
var socket = io();

var state = 0; // game state - 0: waiting room, 1: game started, -1: game over
var yourTurn = false;
var color;
var availableMoves;
var anim = true;


// if gameid not in session storage, set it
if (!sessionStorage.getItem(gameId)) {
    sessionStorage.setItem(gameId, userId)
}


// clears all keys in session storage except for the current gameId key
function clearKeysExcept(currKey) {
    var keys = Object.keys(sessionStorage).filter( key => {
        return key !== currKey
    })

    for (i=0; i<keys.length; i++) {
        sessionStorage.removeItem(keys[i]);
    }
}
clearKeysExcept(gameId);


// on socketio connect, join game room
socket.on('connect', function() {

    // get name
    var name = ( ( Object.keys(localStorage).includes('name') ) ? localStorage.getItem('name') : '' );
    while (name.length <= 0 || name.length > 30) {
        name = prompt('Enter your name:\n(name length must be between 1 and 30 characters)');
    }
    localStorage.setItem('name', name);

    var data = {
        'room': gameId,
        'username': userId,
        'name': name,
        'countryCode': countryCode || 'UK'
    }
    if (Object.keys(localStorage).includes('userpass')) {
        data['userpass'] = localStorage.getItem('userpass');
    }

    socket.emit('join', data, res => {
        if (res.status) { // joined game
            $('.page').show();

            if ( !(Object.keys(localStorage).includes('userpass')) ) {
                localStorage.setItem('userpass', res.userpass)
            }
        }
        else { // not joined game

            // go to home page
            location.pathname = '/';
        }
    });
});


// get current game state - (this will run on game start and whenever page refreshed and need to position all pieces on board)
socket.on('game_state', res => { // set up board
    
    // if game in waiting room (or on refresh set up game then set state back to running)
    // if game in gameover state
    if (state === -1) {
        $('.gameover').show();

        $('#state').hide();
    }
    else if (state === 0) {
        color = res[userId].team;
        
        if (res[userId].team === 'black') {
            reverse();
        }

        setPieces(res.board);

        if (res.lastMove) {
            s = res.lastMove.startPos;
            n = res.lastMove.newPos;

            $(`#${n[0]}-${n[1]}`).addClass('last-move');
            $(`#${s[0]}-${s[1]}`).addClass('last-move');
        }
        

        // --------- set profiles
        // set enemy profile
        var enemyId = res.players.filter( i => {
            return i !== userId;
        })[0]
        setProfile(res[enemyId].countryCode, $('.enemy-profile'), res[enemyId].name, res[enemyId].team);
        // set user profile
        setProfile(countryCode, $('.your-profile'), res[userId].name, res[userId].team);

        // game start sound 
        sound.start.play();
        
        $('.info-bottom').show();

        state = 1;
    }
    

    $('#state').text(`${res[res.turn].team} to move.`);

    //console.log(res)

    yourTurn = (res[userId].team === res[res.turn].team);
    if (yourTurn) {
        $('.board').removeClass('off');
    }
    else {
        $('.board').addClass('off');
    }

    availableMoves = {};
    for (i in res.board) {
        var item = res.board[i];
        availableMoves[`${item.x}-${item.y}`] = item.availableMoves;
    }

    updateMovesList(res.movesList);
})


// set/updates moves list 
function updateMovesList(moves) {
    var html = '';
    for (i in moves) {
        html += `<div class='note'><div class='note-cnt'>${i}.</div>`;
        for (n=0; n<moves[i].length; n++) {
            html += `<div class='note-move'>${moves[i][n]}</div>`;
        }
        html += '</div>'
    }

    $('.info-mid').html(html);
    $(".info-mid").scrollTop($(".info-mid")[0].scrollHeight);
}

// copy url to clipboard
function copy() {
    navigator.clipboard.writeText(window.location.href);
}


// set pieces to their pos on board
function setPieces(b) {
    for (i=0; i<b.length; i++) {
        var ele = $(`#${b[i].x}-${b[i].y}`);
        ele.html(`<div class='pos'>${chars[b[i].x]}${b[i].y}</div> <div x='${b[i].x}' y='${b[i].y}' name='${b[i].name}' class='piece ${b[i].color} ${( b[i].color === color ) ? '' : 'enemy'}'>${pieces[ b[i].name ]}</div> <div class='indicator'></div>`);

        dragElement(ele.find('.piece')[0]);
    }
}


// removes class show move from all squares with it
function removeShowMoves() {
    $('.show-move').each( i => {
        $('.show-move')[0].classList.remove('show-move');
    })
}

/*
 piece onclick handling
*/
$('.board').on('click', (e) => {
    var ele = $(e.target);
    if ($('.selected').length === 0) {
        if (state === -1) { // if gameover dont allow
            return;
        }
        
        if (ele.hasClass('fas')) {
            ele = ele.parents('.piece');
            ele = $(ele);
        }
        if (ele.hasClass('piece') ) {
            ele.addClass('selected');
            
            removeShowMoves();

            for (i in availableMoves[`${ele.attr('x')}-${ele.attr('y')}`]) {
                var pos = availableMoves[`${ele.attr('x')}-${ele.attr('y')}`][i];
                $(`#${pos[0]}-${pos[1]}`).addClass('show-move');
            }
        }
    }
    else {
        if (state === -1) { // if gameover dont allow
            return;
        }

        if ($('.board').hasClass('off')) { // dont allow when board is disabled
            return;
        }

        if (!ele.hasClass('square')) {
            ele = ele.parents('.square');
        }

        if (ele) {
            $(ele).addClass('target');
        }
        
        move();
    }
})

/*
 send a move to the server
*/
function move() {
    //console.log('MOVE')
    var a = $('.selected');
    var b = $('.target');

    // target is not in available moves 
    if (!(b.find('.indicator').is(':visible'))) {
        //console.log('no indicator on target')
        a.removeClass('selected');
        b.removeClass('target');

        a.show();
        anim = true;
        
        removeShowMoves();

        // if there is a piece on the square that is not an enemy piece, then select it
        if (b.find('.enemy').length === 0 && b.find('.piece').length === 1) {
            // select the new piece
            var ele = b.find('.piece');
            ele.addClass('selected');

            for (i in availableMoves[`${ele.attr('x')}-${ele.attr('y')}`]) {
                var pos = availableMoves[`${ele.attr('x')}-${ele.attr('y')}`][i];
                $(`#${pos[0]}-${pos[1]}`).addClass('show-move');
            }
        }
        return;
    }

    removeShowMoves();

    /// if pawn promotion
    if (a.attr('name') === 'pawn' && (b.attr('y') === '8' || b.attr('y') === '1')) {

        var offset = b.offset();
        var html = `
        <div class='promote-choose flex-stack' style='color: ${color}; left: ${offset.left}; top: ${offset.top};'>
            <div class='choice' style='width: ${$('.square').width()}px; height: ${$('.square').width()}px;' onclick='choose("queen");'><i class="fas fa-chess-queen fa-3x"></i></div>
            <div class='choice' style='width: ${$('.square').width()}px; height: ${$('.square').width()}px;' onclick='choose("knight");'><i class="fas fa-chess-knight fa-3x"></i></div>
            <div class='choice' style='width: ${$('.square').width()}px; height: ${$('.square').width()}px;' onclick='choose("bishop");'><i class="fas fa-chess-bishop fa-3x"></i></div>
            <div class='choice' style='width: ${$('.square').width()}px; height: ${$('.square').width()}px;' onclick='choose("rook");'><i class="fas fa-chess-rook fa-3x"></i></div>

            <div class='choice close' style='width: ${$('.square').width()}px;' onclick='choose("close");'><i class="fas fa-times fa-2x"></i></div>
        </div>
        `;

        $('.board').addClass('off');

        $('body').append($(html))
    }
    else {
        socket.emit('move', {'room': gameId, 'username': userId, 'userpass': localStorage.getItem('userpass'), 'piece': [a.attr('x'), a.attr('y')], 'target': [b.attr('x'), b.attr('y')]}, res => {        
            a.removeClass('selected');
            b.removeClass('target');

            if (!res) {
                // invalid move so make the target color red or something to show user their move was invalid
                b.addClass('bad-move');
                setTimeout( () => {
                    b.removeClass('bad-move');
                }, 400)

                a.show();
                anim = true;
            }
            
        })
    }
}


/*
 choice for pawn promotion
*/
function choose(c) {
    var a = $('.selected');
    var b = $('.target');

    $('.promote-choose').remove();

    $('.board').removeClass('off');

    if (c === 'close') {
        a.removeClass('selected');
        b.removeClass('target');

        a.show();
        anim = true;
    }
    else {
        socket.emit('move', {'room': gameId, 'username': userId, 'userpass': localStorage.getItem('userpass'), 'piece': [a.attr('x'), a.attr('y')], 'target': [b.attr('x'), b.attr('y')], 'promote': c}, res => {        
            a.removeClass('selected');
            b.removeClass('target');

            if (!res) {
                // invalid move so make the target color red or something to show user their move was invalid
                b.addClass('bad-move');
                setTimeout( () => {
                    b.removeClass('bad-move');
                }, 400)

                a.show();
                anim = true;
            }
            
        })
    }
}


/*
 animate piece move to target square
*/
function moveAnimate(oldParent, element, newParent, normalMove=true, promotion=false) {
    //console.log(promotion, promotion!==false)

    removeShowMoves();

    // Allow passing in either a jQuery object or selector
    element = $(element);
    newParent= $(newParent);
    
    // sound
    if (newParent.find('.piece').length === 0) { // move to square sound
        sound.move.play();
    }
    else {
        sound.capture.play(); // capture piece sound
    }

    $('.last-move').each( i => {
        $('.last-move')[0].classList.remove('last-move');
    })

    if ($(newParent).find('.piece').length > 0) {
        $(newParent).find('.piece').remove();
    }

    var oldOffset = element.offset();
    element.appendTo(newParent);
    var newOffset = element.offset();

    var temp = element.clone().appendTo('body');
    temp.css({
        'position': 'absolute',
        'left': oldOffset.left,
        'top': oldOffset.top,
        'z-index': 1000,
        'max-width': def.maxPieceWidth,
        'max-height': def.maxPieceWidth
    });
    
    var speed = (anim ? 250 : 0);

    $(element).hide();
    temp.animate({'top': newOffset.top, 'left': newOffset.left}, speed, function(){

        $(element).detach().appendTo(newParent);
        $(element).show();

        if (normalMove) {
            $(oldParent).addClass('last-move');
            $(newParent).addClass('last-move');
        }

        temp.remove();

        anim = true;

        // pawn promotion 
        if (promotion !== false) {
            //console.log(promotion)

            $(element).attr('name', promotion);
            $(element).find('i').remove();
            $(element).append(pieces[promotion]);
        }
    });
}
/*
 move piece from server signal
*/
socket.on('move_piece', res => {
    var p = res.oldPos;
    var n = res.newPos
    var ele = $(`#${p[0]}-${p[1]}`).find('.piece');

    // set piece coordinate attributes
    $(ele).attr('x', n[0]);
    $(ele).attr('y', n[1]);

    // put piece into new square
    //$(ele).detach().appendTo(`#${n[0]}-${n[1]}`);
    if ('promotion' in res) {
        moveAnimate(document.getElementById(`${p[0]}-${p[1]}`), ele, document.getElementById(`${n[0]}-${n[1]}`), normalMove=true, promotion=res.promotion)
    }
    else {
        moveAnimate(document.getElementById(`${p[0]}-${p[1]}`), ele, document.getElementById(`${n[0]}-${n[1]}`))
    }

    // un-highlight piece and target
    var a = $('.selected');
    var b = $('.target');
    a.removeClass('selected');
    b.removeClass('target');

    $('#state').text(`${res[res.turn].team} to move.`);

    yourTurn = (res[userId].team === res[res.turn].team);

    if (yourTurn) {
        $('.board').removeClass('off');
    }
    else {
        $('.board').addClass('off');
    }
})


// remove pawn victim on en passant
socket.on('en_passant', res => {
    var pos = res.targetPawn;
    $(`#${pos[0]}-${pos[1]}`).find('.piece').remove();
})

// move rook on castles
socket.on('castles', res => {
    var p = res.rookPos;
    var n = res.targetPos;

    var ele = $(`#${p[0]}-${p[1]}`).find('.piece');

    // set piece coordinate attributes
    $(ele).attr('x', n[0]);
    $(ele).attr('y', n[1]);

    // put piece into new square
    //$(ele).detach().appendTo(`#${n[0]}-${n[1]}`);
    moveAnimate(document.getElementById(`${p[0]}-${p[1]}`), ele, document.getElementById(`${n[0]}-${n[1]}`), normalMove=false)
})

/*
 ---------------------------- drag pieces
*/

function dragElement(elmnt) {
    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    var cln;
    elmnt.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        if (state === -1) { // if gameover dont allow
            return;
        }

        e = e || window.event;
        e.preventDefault();
        // get the mouse cursor position at startup:
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        // call a function whenever the cursor moves:
        document.onmousemove = elementDrag;

        $('body').css('cursor', 'grabbing');

        // remove selected thingies
        var a = $('.selected');
        var b = $('.target');
        a.removeClass('selected');
        b.removeClass('target');

        // show available moves
        var ele = $(elmnt);

        var oldOffset = ele.offset();
        cln = ele.clone().appendTo(ele.parents('.square'));

        cln.hide();

        ele.detach().appendTo('body');
        ele.css({
            'id': 'dragging-piece',
            'position': 'absolute',
            'left': oldOffset.left,
            'top': oldOffset.top,
            'z-index': 1000,
            'pointer-events': 'none',
            'max-width': def.maxPieceWidth,
            'max-height': def.maxPieceWidth
        });

        removeShowMoves();
        for (i in availableMoves[`${ele.attr('x')}-${ele.attr('y')}`]) {
            var pos = availableMoves[`${ele.attr('x')}-${ele.attr('y')}`][i];
            $(`#${pos[0]}-${pos[1]}`).addClass('show-move');
        }
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();

        // calculate the new cursor position:
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;

        // set the element's new position:
        elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
        elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
    }

    function closeDragElement() {
        // stop moving when mouse button is released:

        $('body').css('cursor', '');

        $(elmnt).remove();
        
        var target = $('.square:hover');

        if (target.length === 0) {
            cln.show();
            dragElement(cln[0]);
        }
        else {
            var currSquare = cln.parents('.square');

            if (currSquare.attr('id') === target.attr('id')) { // target is same square as starting
                cln.show();
                dragElement(cln[0]);

                cln.addClass('selected');

                for (i in availableMoves[`${cln.attr('x')}-${cln.attr('y')}`]) {
                    var pos = availableMoves[`${cln.attr('x')}-${cln.attr('y')}`][i];
                    $(`#${pos[0]}-${pos[1]}`).addClass('show-move');
                }
                
            }
            else {
                cln.addClass('selected');
                dragElement(cln[0]);
                target.addClass('target');
                anim = false;
                move();
            }
        }

        document.onmouseup = null;
        document.onmousemove = null;
    }
}



// emote click 
function emote(ele) {
    var msg = ele.classList.value.split(' ')[1];
    message(msg);
}
// phrase click
function msg(ele) {
    var msg = ele.innerText;
    message(msg);
}

// send message 
function message(msg) {
    socket.emit('message', {'username': userId, 'userpass': localStorage.getItem('userpass'), 'room': gameId, 'message': msg}, (res) => {
        //console.log(res)
    })
}

var msgs = ['thumbs', 'angry', 'crying', 'laughing'];
// do emote animation
socket.on('emote', (res) => {
    var target = (res.from === userId ? '.your-profile' : '.enemy-profile' );

    if ($(target).find('.message').length > 0) {
        $(target).find('.message').hide();
    }
    if (msgs.includes(res.message)) { // emote
        var cln = $(`.${res.message}`).html();
        $(target).append(`<div class="message emote">${cln}</div>`);
    }
    else { // phrase
        $(target).append(`<div class="message phrase">${res.message}</div>`);
    }
})

$('body').on('DOMNodeInserted', '.message', function () {
    setTimeout( () => {
        $(this).remove();
    }, 2000)
});



/*
 on game over
*/
socket.on('game_over', (res) => {
    //console.log('GAME OVER', res)

    state = -1;

    $('.won').text(res.gameEndType);
    $('.by').text(res.by);
    $('.rematch-count').text(`${res.ready}/2`);

    $('.gameover').show();
    $('.gameover').addClass('animateBounceIn');
    setTimeout( () => {
        $('.gameover').removeClass('animateBounceIn');

    }, 500)
})

/*
 on player ready up, set players ready display 
*/
socket.on('user_ready', res => {
    //console.log(res)

    $('.rematch-count').text(`${res.ready}/2`);

    if (res.ready === 2) {
        //console.log('rematch accepted')
        location.reload();
    }
})

// user ready up function
function readyUp() {
    $('.rematch').attr("disabled", true);
    socket.emit('rematch', {'room': gameId, 'username': userId, 'userpass': localStorage.getItem('userpass')}, res => {
        //console.log('ready up res: ', res)

    })
}