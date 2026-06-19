// Called from entry.S to get us going.
// entry.S already took care of defining envs, pages, uvpd, and uvpt.

#include <inc/lib.h>

extern void umain(int argc, char **argv);

const char *binaryname = "<unknown>";

void
libmain(int argc, char **argv)
{
	if (argc > 0)
		binaryname = argv[0];

	umain(argc, argv);
	exit();
}
