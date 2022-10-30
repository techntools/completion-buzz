function Handle(channel, msg)
    echo 'Received: ' .. a:msg[1]
endfunc

let channel = ch_open("localhost:8765")

let cwd = getcwd()

function! AddBuffer(list, value) abort
    let matching = filter(copy(a:list), 'v:val == a:value')
    if empty(matching)
        call add(a:list, a:value)
    endif
    return a:list
endfunction

function! Buffers()
    let buffers = []
    for buf in getbufinfo()
        if empty(win_findbuf(buf.bufnr)) && filereadable(buf.name)
            call AddBuffer(buffers, buf.name)
        endif
    endfor
    return buffers
endfunction

function! SendFileList()
    let buffers = Buffers()
    call ch_sendexpr(g:channel, json_encode({ 'cwd': g:cwd, 'filelist': buffers }), { 'callback': 'Handle' })
endfunction

function! SendModifiedBuffer()
    let buffers = Buffers()
    call ch_sendexpr(g:channel, json_encode({ 'cwd': g:cwd, 'filelist': buffers }), { 'callback': 'Handle' })
endfunction

au BufReadPost * call SendFileList()
au FileReadPost * call SendFileList()
au BufDelete * call SendFileList()

function! FindMatches()
    echo ch_sendexpr(g:channel, json_encode({ 'target': 'miner' }), { 'callback': 'Handle' })
endfunction

call SendFileList()

function HandleSuggestions(name, ctx, startcol, channel, msg)
    let suggestions = []

    for w in a:msg
        call add(suggestions, { 'word': w, 'menu': '[CB]' })
    endfor

    call easycomplete#complete(a:name, a:ctx, a:startcol, suggestions)
endfunc

function! s:CompleteHandler(typing, name, ctx, startcol)
    let l:HandleSugg = funcref('HandleSuggestions', [a:name, a:ctx, a:startcol])

    call ch_sendexpr(g:channel, json_encode({ 'target': a:typing }), { 'callback': l:HandleSugg })
endfunction

function! Completor(opt, ctx)
    call easycomplete#util#AsyncRun(function('s:CompleteHandler'), [a:ctx['typing'], a:opt['name'], a:ctx, a:ctx['startcol']], 1)
    return v:true
endfunction

call easycomplete#RegisterSource({
    \ 'name':        'mine',
    \ 'whitelist':   ['*'],
    \ 'completor':   'Completor',
    \  })

au CmdwinEnter * EasyCompleteDisable
au CmdwinLeave * EasyCompleteEnable

" When/How to update the file list ?
"
" When/How to signal to update the word list ? That file has changed ?
" Not need to think about this with vim-easycomplete plugin.
