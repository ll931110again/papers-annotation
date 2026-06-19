#include "ns.h"

extern union Nsipc nsipcbuf;

void
output(envid_t ns_envid)
{
	binaryname = "ns_output";

	int32_t req;
	envid_t whom;
	int r;

	while (1) {
		req = ipc_recv(&whom, &nsipcbuf, NULL);
		if (req != NSREQ_OUTPUT)
			continue;

		while ((r = sys_net_send(nsipcbuf.pkt.jp_data,
					 nsipcbuf.pkt.jp_len)) == -E_TX_FULL)
			sys_yield();

		if (r < 0) {
			if (r == -E_PKT_TOO_LARGE) {
				cprintf("%s: packet too large (%d bytes), ignored\n",
					binaryname, nsipcbuf.pkt.jp_len);
				continue;
			}
			panic("%s: sys_net_send: %e", binaryname, r);
		}
	}
}
