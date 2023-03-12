set complete=

let g:max_buffer_size = 5000000 " 5mb

let s:words = {}

let wid = str2nr(matchstr(reltimestr(reltime()), '\v\.@<=\d+')[1:])

let s:chopt = { 'noblock': 1 }

let s:channel = ch_open("localhost:8765", s:chopt)

let cwd = getcwd()

function! AddBuffer(list, value) abort
    let matching = filter(copy(a:list), 'v:val == a:value')
    if empty(matching)
        call add(a:list, a:value)
    endif
    return a:list
endfunction

function! Buffers() abort
    let buffers = []
    for buf in getbufinfo()
        if empty(win_findbuf(buf.bufnr)) && filereadable(buf.name)
            call AddBuffer(buffers, buf.name)
        endif
    endfor
    return buffers
endfunction

function! WarnMsg(msg)
    echohl WarningMsg | echomsg a:msg | echohl None
endfunction

function! SendFileList()
    if ch_status(s:channel) != 'open'
        return WarnMsg('No connection with completion server')
    endif

    let buffers = Buffers()
    call ch_sendexpr(s:channel, json_encode({ 'cwd': g:cwd, 'wid': g:wid, 'filelist': buffers }))
endfunction

function! Leaving()
    if ch_status(s:channel) != 'open'
        return
    endif

    call ch_sendexpr(s:channel, json_encode({ 'cwd': g:cwd, 'wid': g:wid, 'closing': v:true }))
endfunction

function s:Init()
    call SendFileList()

    au BufReadPost * call SendFileList()
    au FileReadPost * call SendFileList()
    au BufDelete * call SendFileList()

    au VimLeavePre * call Leaving()
endfunction
call s:Init()
" Single file loaded with `vim file.ext` will not be scanned if this call is
" kept in s:Init()
au BufWinEnter * call s:refresh_keywords()

function HandleSuggestions(typing, name, ctx, startcol, channel, msg)
    call easycomplete#complete(a:name, a:ctx, a:startcol, a:msg)
endfunc

function! s:CompleteHandler(typing, name, ctx, startcol)
    call s:refresh_keyword_incremental(getline('.'))

    let tagcompletions = getcompletion(a:typing, 'tag')

    let l:HandleSugg = funcref('HandleSuggestions', [a:typing, a:name, a:ctx, a:startcol])

    call ch_sendexpr(s:channel, json_encode({ 'cwd': g:cwd, 'wid': g:wid, 'target': a:typing, 'tagcompletions': tagcompletions, 'bufferkeywords': keys(s:words) }), { 'callback': l:HandleSugg })
endfunction

function! Completor(opt, ctx)
    if a:ctx['typing'] !~ '\k'
        return v:true
    endif

    call easycomplete#util#AsyncRun(function('s:CompleteHandler'), [a:ctx['typing'], a:opt['name'], a:ctx, a:ctx['startcol']], 1)

    return v:true
endfunction

function! s:should_ignore() abort
    if g:max_buffer_size != -1
        let l:buffer_size = line2byte(line('$') + 1)
        if l:buffer_size > g:max_buffer_size
            echo 'Ignoring buffer autocomplete due to large size ' .. expand('%:p') .. l:buffer_size
            return 1
        endif
    endif

    return 0
endfunction

function! s:refresh_keywords(buffer_clear_cache = 0) abort
    if a:buffer_clear_cache
        let s:words = {}
    endif

    let l:text = join(getline(1, '$'), "\n")
    for l:word in split(l:text, '\W\+')
        if len(l:word) > 1
            let s:words[l:word] = 1
        endif
    endfor
endfunction

function! s:refresh_keyword_incremental(typed) abort
    let l:words = split(a:typed, '\W\+')

    for l:word in l:words[:-2]
        if len(l:word) > 1
            let s:words[l:word] = 1
        endif
    endfor
endfunction

call easycomplete#RegisterSource({
    \ 'name':        'completion-buzz',
    \ 'whitelist':   ['*'],
    \ 'completor':   'Completor',
    \ })
