#ifndef _NOEXCLUSIONS
#include "Exclude.h"	/* Define Preprocessor variables to */
			/* exclude un-wanted header files. */
#endif
#include "envirmnt.h"
#include <windows.h>
#include <tchar.h>
#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
#include <io.h>
#include "support.h"
#ifdef _MT
#include <process.h>
#endif
