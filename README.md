## Installation

Developed and tested with Vim only.

``` vim script
call minpac#add('inkarkat/vim-ingo-library')
call minpac#add('techntools/vim-CompleteHelper')
call minpac#add('techntools/asyncomplete.vim')
call minpac#add('techntools/completion-buzz', { 'branch': 'main' })
```

## My asyncomplete.vim settings

```vim script
let g:asyncomplete_auto_popup = 1
let g:asyncomplete_matchfuzzy = 1
let g:asyncomplete_min_chars = 1
let g:asyncomplete_auto_completeopt = 0
let g:asyncomplete_popup_delay = 0

inoremap <expr> <cr> pumvisible() ? "\<C-y>\<ESC>a" : "\<cr>"

function! s:check_back_space() abort
    let col = col('.') - 1
    return !col || getline('.')[col - 1]  =~ '\s'
endfunction

inoremap <silent><expr> <TAB>
  \ pumvisible() ? "\<C-n>" :
  \ <SID>check_back_space() ? "\<TAB>" :
  \ asyncomplete#force_refresh()

inoremap <expr><S-TAB> pumvisible() ? "\<C-p>" : "\<C-h>"

au CmdwinEnter : let b:asyncomplete_enable = 0
```

If you see some lag in completion, try changing value of ```g:asyncomplete_min_chars``` to more than 1

## How it works

As soon as first instance of Vim is started, server starts and stays alive until you shut down your PC or kill the server process.

Upon VimEnter, it sends file list from ```set complete?``` to completion server where a word pool is created.

Upon every BufLeave, if buffer is modified, its contents are sent to server to refresh word pool. Every modification is passed only once. Same modications are not passed multiple times upon further BufLeave events.

For words matching in current buffer, it scans the current buffer in Vim itself.

Merges matches from current buffer, tags and word pool that server holds.

## My setup with LSP

I am using ```C-X C-O``` omnicompletions with this [yegappan/lsp](https://github.com/yegappan/lsp). This LSP is Vim 9 only.

## About forks
My forks remove code that is not needed for the completion server and to improve performance.

## Credits

I am extremely thankfull to all the code owners. This plugin would not be possible without their work.

## Some RnD 

[Speed up regex replacements](https://stackoverflow.com/questions/42742810/speed-up-millions-of-regex-replacements-in-python-3)

[Fast string comparison in Python](https://stackoverflow.com/questions/49950747/why-is-string-comparison-so-fast-in-python)

[Python performance tuning](https://stackify.com/20-simple-python-performance-tuning-tips/#:~:text=18.%20Don%E2%80%99t%20construct%20a%20set%20for%20a%20conditional.)
