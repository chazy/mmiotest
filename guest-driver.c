/*
 * guest-driver - start fake VM and test MMIO operations
 * Copyright (C) 2012 Christoffer Dall <cdall@cs.columbia.edu>
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.# 
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <linux/kvm.h>

#include <io_common.h>

#define pr_err(fmt, args...) fprintf(stderr, fmt "\n", args)
#define pr_errno(fmt, args...) \
	fprintf(stderr, fmt ": %s\n", args, strerror(errno))

#define MAP_SIZE (4 * 4096) // Four pages of assembly, my hands won't bleed
#define PAGE_SIZE (4096)
#define PAGE_MASK (~(PAGE_SIZE - 1))

#define CODE_SLOT 0
#define CODE_PHYS_BASE (0x80000000)
#define RW_SLOT 1
#define RW_PHYS_BASE (0x40000000)

static int sys_fd;
static int vm_fd;
static int vcpu_fd;
static struct kvm_run *kvm_run;
static void *code_base;
static struct kvm_userspace_memory_region code_mem;
static void *rw_base;
static struct kvm_userspace_memory_region rw_mem;

static char *io_data = IO_DATA;


static int create_vm(void)
{
	vm_fd = ioctl(sys_fd, KVM_CREATE_VM, 0);
	if (vm_fd < 0) {
		perror("kvm_create_vm failed");
		return -1;
	}

	return 0;
}

static int create_vcpu(void)
{
	int mmap_size;

	vcpu_fd = ioctl(vm_fd, KVM_CREATE_VCPU, 0);
	if (vcpu_fd < 0) {
		perror("kvm_create_vcpu failed");
		return -1;
	}

	mmap_size = ioctl(sys_fd, KVM_GET_VCPU_MMAP_SIZE, 0);
	if (mmap_size < 0) {
		perror("KVM_GET_VCPU_MMAP_SIZE failed");
		return -1;
	}

	kvm_run = mmap(NULL, mmap_size, PROT_READ | PROT_WRITE, MAP_SHARED,
		       vcpu_fd, 0);
	if (kvm_run == MAP_FAILED) {
		perror("mmap VCPU run failed!");
		return -1;
	}

	return 0;
}

static int kvm_register_mem(int id, void *addr, unsigned long base,
			    struct kvm_userspace_memory_region *mem)
{
	int ret;

	mem->slot = id;
	mem->guest_phys_addr = base;
	mem->memory_size = MAP_SIZE;
	mem->userspace_addr = (unsigned long)addr;
	mem->flags = 0;

	ret = ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, mem);
	if (ret < 0) {
		pr_errno("error registering region: %d", id);
		return -1;
	}
	return 0;
}

static int register_memregions(const char *code_file)
{
	int ret;

	code_base = mmap(NULL, MAP_SIZE, PROT_READ | PROT_WRITE, MAP_PRIVATE,
			 vm_fd, 0);
	if (code_base == MAP_FAILED) {
		perror("mmap code file failed!");
		return -1;
	} else if ((unsigned long)code_base & ~PAGE_MASK) {
		pr_err("mmap code file on non-page boundary: %p", code_base);
		return -1;
	}
	ret = kvm_register_mem(CODE_SLOT, code_base, CODE_PHYS_BASE, &code_mem);
	if (ret)
		return -1;


	rw_base = mmap(NULL, MAP_SIZE, PROT_READ | PROT_WRITE,
		       MAP_PRIVATE | MAP_ANONYMOUS, 0, 0);
	if (rw_base == MAP_FAILED) {
		perror("mmap rw failed!");
		return -1;
	} else if ((unsigned long)rw_base & ~PAGE_MASK) {
		pr_err("mmap rw region on non-page boundary: %p", rw_base);
		return -1;
	}
	ret = kvm_register_mem(RW_SLOT, rw_base, RW_PHYS_BASE, &rw_mem);
	if (ret)
		return -1;

	return 0;
}

static int init_vcpu(void)
{
	struct kvm_regs regs;

	memset(&regs, 0, sizeof(regs));
	regs.reg15 = CODE_PHYS_BASE;
	regs.reg13[MODE_SVC] = RW_PHYS_BASE + MAP_SIZE;

	if (ioctl(vcpu_fd, KVM_SET_REGS, &regs) < 0) {
		perror("error setting VCPU registers");
		return -1;
	}
	return 0;
}

static int check_write(unsigned long offset, void *_data, unsigned long len)
{
	char *data, *host_data;

	data = _data;
	host_data = io_data + offset;

	if (memcmp(data, host_data, len)) {
		printf("ERROR: VM write mismatch:\n"
		       "VM data: %c%c%c%c%c%c%c%c\n"
		       "IO data: %c%c%c%c%c%c%c%c\n"
		       "    len: %lu\n"
		       " offset: %lu\n",
		       data[0], data[1], data[2], data[3],
		       data[4], data[5], data[6], data[7],
		       host_data[0], host_data[1], host_data[2], host_data[3],
		       host_data[4], host_data[5], host_data[6], host_data[7],
		       len, offset);
		return -1;
	}

	return 0;
}

static int do_read(unsigned long offset, void *data, unsigned long len)
{
	char *host_data;

	host_data = io_data + offset;
	memcpy(data, host_data, len);
	return 0;
}

static int handle_mmio(void)
{
	unsigned long long phys_addr;
	unsigned char *data;
	unsigned long len;
	bool is_write;
	int ret;

	phys_addr = kvm_run->mmio.phys_addr;
	data = kvm_run->mmio.data;
	len = kvm_run->mmio.len;
	is_write = kvm_run->mmio.is_write;

	/* Test if we're reading/writing data */
	if (phys_addr >= IO_DATA_BASE &&
	    phys_addr + len < IO_DATA_BASE + strlen(io_data)) {
		if (is_write)
			ret = check_write(phys_addr - IO_DATA_BASE, data, len);
		else
			ret = do_read(phys_addr - IO_DATA_BASE, data, len);
	}

	/* Test if it's a control operation */
	if (phys_addr >= IO_CTL_BASE && len == IO_DATA_SIZE) {
		if (!is_write)
			return -1; /* only writes allowed */
		switch (data[0]) {
		case CTL_OK:
			printf("PASS: Guest reads what it expects\n");
			return 1;
		case CTL_ERR:
			printf("ERROR: Guest had error\n");
			return -1;
		default:
			printf("INFO: Guest wrote %d\n", data[0]);
		}
	}

	return 0;
}

