// Same as pingpongs.c but verifies sfork shared memory for `val`.

#include <inc/lib.h>

uint32_t val;

void
umain(int argc, char **argv)
{
	envid_t who;
	uint32_t i;

	i = 0;
	if ((who = sfork()) != 0) {
		cprintf("parent %08x; thisenv->env_id=%08x\n",
			sys_getenvid(), thisenv->env_id);
		ipc_send(who, 0, 0, 0);
	}

	while (1) {
		ipc_recv(&who, 0, 0);
		cprintf("%08x got %d from %08x (thisenv %08x)\n",
			sys_getenvid(), val, who, thisenv->env_id);
		if (val == 10)
			return;
		++val;
		ipc_send(who, 0, 0, 0);
		if (val == 10)
			return;
	}
}
