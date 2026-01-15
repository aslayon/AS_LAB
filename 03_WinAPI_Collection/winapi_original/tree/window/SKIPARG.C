/* SkipArg.c
	Skip one command line argument - skip tabs and spaces. */

#include "EvryThng.h"

LPTSTR SkipArg (LPCTSTR targv)
{
	LPTSTR p;

	p = (LPTSTR)targv;
		/* Skip up to the next tab or space. */
	while (*p != '\0' && *p != ' ' && *p != '\t') p++;
		/* Skip over tabs and spaces to the next arg. */
	while (*p != '\0' && (*p == ' ' || *p == '\t')) p++;
	return p;
}


