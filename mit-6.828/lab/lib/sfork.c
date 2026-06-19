// Challenge: shared-memory fork (stacks remain copy-on-write).

#include <inc/string.h>
#include <inc/lib.h>

extern void _pgfault_upcall(void);

#define PTE_COW		0x800

static void
pgfault(struct UTrapframe *utf)
{
	void *addr = (void *) utf->utf_fault_va;
	uint32_t err = utf->utf_err;
	int r;

	if ((err & FEC_WR) == 0 || (uvpt[PGNUM(addr)] & PTE_COW) == 0)
		panic("pgfault at %p: err %d", addr, err);

	if ((r = sys_page_alloc(0, (void *) PFTEMP, PTE_U | PTE_W | PTE_P)) < 0)
		panic("pgfault: page alloc failed: %e", r);
	memmove(PFTEMP, ROUNDDOWN(addr, PGSIZE), PGSIZE);
	if ((r = sys_page_map(0, (void *) PFTEMP, 0, ROUNDDOWN(addr, PGSIZE),
			      PTE_U | PTE_W | PTE_P)) < 0)
		panic("pgfault: page map failed: %e", r);
	if ((r = sys_page_unmap(0, (void *) PFTEMP)) < 0)
		panic("pgfault: page unmap failed: %e", r);
}

static int
duppage(envid_t envid, unsigned pn)
{
	int r;
	void *addr = (void *) (pn * PGSIZE);
	int perm = uvpt[pn] & PTE_SYSCALL;

	if (uvpt[pn] & PTE_SHARE)
		perm = (uvpt[pn] & PTE_SYSCALL) | PTE_SHARE;
	else if (perm & PTE_W)
		perm = (perm & ~PTE_W) | PTE_COW;
	if ((r = sys_page_map(0, addr, envid, addr, perm)) < 0)
		panic("duppage: %e", r);
	if ((perm & PTE_COW) &&
	    (r = sys_page_map(0, addr, 0, addr, perm)) < 0)
		panic("duppage: %e", r);
	return 0;
}

static int
is_stack_page(void *addr)
{
	uintptr_t a = (uintptr_t) addr;

	if (a >= UXSTACKTOP - PGSIZE && a < UXSTACKTOP)
		return 1;
	if (a >= USTACKTOP - PGSIZE && a < USTACKTOP)
		return 1;
	return 0;
}

static int
sharepage(envid_t envid, unsigned pn)
{
	void *addr = (void *) (pn * PGSIZE);
	int perm = uvpt[pn] & PTE_SYSCALL;
	int r;

	if (uvpt[pn] & PTE_SHARE)
		perm |= PTE_SHARE;
	else if (perm & PTE_W)
		perm = (perm & ~PTE_COW) | PTE_SHARE | PTE_W;

	if ((r = sys_page_map(0, addr, envid, addr, perm)) < 0)
		return r;
	return 0;
}

envid_t
sfork(void)
{
	envid_t envid;
	uint8_t *addr;
	int r;

	set_pgfault_handler(pgfault);

	envid = sys_exofork();
	if (envid < 0)
		panic("sfork: %e", envid);
	if (envid == 0)
		return 0;

	for (addr = 0; addr < (uint8_t *) UTOP; addr += PGSIZE) {
		if (addr == (uint8_t *) (UXSTACKTOP - PGSIZE))
			continue;
		if ((uvpd[PDX(addr)] & PTE_P) && (uvpt[PGNUM(addr)] & PTE_P) &&
		    (uvpt[PGNUM(addr)] & PTE_U)) {
			if (is_stack_page(addr)) {
				if ((r = duppage(envid, PGNUM(addr))) < 0)
					panic("sfork: duppage: %e", r);
			} else if ((r = sharepage(envid, PGNUM(addr))) < 0)
				panic("sfork: sharepage: %e", r);
		}
	}

	if ((r = sys_page_alloc(envid, (void *) (UXSTACKTOP - PGSIZE),
				PTE_U | PTE_W)) < 0)
		panic("sfork: exception stack alloc: %e", r);
	if ((r = sys_env_set_pgfault_upcall(envid, _pgfault_upcall)) < 0)
		panic("sfork: set pgfault upcall: %e", r);
	if ((r = sys_env_set_status(envid, ENV_RUNNABLE)) < 0)
		panic("sfork: set status: %e", r);

	return envid;
}
