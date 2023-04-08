let g:buzz_connection_delay = 1000

let s:wid = str2nr(matchstr(reltimestr(reltime()), '\v\.@<=\d+')[1:])

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
endfunction

func! s:OnBuzzing(...)
    let s:channel = ch_open('localhost:8765', s:chopt)
    if ch_status(s:channel) != 'open'
        return s:WarnMsg(s:msg_conn_failed)
    endif

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

    let s:chopt = { 'noblock': 1 }
    let s:channel = ch_open('localhost:8765', s:chopt)
    if ch_status(s:channel) != 'open'
        call system('python3 ' . expand('<sfile>:p:h') . '/server.py' . ' &')
        return timer_start(g:buzz_connection_delay, function('s:OnBuzzing'))
    endif

    call s:AfterInit()
endfunction
au VimEnter * call s:Init()

function! HandleSuggestions(name, ctx, startcol, channel, msg)
    call asyncomplete#complete(a:name, a:ctx, a:startcol, a:msg)
endfunc

function! s:CompleteHandler(opt, ctx)
    let l:startcol = searchpos('\k*\%#', 'bn', line('.'))[1]

    " let l:typed = matchstr(getline('.'), '\%' . l:startcol . 'c\k\+')
    let l:typed = getline('.')[l:startcol - 1 : col('.') - 2]

    let l:bufferkeywords = []
    call CompleteHelper#FindMatches(l:bufferkeywords, '\<' . l:typed . '\k\+', {'complete': '.'})

    let l:HandleSugg = funcref('HandleSuggestions', [a:opt['name'], a:ctx, l:startcol])

    let l:tagcompletions = []
    try
        let l:tagcompletions = getcompletion(l:typed, 'tag')
    catch
        " For non project files, vim-gutentags does not generate tagsfile. Error
        " is thrown if no tagsfile is found.
    endtry

    call ch_sendexpr(s:channel, json_encode({ 'wid': s:wid, 'target': l:typed, 'tagcompletions': l:tagcompletions, 'bufferkeywords': l:bufferkeywords }), { 'callback': l:HandleSugg })
    " call asyncomplete#complete(a:opt['name'], a:ctx, l:startcol, l:bufferkeywords)
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