static int kvm_cpu_exec(void)
{
	int ret;
	bool should_run = true;

	while (should_run) {
		ret = ioctl(vcpu_fd, KVM_RUN, 0);

		if (ret == -EINTR || ret == -EAGAIN) {
			continue;
		} else if (ret < 0) {
			perror("Error running vcpu");
			return -1;
		}

		if (kvm_run->exit_reason == KVM_EXIT_MMIO) {
			ret = handle_mmio();
			if (ret < 0)
				return -1;
			else if (ret > 0)
				should_run = false;
		}
	}

	return 0;
}

static void usage(int argc, const char *argv[])
{
	printf("Usage: %s <binary>\n", argv[0]);
}

int main(int argc, const char *argv[])
{
	int ret;
	const char *file;

	if (argc != 2) {
		usage(argc, argv);
		return EXIT_FAILURE;
	}
	file = argv[1];
	printf("Starting VM with code from: %s\n", file);

	sys_fd = open("/dev/kvm", O_RDWR);
	if (sys_fd < 0) {
		perror("cannot open /dev/kvm - module loaded?");
		return EXIT_FAILURE;
	}

	ret = create_vm();
	if (ret)
		return EXIT_FAILURE;

	ret = register_memregions(file);
	if (ret)
		return EXIT_FAILURE;

	ret = create_vcpu();
	if (ret)
		return EXIT_FAILURE;

	ret = init_vcpu();
	if (ret)
		return EXIT_FAILURE;
	
	ret = kvm_cpu_exec();
	if (ret < 0)
		return EXIT_FAILURE;

	return EXIT_SUCCESS;
}
