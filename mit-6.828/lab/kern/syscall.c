/* See COPYRIGHT for copyright information. */

#include <inc/x86.h>
#include <inc/error.h>
#include <inc/string.h>
#include <inc/assert.h>
#include <inc/elf.h>
#include <inc/memlayout.h>

#include <kern/env.h>
#include <kern/pmap.h>
#include <kern/trap.h>
#include <kern/syscall.h>
#include <kern/console.h>
#include <kern/sched.h>
#include <kern/time.h>
#include <kern/e1000.h>

// Print a string to the system console.
// The string is exactly 'len' characters long.
// Destroys the environment on memory errors.
static void
sys_cputs(const char *s, size_t len)
{
	// Check that the user has permission to read memory [s, s+len).
	// Destroy the environment if not.

	// LAB 3: Your code here.
	user_mem_assert(curenv, s, len, PTE_U);

	// Print the string supplied by the user.
	cprintf("%.*s", len, s);
}

// Read a character from the system console without blocking.
// Returns the character, or 0 if there is no input waiting.
static int
sys_cgetc(void)
{
	return cons_getc();
}

// Returns the current environment's envid.
static envid_t
sys_getenvid(void)
{
	return curenv->env_id;
}

// Destroy a given environment (possibly the currently running environment).
//
// Returns 0 on success, < 0 on error.  Errors are:
//	-E_BAD_ENV if environment envid doesn't currently exist,
//		or the caller doesn't have permission to change envid.
static int
sys_env_destroy(envid_t envid)
{
	int r;
	struct Env *e;

	if ((r = envid2env(envid, &e, 1)) < 0)
		return r;
	env_destroy(e);
	return 0;
}

// Deschedule current environment and pick a different one to run.
static void
sys_yield(void)
{
	sched_yield();
}

// Allocate a new environment.
// Returns envid of new environment, or < 0 on error.  Errors are:
//	-E_NO_FREE_ENV if no free environment is available.
//	-E_NO_MEM on memory exhaustion.
static envid_t
sys_exofork(void)
{
	// Create the new environment with env_alloc(), from kern/env.c.
	// It should be left as env_alloc created it, except that
	// status is set to ENV_NOT_RUNNABLE, and the register set is copied
	// from the current environment -- but tweaked so sys_exofork
	// will appear to return 0.

	// LAB 4: Your code here.
	struct Env *e;
	int r;

	if ((r = env_alloc(&e, curenv->env_id)) < 0)
		return r;
	e->env_status = ENV_NOT_RUNNABLE;
	e->env_tf = curenv->env_tf;
	e->env_tf.tf_regs.reg_eax = 0;
	return e->env_id;
}

// Set envid's env_status to status, which must be ENV_RUNNABLE
// or ENV_NOT_RUNNABLE.
//
// Returns 0 on success, < 0 on error.  Errors are:
//	-E_BAD_ENV if environment envid doesn't currently exist,
//		or the caller doesn't have permission to change envid.
//	-E_INVAL if status is not a valid status for an environment.
static int
sys_env_set_status(envid_t envid, int status)
{
	// Hint: Use the 'envid2env' function from kern/env.c to translate an
	// envid to a struct Env.
	// You should set envid2env's third argument to 1, which will
	// check whether the current environment has permission to set
	// envid's status.

	// LAB 4: Your code here.
	struct Env *e;
	int r;

	if (status != ENV_RUNNABLE && status != ENV_NOT_RUNNABLE)
		return -E_INVAL;
	if ((r = envid2env(envid, &e, 1)) < 0)
		return r;
	e->env_status = status;
	return 0;
}

