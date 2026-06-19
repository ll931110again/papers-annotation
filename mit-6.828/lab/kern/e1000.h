#ifndef JOS_KERN_E1000_H
#define JOS_KERN_E1000_H

#include <inc/types.h>
#include <kern/pci.h>

#define E1000_VEN_ID			0x8086
#define E1000_DEV_ID_82540EM		0x100E

#define ETH_PKT_SIZE			1518
#define TX_BUF_SIZE			1536
#define NTXDESC				64
#define RX_BUF_SIZE			2048
#define NRXDESC				128

#define E1000_STATUS			0x00008
#define E1000_RCTL			0x00100
#define E1000_TCTL			0x00400
#define E1000_TIPG			0x00410
#define E1000_RDBAL			0x02800
#define E1000_RDBAH			0x02804
#define E1000_RDLEN			0x02808
#define E1000_RDH			0x02810
#define E1000_RDT			0x02818
#define E1000_TDBAL			0x03800
#define E1000_TDBAH			0x03804
#define E1000_TDLEN			0x03808
#define E1000_TDH			0x03810
#define E1000_TDT			0x03818
#define E1000_RAL			0x05400
#define E1000_RAH			0x05404

#define E1000_TCTL_EN			0x00000002
#define E1000_TCTL_PSP			0x00000008
#define E1000_TCTL_CT			0x00000ff0
#define E1000_TCTL_COLD			0x003ff000
#define E1000_CT_SHIFT			4
#define E1000_COLD_SHIFT		12
#define E1000_COLLISION_THRESHOLD	0x10
#define E1000_COLLISION_DISTANCE	0x40

#define E1000_TIPG_IPGT_MASK		0x000003FF
#define E1000_TIPG_IPGR1_MASK		0x000FFC00
#define E1000_TIPG_IPGR2_MASK		0x3FF00000
#define E1000_TIPG_IPGR1_SHIFT		10
#define E1000_TIPG_IPGR2_SHIFT		20
#define E1000_DEFAULT_TIPG_IPGT		10
#define E1000_DEFAULT_TIPG_IPGR1	4
#define E1000_DEFAULT_TIPG_IPGR2	6

#define E1000_RCTL_EN			0x00000002
#define E1000_RCTL_LBM			0x000000c0
#define E1000_RCTL_RDMTS		0x00000300
#define E1000_RCTL_SZ			0x00030000
#define E1000_RCTL_SECRC		0x04000000
#define E1000_RCTL_BSEX			0x02000000
#define E1000_RCTL_LBM_NO		0x00000000
#define E1000_RCTL_LBM_SHIFT		6
#define E1000_RCTL_RDMTS_HALF		0x00000000
#define E1000_RCTL_RDMTS_SHIFT		8
#define E1000_RCTL_SZ_2048		0x00000000
#define E1000_RCTL_SZ_SHIFT		16

#define E1000_RAH_AV			0x80000000
#define JOS_DEFAULT_MAC_LOW		0x12005452
#define JOS_DEFAULT_MAC_HIGH		0x00005634

#define E1000_TXD_CMD_EOP		0x01
#define E1000_TXD_CMD_RS		0x08
#define E1000_TXD_STAT_DD		0x01
#define E1000_RXD_STAT_DD		0x01

struct e1000_tx_desc {
	uint64_t addr;
	uint16_t length;
	uint8_t cso;
	uint8_t cmd;
	uint8_t status;
	uint8_t css;
	uint16_t special;
} __attribute__((packed));

struct e1000_rx_desc {
	uint64_t addr;
	uint16_t length;
	uint16_t chksum;
	uint8_t status;
	uint8_t err;
	uint16_t special;
} __attribute__((packed));

int e1000_attach(struct pci_func *pcif);
int e1000_transmit(const void *buf, size_t size);
int e1000_receive(void *buf, size_t size);

#endif	// JOS_KERN_E1000_H
