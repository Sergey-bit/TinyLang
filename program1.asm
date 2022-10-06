format PE Console
entry start

section '.data' data writeable readable
    
    form  db "%d", 0

section '.code' code readable executable

start:
    push 10
    push 20
    call [fib]

    push eax
    push form
    call [printf]
    push 0
    call [printf]

fib:
    pop ebx
    pop edx
    
    cmp ebx, edx
    jbe @f

    mov eax, ebx
    jmp mk1

    @f:
        mov eax, edx

    .mk1:
        ret


section '.idata' import data readable
    library kernel, 'kernel32.dll', \
            msvcrt, 'msvcrt.dll'

    import kernel, \
            exit, 'ExitProcess'

    import msvcrt, \
            printf, 'printf', \
            scanf, 'scanf', \
            getch, '_getch'