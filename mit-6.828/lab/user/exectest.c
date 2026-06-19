#include <inc/lib.h>

void
umain(int argc, char **argv)
{
	envid_t me = sys_getenvid();

	cprintf("exectest: before exec envid=%08x\n", me);
	execl("/hello", "hello", 0);
	panic("exec returned");
}
