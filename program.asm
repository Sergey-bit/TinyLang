format PE Console
entry start

include 'FASM\INCLUDE\win32a.inc'


section '.data' data readable writeable
	__str__0 db  '%d %d', 0
	__str__1 db  '%d + %d = %d', 10, 0
	__str__2 db  '%dth fibonacci number is %d', 10, 0
	__str__3 db  '%dth fibonacci number is %d', 10, 0
	__str__4 db  '%d mod %d = %d', 10, 0
	__str__5 db  's / k = %d.%d', 10, 0
	__str__6 db  's / k = %d.%d', 10, 0
	__str__7 db  's * k = %d', 10, 0
	__str__8 db  'Press any key...', 10, 0
	__str__9 db  'a: %d, b: %d, f: %d, counter: %d', 10, 0
	__str__10 db  '%d', 10, 0
	__str__11 db  'between %d and %d: %d', 10, 0
	ghdsfetbglg dd ?
	s dd ?
	k dd ?
	float_part1 dd ?
	float_part2 dd ?
section '.code' code readable executable
	start:
		invoke scanf , __str__0, s, k
		sub esp, 0xc
		push ecx
		push eax
		push edx
		mov eax, dword [s]
		cdq
		div dword [k]
		mov ecx, edx
		pop edx
		pop eax
		push edx
		push ecx
		push edx
		ccall tf, ecx, dword [k]
		sub esp, 0x8
		pop edx
		pop ecx
		mov edx, eax
		mov dword [float_part1], edx
		pop edx
		push ebx
		push eax
		push edx
		mov eax, dword [s]
		cdq
		div dword [k]
		mov ebx, edx
		pop edx
		pop eax
		push edx
		push ebx
		push edx
		ccall to_float, ebx, dword [k]
		pop edx
		pop ebx
		mov edx, eax
		mov dword [float_part2], edx
		pop edx
		push edx
		push edx
		ccall fib, dword [s]
		pop edx
		mov edx, eax
		push ebx
		push ebx
		push edx
		ccall union, edx, dword [k], max
		pop edx
		pop ebx
		mov ebx, eax
		pop ebx
		push ebx
		push ebx
		ccall fib, dword [k]
		pop ebx
		mov ebx, eax
		push ecx
		push ecx
		push ebx
		ccall union, dword [s], ebx, min
		pop ebx
		pop ecx
		mov ecx, eax
		pop ecx
		push ecx
		mov ecx, dword [s]
		add ecx, dword [k]
		push ecx
		invoke printf, __str__1, dword [s], dword [k], ecx
		sub esp, 0x10
		pop ecx
		pop ecx
		push ebx
		push ebx
		ccall fib, dword [s]
		pop ebx
		mov ebx, eax
		push ebx
		invoke printf, __str__2, dword [s], ebx
		sub esp, 0xc
		pop ebx
		pop ebx
		push edx
		push edx
		ccall fib, dword [k]
		pop edx
		mov edx, eax
		push edx
		invoke printf, __str__3, dword [k], edx
		sub esp, 0xc
		pop edx
		pop edx
		push edx
		push eax
		mov eax, dword [s]
		cdq
		div dword [k]
		pop eax
		push edx
		invoke printf, __str__4, dword [s], dword [k], edx
		sub esp, 0x10
		pop edx
		pop edx
		push edx
		push eax
		mov eax, dword [s]
		cdq
		idiv dword [k]
		mov edx, eax
		pop eax
		push edx
		invoke printf, __str__5, edx, dword [float_part1]
		sub esp, 0xc
		pop edx
		pop edx
		push ebx
		push eax
		push edx
		mov eax, dword [s]
		cdq
		idiv dword [k]
		mov ebx, eax
		pop edx
		pop eax
		push ebx
		invoke printf, __str__6, ebx, dword [float_part2]
		sub esp, 0xc
		pop ebx
		pop ebx
		push ecx
		push edx
		push eax
		mov eax, 5
		imul dword [k]
		mov ecx, eax
		pop eax
		pop edx
		push ecx
		invoke printf, __str__7, ecx
		sub esp, 0x8
		pop ecx
		pop ecx
		invoke printf, __str__8
		sub esp, 0x4
		invoke exit, 0
	proc fib c, n
			push edx
			mov edx, dword [n]
			cmp edx, 0
			je @f
			xor edx, edx
			jmp .after12
		@@:
			mov edx, -1
		.after12:
			push ecx
			mov ecx, dword [n]
			cmp ecx, 1
			je @f
			xor ecx, ecx
			jmp .after13
		@@:
			mov ecx, -1
		.after13:
			push ebx
			or ecx, edx
			mov ebx, ecx
			cmp ebx, 0
			pop ebx
			je .if14
			mov eax, 1
			jmp .return
		.if14:
			push ebx
			mov ebx, -1
			push ecx
			mov ecx, dword [n]
			add ecx, ebx
			push ebx
			push ecx
			push ebx
			ccall fib, ecx
			pop ebx
			pop ecx
			mov ebx, eax
			push edx
			mov edx, -2
			push ecx
			mov ecx, dword [n]
			add ecx, edx
			push edx
			push ecx
			push ebx
			push edx
			ccall fib, ecx
			pop edx
			pop ebx
			pop ecx
			mov edx, eax
			push ecx
			mov ecx, ebx
			add ecx, edx
			mov eax, ecx
			pop ecx
			jmp .return
		.return:
			ret
	endp
	proc max c, a, b
			push edx
			mov edx, dword [a]
			cmp edx, dword [b]
			jge @f
			xor edx, edx
			jmp .after15
		@@:
			mov edx, -1
		.after15:
			cmp edx, 0
			pop edx
			je .if16
			mov eax, dword [a]
			jmp .return
		.if16:
			mov eax, dword [b]
			jmp .return
		.return:
			ret
	endp
	proc min c, a, b
			push ecx
			mov ecx, dword [a]
			cmp ecx, dword [b]
			jle @f
			xor ecx, ecx
			jmp .after17
		@@:
			mov ecx, -1
		.after17:
			cmp ecx, 0
			pop ecx
			je .if18
			mov eax, dword [a]
			jmp .return
		.if18:
			mov eax, dword [b]
			jmp .return
		.return:
			ret
	endp
	proc to_float c, a, b
		locals
			counter dd ?
			f dd ?
		endl
			push ecx
			mov ecx, 0
			mov dword [counter], ecx
			pop ecx
			push ebx
			mov ebx, 0
			mov dword [f], ebx
			pop ebx
		.while19:
			push ecx
			mov ecx, dword [counter]
			cmp ecx, 8
			jl @f
			xor ecx, ecx
			jmp .after20
		@@:
			mov ecx, -1
		.after20:
			cmp ecx, 0
			pop ecx
			je @f
			invoke printf, __str__9, dword [a], dword [b], dword [f], dword [counter]
			sub esp, 0x14
			push edx
			push eax
			mov eax, 10
			imul dword [a]
			mov dword [a], eax
			pop eax
			pop edx
			push ecx
			push edx
			push eax
			mov eax, 10
			imul dword [f]
			mov ecx, eax
			pop eax
			pop edx
			push ebx
			push eax
			push edx
			mov eax, dword [a]
			cdq
			idiv dword [b]
			mov ebx, eax
			pop edx
			pop eax
			push edx
			mov edx, ecx
			add edx, ebx
			mov dword [f], edx
			pop edx
			push eax
			push edx
			mov eax, dword [a]
			cdq
			div dword [b]
			mov dword [a], edx
			pop edx
			pop eax
			push ecx
			mov ecx, 1
			add dword [counter], ecx
			pop ecx
			jmp .while19
		@@:
			invoke printf, __str__10, dword [f]
			sub esp, 0x8
			mov eax, dword [f]
			jmp .return
		.return:
			ret
	endp
	proc union c, s, k, f
			push ecx
			push ecx
			invoke f, dword [k], dword [s]
			pop ecx
			mov ecx, eax
			push ecx
			invoke printf, __str__11, dword [s], dword [k], ecx
			sub esp, 0x10
			pop ecx
			pop ecx
		.return:
			ret
	endp