// Set envid's trap frame to 'tf'.
// tf is modified to make sure that user environments always run at code
// protection level 3 (CPL 3) with interrupts enabled.
//
// Returns 0 on success, < 0 on error.  Errors are:
//	-E_BAD_ENV if environment envid doesn't currently exist,
//		or the caller doesn't have permission to change envid.
static int
sys_env_set_trapframe(envid_t envid, struct Trapframe *tf)
{
	// LAB 5: Your code here.
	struct Env *e;
	int r;

	if ((r = envid2env(envid, &e, 1)) < 0)
		return r;
	user_mem_assert(curenv, tf, sizeof(struct Trapframe), PTE_U);
	e->env_tf = *tf;
	e->env_tf.tf_cs |= 3;
	e->env_tf.tf_eflags |= FL_IF;
	return 0;
}

// Set the page fault upcall for 'envid' by modifying the corresponding struct
// Env's 'env_pgfault_upcall' field.  When 'envid' causes a page fault, the
// kernel will push a fault record onto the exception stack, then branch to
// 'func'.
//
// Returns 0 on success, < 0 on error.  Errors are:
//	-E_BAD_ENV if environment envid doesn't currently exist,
//		or the caller doesn't have permission to change envid.
static int
sys_env_set_pgfault_upcall(envid_t envid, void *func)
{
	// LAB 4: Your code here.
	struct Env *e;
	int r;

	if ((r = envid2env(envid, &e, 1)) < 0)
		return r;
	e->env_pgfault_upcall = func;
	return 0;
}

// Allocate a page of memory and map it at 'va' with permission
// 'perm' in the address space of 'envid'.
// The page's contents are set to 0.
// If a page is already mapped at 'va', that page is unmapped as a
// side effect.
//
// perm -- PTE_U | PTE_P must be set, PTE_AVAIL | PTE_W may or may not be set,
//         but no other bits may be set.  See PTE_SYSCALL in inc/mmu.h.
//
// Return 0 on success, < 0 on error.  Errors are:
//	-E_BAD_ENV if environment envid doesn't currently exist,
//		or the caller doesn't have permission to change envid.
//	-E_INVAL if va >= UTOP, or va is not page-aligned.
//	-E_INVAL if perm is inappropriate (see above).
//	-E_NO_MEM if there's no memory to allocate the new page,
//		or to allocate any necessary page tables.
static int
sys_page_alloc(envid_t envid, void *va, int perm)
{
	// Hint: This function is a wrapper around page_alloc() and
	//   page_insert() from kern/pmap.c.
	//   Most of the new code you write should be to check the
	//   parameters for correctness.
	//   If page_insert() fails, remember to free the page you
	//   allocated!

	// LAB 4: Your code here.
	struct Env *e;
	struct PageInfo *pp;
	int r;

	if ((uintptr_t) va >= UTOP || (uintptr_t) va % PGSIZE)
		return -E_INVAL;
	if ((perm & ~(PTE_SYSCALL | PTE_SHARE)) || !(perm & PTE_U))
		return -E_INVAL;
	if ((r = envid2env(envid, &e, 1)) < 0)
		return r;
	if (!(pp = page_alloc(ALLOC_ZERO)))
		return -E_NO_MEM;
	if ((r = page_insert(e->env_pgdir, pp, va, perm)) < 0) {
		page_free(pp);
		return r;
	}
	return 0;
}

