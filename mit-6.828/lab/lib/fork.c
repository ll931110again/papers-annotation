// implement fork from user space

#include <inc/string.h>
#include <inc/lib.h>

// Assembly language pgfault entrypoint defined in lib/pfentry.S.
extern void _pgfault_upcall(void);

// It is one of the bits explicitly allocated to user processes (PTE_AVAIL).
#define PTE_COW		0x800

//
// Custom page fault handler - if faulting page is copy-on-write,
// map in our own private writable copy.
//
static void
pgfault(struct UTrapframe *utf)
{
	void *addr = (void *) utf->utf_fault_va;
	uint32_t err = utf->utf_err;
	int r;

	// Check that the faulting access was (1) a write, and (2) to a
	// copy-on-write page.  If not, panic.
	// Hint:
	//   Use the read-only page table mappings at uvpt
	//   (see <inc/memlayout.h>).

	// LAB 4: Your code here.
	if ((err & FEC_WR) == 0 || (uvpt[PGNUM(addr)] & PTE_COW) == 0)
		panic("pgfault at %p: err %d", addr, err);

	// LAB 4: Your code here.
	if ((r = sys_page_alloc(0, (void *) PFTEMP, PTE_U | PTE_W | PTE_P)) < 0)
		panic("pgfault: page alloc failed: %e", r);
	memmove(PFTEMP, ROUNDDOWN(addr, PGSIZE), PGSIZE);
	if ((r = sys_page_map(0, (void *) PFTEMP, 0, ROUNDDOWN(addr, PGSIZE),
			      PTE_U | PTE_W | PTE_P)) < 0)
		panic("pgfault: page map failed: %e", r);
	if ((r = sys_page_unmap(0, (void *) PFTEMP)) < 0)
		panic("pgfault: page unmap failed: %e", r);
}

//
// Map our virtual page pn (address pn*PGSIZE) into the target envid
// at the same virtual address.  If the page is writable or copy-on-write,
// the new mapping must be created copy-on-write, and then our mapping must be
// marked copy-on-write as well.  (Exercise: Why do we need to mark ours
// copy-on-write again if it was already copy-on-write at the beginning of
// this function?)
//
// Returns: 0 on success, < 0 on error.
// It is also OK to panic on error.
//
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

//
// User-level fork with copy-on-write.
// Set up our page fault handler appropriately.
// Create a child.
// Copy our address space and page fault handler setup to the child.
// Then mark the child as runnable and return.
//
// Returns: child's envid to the parent, 0 to the child, < 0 on error.
// It is also OK to panic on error.
//
// Hint:
//   Use uvpd, uvpt, and duppage.
//   Remember to fix "thisenv" in the child process.
//   Neither user exception stack should ever be marked copy-on-write,
//   so you must allocate a new page for the child's user exception stack.
//
envid_t
fork(void)
{
	// LAB 4: Your code here.
	envid_t envid;
	uint8_t *addr;
	int r;
	extern unsigned char end[];

	set_pgfault_handler(pgfault);

	envid = sys_exofork();
	if (envid < 0)
		panic("fork: %e", envid);
	if (envid == 0)
		return 0;

	for (addr = 0; addr < (uint8_t *) UTOP; addr += PGSIZE) {
		if (addr == (uint8_t *) (UXSTACKTOP - PGSIZE))
			continue;
		if ((uvpd[PDX(addr)] & PTE_P) && (uvpt[PGNUM(addr)] & PTE_P) &&
		    (uvpt[PGNUM(addr)] & PTE_U)) {
			if ((r = duppage(envid, PGNUM(addr))) < 0)
				panic("fork: duppage: %e", r);
		}
	}

	if ((r = sys_page_alloc(envid, (void *) (UXSTACKTOP - PGSIZE),
				PTE_U | PTE_W)) < 0)
		panic("fork: exception stack alloc: %e", r);
	if ((r = sys_env_set_pgfault_upcall(envid, _pgfault_upcall)) < 0)
		panic("fork: set pgfault upcall: %e", r);
	if ((r = sys_env_set_status(envid, ENV_RUNNABLE)) < 0)
		panic("fork: set status: %e", r);

	return envid;
}
