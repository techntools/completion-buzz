let s:wid = str2nr(matchstr(reltimestr(reltime()), '\v\.@<=\d+')[1:])

let s:chopt = { 'noblock': 1 }
let s:channel = ch_open('localhost:8765', s:chopt)

let s:msg_conn_failed = 'Failed to connect with completion server'

function! AddBuffer(list, value) abort
    let l:matching = filter(copy(a:list), 'v:val == a:value')
    if empty(l:matching)
        call add(a:list, a:value)
    endif
    return a:list
endfunction

function! Buffers() abort
    let l:buffers = []
    for buf in getbufinfo()
        if empty(win_findbuf(buf.bufnr)) && filereadable(buf.name)
            call AddBuffer(l:buffers, buf.name)
        endif
    endfor
    return l:buffers
endfunction

function! s:WarnMsg(msg)
    echohl WarningMsg | echom a:msg | echohl None | redraw
endfunction

function! SendFileList()
    if ch_status(s:channel) != 'open'
        return s:WarnMsg(s:msg_conn_failed)
    endif

    call ch_sendexpr(s:channel, json_encode({ 'wid': s:wid, 'filelist': Buffers() }))
endfunction

function! Leaving()
    if ch_status(s:channel) != 'open'
        return
    endif

    call ch_sendexpr(s:channel, json_encode({ 'wid': s:wid, 'closing': v:true }))

    call ch_close(s:channel)
endfunction

func! s:OnBuzzing(tid)
    let s:channel = ch_open('localhost:8765', s:chopt)
    if ch_status(s:channel) != 'open'
        if timer_info(a:tid)[0]['repeat'] == 0
            return s:WarnMsg(s:msg_conn_failed)
        endif

        return
    endif

    call timer_stop(a:tid)

    call s:AfterInit()
endfu

func! s:AfterInit(...)
    call SendFileList()

    au FileReadPost * call SendFileList()
    au BufDelete * call SendFileList()

    au VimLeavePre * call Leaving()
endfun

function! s:Init()
    if !exists('g:asyncomplete_loaded')
        return s:WarnMsg('Please install asyncomplete.vim')
    endif

    if ch_status(s:channel) != 'open'
        call system('python3 ' . expand('<script>:p:h:h') . '/server.py' . ' &')
        return timer_start(1000, function('s:OnBuzzing'), { 'repeat': 3 })
    endif

    call s:AfterInit()
endfunction
au VimEnter * call s:Init()

function! s:FindMatches(pattern)
    let l:matches = []

    let l:save_view = winsaveview()
    let l:cursor = getpos('.')[1:2]

    let l:firstMatchPos = [0,0]
    while ! complete_check()
        let l:matchPos = searchpos(a:pattern, 'w')
        if l:matchPos == [0,0] || l:matchPos == l:firstMatchPos
            " Stop when no matches or wrapped around to first match.
            break
        endif
        if l:firstMatchPos == [0,0]
            " Record first match position to detect wrap-around.
            let l:firstMatchPos = l:matchPos
        endif

        let l:matchEndPos = searchpos(a:pattern, 'cen')
        if l:cursor[0] < l:matchPos[0] || l:cursor[0] > l:matchEndPos[0] || l:cursor[0] == l:matchPos[0] && l:cursor[1] < l:matchPos[1] || l:cursor[0] == l:matchEndPos[0] && l:cursor[1] > l:matchEndPos[1]
            " Do not include a match around the cursor position; this would
            " either just return the completion base, which Vim would not
            " offer anyway, or the completion base and following text, which
            " is unlikely to be desired, and not offered by the built-in
            " completions, neither. By avoiding this match, we may shrink
            " down the completion list to a single match, which would be
            " inserted immediately without the user having to choose one.

            " Extract and collect the match text.
            call add(l:matches, ingo#text#Get(l:matchPos, l:matchEndPos))
        endif
    endwhile

    call winrestview(l:save_view)

    return l:matches
endfunction

function! HandleSuggestions(name, ctx, startcol, channel, msg)
    call asyncomplete#complete(a:name, a:ctx, a:startcol, a:msg)
endfunc

function! s:CompleteHandler(opt, ctx)
    let l:startcol = searchpos('\k*\%#', 'bn', line('.'))[1]

    " let l:typed = matchstr(getline('.'), '\%' . l:startcol . 'c\k\+')
    let l:typed = getline('.')[l:startcol - 1 : col('.') - 2]

    try
        let l:tagcompletions = getcompletion(l:typed, 'tag')
    catch
        " For non project files, vim-gutentags does not generate tagsfile. Error
        " is thrown if no tagsfile is found.
        let l:tagcompletions = []
    endtry

    call ch_sendexpr(s:channel, json_encode({
                \ 'wid': s:wid,
                \ 'target': l:typed,
                \ 'tagcompletions': l:tagcompletions,
                \ 'bufferkeywords': s:FindMatches('\<' . l:typed . '\k\+')
                \ }), { 'callback': funcref('HandleSuggestions', [a:opt['name'], a:ctx, l:startcol]) })
    " call asyncomplete#complete(a:opt['name'], a:ctx, l:startcol, s:FindMatches('\<' . l:typed . '\k\+'))
endfunction

call asyncomplete#register_source({
   \ 'name': 'completion-buzz',
   \ 'allowlist': ['*'],
   \ 'completor': function('s:CompleteHandler'),
   \ })

let s:buf_mod_ticks = {}

func! OnBufLeave()
    let l:bf = expand('%:p')

    if getftime(l:bf) <= -1
        return
    endif

    if ch_status(s:channel) != 'open'
        return s:WarnMsg(s:msg_conn_failed)
    endif

    if has_key(s:buf_mod_ticks, l:bf)
        if s:buf_mod_ticks[l:bf] != b:changedtick
            let s:buf_mod_ticks[l:bf] = b:changedtick
            call ch_sendexpr(s:channel, json_encode({ 'wid': s:wid, 'fileloc': l:bf, 'filelines': getline(1, '$') }))
        endif
    else
        let s:buf_mod_ticks[l:bf] = b:changedtick
        call ch_sendexpr(s:channel, json_encode({ 'wid': s:wid, 'fileloc': l:bf, 'filelines': getline(1, '$') }))
    endif
endfu

au BufLeave * call OnBufLeave()
