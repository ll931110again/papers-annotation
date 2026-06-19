#include <inc/lib.h>
#include <inc/elf.h>

// Load a program into ETEMP and replace the current environment with it.
int
exec(const char *prog, const char **argv)
{
	unsigned char elf_buf[512];
	struct Elf *elf;
	struct Stat st;
	int fd, r;
	uintptr_t temp;
	size_t off;

	if ((r = open(prog, O_RDONLY)) < 0)
		return r;
	fd = r;

	if ((r = fstat(fd, &st)) < 0) {
		close(fd);
		return r;
	}

	for (temp = (uintptr_t) ETEMP, off = 0; off < (size_t) st.st_size;
	     temp += PGSIZE, off += PGSIZE) {
		if ((r = sys_page_alloc(0, (void *) temp, PTE_P | PTE_U | PTE_W)) < 0)
			goto error;
		if ((r = readn(fd, (void *) temp, PGSIZE)) < 0)
			goto error;
	}

	elf = (struct Elf *) ETEMP;
	if (elf->e_magic != ELF_MAGIC) {
		close(fd);
		return -E_NOT_EXEC;
	}

	if ((r = sys_exec((void *) ETEMP, argv)) < 0)
		goto error;

	close(fd);
	return 0;

error:
	close(fd);
	sys_env_destroy(0);
	return r;
}

int
execl(const char *prog, const char *arg0, ...)
{
	int argc = 0;
	va_list vl;

	va_start(vl, arg0);
	while (va_arg(vl, void *) != NULL)
		argc++;
	va_end(vl);

	const char *args[argc + 2];
	args[0] = arg0;
	args[argc + 1] = NULL;

	va_start(vl, arg0);
	for (unsigned i = 0; i < (unsigned) argc; i++)
		args[i + 1] = va_arg(vl, const char *);
	va_end(vl);

	return exec(prog, args);
}