// Map the page of memory at 'srcva' in srcenvid's address space
// at 'dstva' in dstenvid's address space with permission 'perm'.
// Perm has the same restrictions as in sys_page_alloc, except
// that it also must not grant write access to a read-only
// page.
//
// Return 0 on success, < 0 on error.  Errors are:
//	-E_BAD_ENV if srcenvid and/or dstenvid doesn't currently exist,
//		or the caller doesn't have permission to change one of them.
//	-E_INVAL if srcva >= UTOP or srcva is not page-aligned,
//		or dstva >= UTOP or dstva is not page-aligned.
//	-E_INVAL is srcva is not mapped in srcenvid's address space.
//	-E_INVAL if perm is inappropriate (see sys_page_alloc).
//	-E_INVAL if (perm & PTE_W), but srcva is read-only in srcenvid's
//		address space.
//	-E_NO_MEM if there's no memory to allocate any necessary page tables.
static int
sys_page_map(envid_t srcenvid, void *srcva,
	     envid_t dstenvid, void *dstva, int perm)
{
	// Hint: This function is a wrapper around page_lookup() and
	//   page_insert() from kern/pmap.c.
	//   Again, most of the new code you write should be to check the
	//   parameters for correctness.
	//   Use the third argument to page_lookup() to
	//   check the current permissions on the page.

	// LAB 4: Your code here.
	struct Env *srcenv, *dstenv;
	pte_t *pte;
	struct PageInfo *pp;
	int r;

	if ((uintptr_t) srcva >= UTOP || (uintptr_t) srcva % PGSIZE)
		return -E_INVAL;
	if ((uintptr_t) dstva >= UTOP || (uintptr_t) dstva % PGSIZE)
		return -E_INVAL;
	if ((perm & ~(PTE_SYSCALL | PTE_SHARE)) || !(perm & PTE_U))
		return -E_INVAL;
	if ((r = envid2env(srcenvid, &srcenv, 1)) < 0)
		return r;
	if ((r = envid2env(dstenvid, &dstenv, 1)) < 0)
		return r;
	if (!(pte = pgdir_walk(srcenv->env_pgdir, srcva, 0)))
		return -E_INVAL;
	if (!(*pte & PTE_P))
		return -E_INVAL;
	if ((perm & PTE_W) && !(*pte & PTE_W))
		return -E_INVAL;
	pp = pa2page(PTE_ADDR(*pte));
	if ((r = page_insert(dstenv->env_pgdir, pp, dstva, perm)) < 0)
		return r;
	return 0;
}

// Unmap the page of memory at 'va' in the address space of 'envid'.
// If no page is mapped, the function silently succeeds.
//
// Return 0 on success, < 0 on error.  Errors are:
//	-E_BAD_ENV if environment envid doesn't currently exist,
//		or the caller doesn't have permission to change envid.
//	-E_INVAL if va >= UTOP, or va is not page-aligned.
static int
sys_page_unmap(envid_t envid, void *va)
{
	// Hint: This function is a wrapper around page_remove().

	// LAB 4: Your code here.
	struct Env *e;
	int r;

	if ((uintptr_t) va >= UTOP || (uintptr_t) va % PGSIZE)
		return -E_INVAL;
	if ((r = envid2env(envid, &e, 1)) < 0)
		return r;
	page_remove(e->env_pgdir, va);
	return 0;
}

