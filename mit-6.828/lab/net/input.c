#include "ns.h"

extern union Nsipc nsipcbuf;

#define INPUT_BUFSIZE 2048

void
input(envid_t ns_envid)
{
	binaryname = "ns_input";

	uint8_t inputbuf[INPUT_BUFSIZE];
	int r;

	while (1) {
		memset(inputbuf, 0, sizeof(inputbuf));

		while ((r = sys_net_recv(inputbuf, sizeof(inputbuf))) == -E_RX_EMPTY)
			sys_yield();

		if (r < 0)
			panic("%s: %e", binaryname, r);

		nsipcbuf.pkt.jp_len = r;
		memmove(nsipcbuf.pkt.jp_data, inputbuf, r);
		ipc_send(ns_envid, NSREQ_INPUT, &nsipcbuf, PTE_P | PTE_U);
		sys_yield();
	}
}