proc abs c number
    mov eax, dword [number]
    cmp eax, 0
    jl @f
    jmp .return

    @@:
        neg eax
        jmp .return

    .return:
        ret
endp

proc tf c a, b
    locals
        f dd 0
    endl
    mov eax, dword [a]
    cmp eax, 0
    jl .error
    je .one
    mov eax, dword [b]
    cmp eax, 0
    jg .solution

    .error:
        push 1
        call [exit]

    .one:
        mov eax, 0
        mov dword [f], eax
        jmp .return

    .solution:
        push edx
        push ebx

        repeat 9
            xor edx, edx
            mov eax, dword [a]
            mov edx, 10
            mul edx
            mov ebx, eax
            cdq
            div dword [b]
            push edx
            push eax
            mov eax, dword [f]
            mov edx, 10
            mul edx
            pop ebx
            add eax, ebx
            mov dword [f], eax
            pop edx
            mov dword [a], edx
        end repeat
        pop ebx
        pop edx
    .return:
        mov eax, dword [f]
        ret
endp

section '.idata' import data readable
    library kernel, 'kernel32.dll', \
            msvcrt, 'msvcrt.dll'

    import kernel, \
            exit, 'ExitProcess'

    import msvcrt, \
            printf, 'printf', \
            scanf, 'scanf', \
            getch, '_getch'