// Try to send 'value' to the target env 'envid'.
// If srcva < UTOP, then also send page currently mapped at 'srcva',
// so that receiver gets a duplicate mapping of the same page.
//
// The send fails with a return value of -E_IPC_NOT_RECV if the
// target is not blocked, waiting for an IPC.
//
// The send also can fail for the other reasons listed below.
//
// Otherwise, the send succeeds, and the target's ipc fields are
// updated as follows:
//    env_ipc_recving is set to 0 to block future sends;
//    env_ipc_from is set to the sending envid;
//    env_ipc_value is set to the 'value' parameter;
//    env_ipc_perm is set to 'perm' if a page was transferred, 0 otherwise.
// The target environment is marked runnable again, returning 0
// from the paused sys_ipc_recv system call.  (Hint: does the
// sys_ipc_recv function ever actually return?)
//
// If the sender wants to send a page but the receiver isn't asking for one,
// then no page mapping is transferred, but no error occurs.
// The ipc only happens when no errors occur.
//
// Returns 0 on success, < 0 on error.
// Errors are:
//	-E_BAD_ENV if environment envid doesn't currently exist.
//		(No need to check permissions.)
//	-E_IPC_NOT_RECV if envid is not currently blocked in sys_ipc_recv,
//		or another environment managed to send first.
//	-E_INVAL if srcva < UTOP but srcva is not page-aligned.
//	-E_INVAL if srcva < UTOP and perm is inappropriate
//		(see sys_page_alloc).
//	-E_INVAL if srcva < UTOP but srcva is not mapped in the caller's
//		address space.
//	-E_INVAL if (perm & PTE_W), but srcva is read-only in the
//		current environment's address space.
//	-E_NO_MEM if there's not enough memory to map srcva in envid's
//		address space.
static int
sys_ipc_try_send(envid_t envid, uint32_t value, void *srcva, unsigned perm)
{
	// LAB 4: Your code here.
	struct Env *e;
	pte_t *pte;
	int r;

	if ((r = envid2env(envid, &e, 0)) < 0)
		return r;
	if (!e->env_ipc_recving)
		return -E_IPC_NOT_RECV;

	if ((uintptr_t) srcva < UTOP) {
		if ((uintptr_t) srcva % PGSIZE)
			return -E_INVAL;
		if ((perm & ~(PTE_SYSCALL | PTE_SHARE)) || !(perm & PTE_U))
			return -E_INVAL;
		if (!(pte = pgdir_walk(curenv->env_pgdir, srcva, 0)))
			return -E_INVAL;
		if (!(*pte & PTE_P))
			return -E_INVAL;
		if ((perm & PTE_W) && !(*pte & PTE_W))
			return -E_INVAL;
	}

	e->env_ipc_from = curenv->env_id;
	e->env_ipc_value = value;
	e->env_ipc_recving = 0;
	e->env_status = ENV_RUNNABLE;

	if ((uintptr_t) srcva < UTOP && (uintptr_t) e->env_ipc_dstva < UTOP) {
		if ((r = page_insert(e->env_pgdir, pa2page(PTE_ADDR(*pte)),
				     e->env_ipc_dstva, perm)) < 0)
			return r;
		e->env_ipc_perm = perm;
	} else {
		e->env_ipc_perm = 0;
	}

	return 0;
}

// Block until a value is ready.  Record that you want to receive
// using the env_ipc_recving and env_ipc_dstva fields of struct Env,
// mark yourself not runnable, and then give up the CPU.
//
// If 'dstva' is < UTOP, then you are willing to receive a page of data.
// 'dstva' is the virtual address at which the sent page should be mapped.
//
// This function only returns on error, but the system call will eventually
// return 0 on success.
// Return < 0 on error.  Errors are:
//	-E_INVAL if dstva < UTOP but dstva is not page-aligned.
static int
sys_ipc_recv(void *dstva)
{
	// LAB 4: Your code here.
	if ((uintptr_t) dstva < UTOP && (uintptr_t) dstva % PGSIZE)
		return -E_INVAL;
	curenv->env_ipc_recving = 1;
	curenv->env_ipc_dstva = dstva;
	curenv->env_status = ENV_NOT_RUNNABLE;
	sched_yield();
	return 0;
}

// Return the current time.
static int
sys_time_msec(void)
{
	return time_msec();
}

static int
sys_net_send(const void *buf, size_t size)
{
	user_mem_assert(curenv, buf, size, PTE_U);
	return e1000_transmit(buf, size);
}

static int
sys_net_recv(void *buf, size_t size)
{
	user_mem_assert(curenv, buf, size, PTE_U);
	return e1000_receive(buf, size);
}

static void
exec_region_alloc(struct Env *e, void *va, size_t len, int perm)
{
	void *start = ROUNDDOWN(va, PGSIZE);
	void *end = ROUNDUP((char *) va + len, PGSIZE);
	struct PageInfo *pp;
	int r;

	for (; start < end; start += PGSIZE) {
		pp = page_alloc(ALLOC_ZERO);
		if (!pp)
			panic("exec_region_alloc: page_alloc failed");
		if ((r = page_insert(e->env_pgdir, pp, start, perm)) < 0)
			panic("exec_region_alloc: page_insert failed: %e", r);
	}
}

