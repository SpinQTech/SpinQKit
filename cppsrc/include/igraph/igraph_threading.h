/* -*- mode: C -*-  */
/*
   IGraph library.
   Copyright (C) 2011-2012  Gabor Csardi <csardi.gabor@gmail.com>
   334 Harvard street, Cambridge, MA 02139 USA

   This program is free software; you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation; either version 2 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc.,  51 Franklin Street, Fifth Floor, Boston, MA
   02110-1301 USA

*/

#ifndef IGRAPH_THREADING_H
#define IGRAPH_THREADING_H

#include "igraph_decls.h"

__BEGIN_DECLS

/**
 * \define IGRAPH_THREAD_SAFE
 *
 * Specifies whether igraph was built in thread-safe mode.
 *
 * This macro is defined to 1 if the current build of the igraph library is
 * built in thread-safe mode, and 0 if it is not. A thread-safe igraph library
 * attempts to use thread-local data structures instead of global ones, but
 * note that this is not (and can not) be guaranteed for third-party libraries
 * that igraph links to.
 */

#define IGRAPH_THREAD_SAFE 0

__END_DECLS

#endif
