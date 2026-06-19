#include <inc/string.h>
#include <inc/error.h>
#include <kern/e1000.h>
#include <kern/pmap.h>

static volatile void *e1000_base;
static struct e1000_tx_desc e1000_tx_queue[NTXDESC] __attribute__((aligned(16)));
static uint8_t e1000_tx_buf[NTXDESC][TX_BUF_SIZE];
static struct e1000_rx_desc e1000_rx_queue[NRXDESC] __attribute__((aligned(16)));
static uint8_t e1000_rx_buf[NRXDESC][RX_BUF_SIZE];

#define E1000_REG(offset)	(*(volatile uint32_t *)(e1000_base + (offset)))

static void
e1000_tx_init(void)
{
	int i;

	memset(e1000_tx_queue, 0, sizeof(e1000_tx_queue));
	for (i = 0; i < NTXDESC; i++)
		e1000_tx_queue[i].addr = PADDR(e1000_tx_buf[i]);

	E1000_REG(E1000_TDBAL) = PADDR(e1000_tx_queue);
	E1000_REG(E1000_TDBAH) = 0;
	E1000_REG(E1000_TDLEN) = sizeof(e1000_tx_queue);
	E1000_REG(E1000_TDH) = 0;
	E1000_REG(E1000_TDT) = 0;

	E1000_REG(E1000_TCTL) &= ~(E1000_TCTL_CT | E1000_TCTL_COLD);
	E1000_REG(E1000_TCTL) |= E1000_TCTL_EN | E1000_TCTL_PSP |
		(E1000_COLLISION_THRESHOLD << E1000_CT_SHIFT) |
		(E1000_COLLISION_DISTANCE << E1000_COLD_SHIFT);
	E1000_REG(E1000_TIPG) &= ~(E1000_TIPG_IPGT_MASK |
				   E1000_TIPG_IPGR1_MASK |
				   E1000_TIPG_IPGR2_MASK);
	E1000_REG(E1000_TIPG) |= E1000_DEFAULT_TIPG_IPGT |
		(E1000_DEFAULT_TIPG_IPGR1 << E1000_TIPG_IPGR1_SHIFT) |
		(E1000_DEFAULT_TIPG_IPGR2 << E1000_TIPG_IPGR2_SHIFT);
}

static void
e1000_rx_init(void)
{
	int i;

	memset(e1000_rx_queue, 0, sizeof(e1000_rx_queue));
	for (i = 0; i < NRXDESC; i++)
		e1000_rx_queue[i].addr = PADDR(e1000_rx_buf[i]);

	E1000_REG(E1000_RAL) = JOS_DEFAULT_MAC_LOW;
	E1000_REG(E1000_RAH) = JOS_DEFAULT_MAC_HIGH | E1000_RAH_AV;

	E1000_REG(E1000_RDBAL) = PADDR(e1000_rx_queue);
	E1000_REG(E1000_RDBAH) = 0;
	E1000_REG(E1000_RDLEN) = sizeof(e1000_rx_queue);
	E1000_REG(E1000_RDH) = 0;
	E1000_REG(E1000_RDT) = NRXDESC - 1;

	E1000_REG(E1000_RCTL) &= ~(E1000_RCTL_LBM | E1000_RCTL_RDMTS |
				   E1000_RCTL_SZ | E1000_RCTL_BSEX);
	E1000_REG(E1000_RCTL) |= E1000_RCTL_EN | E1000_RCTL_SECRC;
}

int
e1000_attach(struct pci_func *pcif)
{
	pci_func_enable(pcif);
	e1000_base = mmio_map_region(pcif->reg_base[0], pcif->reg_size[0]);
	cprintf("e1000: status 0x%08x\n", E1000_REG(E1000_STATUS));
	e1000_tx_init();
	e1000_rx_init();
	return 0;
}

int
e1000_transmit(const void *buf, size_t size)
{
	int tail = E1000_REG(E1000_TDT);

	if (size > ETH_PKT_SIZE)
		return -E_PKT_TOO_LARGE;

	if ((e1000_tx_queue[tail].cmd & E1000_TXD_CMD_RS) &&
	    !(e1000_tx_queue[tail].status & E1000_TXD_STAT_DD))
		return -E_TX_FULL;

	e1000_tx_queue[tail].status &= ~E1000_TXD_STAT_DD;
	memmove(e1000_tx_buf[tail], buf, size);
	e1000_tx_queue[tail].length = size;
	e1000_tx_queue[tail].cmd |= E1000_TXD_CMD_RS | E1000_TXD_CMD_EOP;

	E1000_REG(E1000_TDT) = (tail + 1) % NTXDESC;
	return 0;
}

int
e1000_receive(void *buf, size_t size)
{
	int tail = E1000_REG(E1000_RDT);
	int next = (tail + 1) % NRXDESC;
	int length;

	if (!(e1000_rx_queue[next].status & E1000_RXD_STAT_DD))
		return -E_RX_EMPTY;

	length = e1000_rx_queue[next].length;
	if (length > (int) size)
		return -E_PKT_TOO_LARGE;

	memmove(buf, e1000_rx_buf[next], length);
	e1000_rx_queue[next].status &= ~E1000_RXD_STAT_DD;
	E1000_REG(E1000_RDT) = next;
	return length;
}