static void
exec_unmap_user(struct Env *e, uintptr_t keep_lo, uintptr_t keep_hi)
{
	uint32_t pdeno, pteno;
	pte_t *pt;
	uintptr_t va;

	for (pdeno = 0; pdeno < PDX(UTOP); pdeno++) {
		if (!(e->env_pgdir[pdeno] & PTE_P))
			continue;
		pt = (pte_t *) KADDR(PTE_ADDR(e->env_pgdir[pdeno]));
		for (pteno = 0; pteno <= PTX(~0); pteno++) {
			if (!(pt[pteno] & PTE_P))
				continue;
			va = (uintptr_t) PGADDR(pdeno, pteno, 0);
			if (va >= keep_lo && va < keep_hi)
				continue;
			if (pt[pteno] & PTE_SHARE)
				continue;
			page_remove(e->env_pgdir, (void *) va);
		}
	}
}

static int
sys_exec(void *binary, const char **argv)
{
	struct Elf elfcopy;
	struct Proghdr phdrs[32];
	struct Proghdr *ph, *eph;
	size_t string_size, staging_sz;
	int argc, i, r;
	char *string_store;
	uintptr_t *argv_store;
	uintptr_t init_esp;
	uintptr_t keep_lo, keep_hi;
	char argbuf[512];
	char *argp;

	user_mem_assert(curenv, binary, sizeof(struct Elf), PTE_U);
	lcr3(PADDR(curenv->env_pgdir));
	memcpy(&elfcopy, binary, sizeof(elfcopy));
	if (elfcopy.e_phnum > (int) (sizeof(phdrs) / sizeof(phdrs[0])))
		panic("sys_exec: too many phdrs");
	memcpy(phdrs, (uint8_t *) binary + elfcopy.e_phoff,
	       elfcopy.e_phnum * sizeof(struct Proghdr));

	string_size = 0;
	for (argc = 0;; argc++) {
		const char *s;
		size_t len;

		user_mem_assert(curenv, &argv[argc], sizeof(char *), PTE_U);
		lcr3(PADDR(curenv->env_pgdir));
		s = argv[argc];
		if (!s) {
			lcr3(PADDR(kern_pgdir));
			break;
		}
		if (argc >= 32) {
			lcr3(PADDR(kern_pgdir));
			return -E_INVAL;
		}
		lcr3(PADDR(kern_pgdir));
		len = 0;
		while (1) {
			user_mem_assert(curenv, s + len, 1, PTE_U);
			lcr3(PADDR(curenv->env_pgdir));
			if (s[len] == '\0')
				break;
			len++;
			if (len >= sizeof(argbuf) - string_size - 1) {
				lcr3(PADDR(kern_pgdir));
				return -E_NO_MEM;
			}
			lcr3(PADDR(kern_pgdir));
		}
		memcpy(argbuf + string_size, s, len + 1);
		string_size += len + 1;
	}

	if (elfcopy.e_magic != ELF_MAGIC)
		return -E_NOT_EXEC;

	keep_lo = ROUNDDOWN((uintptr_t) binary, PGSIZE);
	staging_sz = PGSIZE;
	ph = phdrs;
	eph = ph + elfcopy.e_phnum;
	for (; ph < eph; ph++) {
		if (ph->p_type != ELF_PROG_LOAD)
			continue;
		if (ph->p_offset + ph->p_filesz > staging_sz)
			staging_sz = ph->p_offset + ph->p_filesz;
	}
	keep_hi = keep_lo + ROUNDUP(staging_sz, PGSIZE);

	exec_unmap_user(curenv, keep_lo, keep_hi);

	ph = phdrs;
	eph = ph + elfcopy.e_phnum;
	for (; ph < eph; ph++) {
		int perm = PTE_U | PTE_W | PTE_P;

		if (ph->p_type != ELF_PROG_LOAD)
			continue;
		if (ph->p_memsz < ph->p_filesz)
			return -E_INVAL;
		exec_region_alloc(curenv, (void *) ph->p_va, ph->p_memsz, perm);
	}

	string_store = (char *) (USTACKTOP - string_size);
	argv_store = (uintptr_t *) (ROUNDDOWN((uintptr_t) string_store, 4) -
				    4 * (argc + 1));
	if ((void *) (argv_store - 2) < (void *) (USTACKTOP - PGSIZE))
		return -E_NO_MEM;

	exec_region_alloc(curenv, (void *) (USTACKTOP - PGSIZE), PGSIZE,
			  PTE_U | PTE_W | PTE_P);

	lcr3(PADDR(curenv->env_pgdir));

	ph = phdrs;
	eph = ph + elfcopy.e_phnum;
	for (; ph < eph; ph++) {
		if (ph->p_type != ELF_PROG_LOAD)
			continue;
		memmove((void *) ph->p_va, (uint8_t *) binary + ph->p_offset,
			ph->p_filesz);
		memset((void *) (ph->p_va + ph->p_filesz), 0,
		       ph->p_memsz - ph->p_filesz);
	}

	argp = argbuf;
	for (i = 0; i < argc; i++) {
		argv_store[i] = (uintptr_t) string_store;
		strcpy(string_store, argp);
		string_store += strlen(argp) + 1;
		argp += strlen(argp) + 1;
	}
	argv_store[argc] = 0;
	argv_store[-1] = (uintptr_t) argv_store;
	argv_store[-2] = argc;
	init_esp = (uintptr_t) &argv_store[-2];

	lcr3(PADDR(kern_pgdir));

	curenv->env_tf.tf_eip = elfcopy.e_entry;
	curenv->env_tf.tf_esp = init_esp;
	curenv->env_tf.tf_eflags |= FL_IF;
	sched_yield();
	return 0;
}

