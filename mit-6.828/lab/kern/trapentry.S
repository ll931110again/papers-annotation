/* See COPYRIGHT for copyright information. */

#include <inc/mmu.h>
#include <inc/memlayout.h>
#include <inc/trap.h>

#include <kern/picirq.h>

#define TRAPHANDLER(name, num)						\
	.globl name;							\
	.type name, @function;						\
	.align 2;							\
	name:								\
	pushl $(num);							\
	jmp _alltraps

#define TRAPHANDLER_NOEC(name, num)					\
	.globl name;							\
	.type name, @function;						\
	.align 2;							\
	name:								\
	pushl $0;							\
	pushl $(num);							\
	jmp _alltraps

.text

TRAPHANDLER_NOEC(handler_divide, T_DIVIDE)
TRAPHANDLER_NOEC(handler_debug, T_DEBUG)
TRAPHANDLER_NOEC(handler_nmi, T_NMI)
TRAPHANDLER_NOEC(handler_brkpt, T_BRKPT)
TRAPHANDLER_NOEC(handler_oflow, T_OFLOW)
TRAPHANDLER_NOEC(handler_bound, T_BOUND)
TRAPHANDLER_NOEC(handler_illop, T_ILLOP)
TRAPHANDLER_NOEC(handler_device, T_DEVICE)
TRAPHANDLER(handler_dblflt, T_DBLFLT)
TRAPHANDLER(handler_tss, T_TSS)
TRAPHANDLER(handler_segnp, T_SEGNP)
TRAPHANDLER(handler_stack, T_STACK)
TRAPHANDLER(handler_gpflt, T_GPFLT)
TRAPHANDLER(handler_pgflt, T_PGFLT)
TRAPHANDLER_NOEC(handler_fperr, T_FPERR)
TRAPHANDLER(handler_align, T_ALIGN)
TRAPHANDLER_NOEC(handler_mchk, T_MCHK)
TRAPHANDLER_NOEC(handler_simderr, T_SIMDERR)

TRAPHANDLER_NOEC(handler_syscall, T_SYSCALL)

TRAPHANDLER_NOEC(handler_irq0, IRQ_OFFSET + IRQ_TIMER)
TRAPHANDLER_NOEC(handler_irq1, IRQ_OFFSET + IRQ_KBD)
TRAPHANDLER_NOEC(handler_irq4, IRQ_OFFSET + IRQ_SERIAL)
TRAPHANDLER_NOEC(handler_irq7, IRQ_OFFSET + IRQ_SPURIOUS)
TRAPHANDLER_NOEC(handler_irq14, IRQ_OFFSET + IRQ_IDE)
TRAPHANDLER_NOEC(handler_irq19, IRQ_OFFSET + IRQ_ERROR)

.globl _alltraps
.type _alltraps, @function
.align 2
_alltraps:
	pushl %ds
	pushl %es
	pushal
	movw $GD_KD, %ax
	movw %ax, %ds
	movw %ax, %es
	pushl %esp
	call trap
