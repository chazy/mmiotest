/*
 * mmio-guest.S - world's simplest VM os - purely MMIO test
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
#include <io_common.h>

.arm
.text

1:	mov	r0, #CTL_DONE
	ldr	lr, =IO_CTL_BASE
	strb	r0, [lr]
	b	1b