// Dispatches to the correct kernel function, passing the arguments.
int32_t
syscall(uint32_t syscallno, uint32_t a1, uint32_t a2, uint32_t a3, uint32_t a4, uint32_t a5)
{
	// Call the function corresponding to the 'syscallno' parameter.
	// Return any appropriate return value.
	// LAB 3: Your code here.
	switch (syscallno) {
	case SYS_cputs:
		sys_cputs((const char *) a1, (size_t) a2);
		return 0;
	case SYS_cgetc:
		return sys_cgetc();
	case SYS_getenvid:
		return sys_getenvid();
	case SYS_env_destroy:
		return sys_env_destroy((envid_t) a1);
	case SYS_yield:
		sys_yield();
		return 0;
	case SYS_exofork:
		return sys_exofork();
	case SYS_env_set_status:
		return sys_env_set_status((envid_t) a1, (int) a2);
	case SYS_env_set_trapframe:
		return sys_env_set_trapframe((envid_t) a1, (struct Trapframe *) a2);
	case SYS_env_set_pgfault_upcall:
		return sys_env_set_pgfault_upcall((envid_t) a1, (void *) a2);
	case SYS_page_alloc:
		return sys_page_alloc((envid_t) a1, (void *) a2, (int) a3);
	case SYS_page_map:
		return sys_page_map((envid_t) a1, (void *) a2,
				    (envid_t) a3, (void *) a4, (int) a5);
	case SYS_page_unmap:
		return sys_page_unmap((envid_t) a1, (void *) a2);
	case SYS_ipc_try_send:
		return sys_ipc_try_send((envid_t) a1, (uint32_t) a2,
					(void *) a3, (unsigned) a4);
	case SYS_ipc_recv:
		return sys_ipc_recv((void *) a1);
	case SYS_time_msec:
		return sys_time_msec();
	case SYS_net_send:
		return sys_net_send((const void *) a1, (size_t) a2);
	case SYS_net_recv:
		return sys_net_recv((void *) a1, (size_t) a2);
	case SYS_exec:
		return sys_exec((void *) a1, (const char **) a2);
	default:
		return -E_INVAL;
	}
}

