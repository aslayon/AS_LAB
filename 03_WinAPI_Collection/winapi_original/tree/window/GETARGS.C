/* Process a string to turn it into a command line. */

#include "EvryThng.h"

VOID GetArgs (LPCTSTR Command, int *pArgc, LPTSTR argstr [])
{
	int i, icm = 0;
	DWORD ic = 0;

 	for (i = 0; ic < _tcslen (Command); i++) {
		while (ic < _tcslen (Command) && 
				Command [ic] != ' ' && Command [ic] != '\t') {
			argstr [i] [icm] = Command [ic];
			ic++;
			icm++;
		}
		argstr [i] [icm] = '\0';
		while (ic < _tcslen (Command) && 
				(Command [ic] == ' ' || Command [ic] == '\t'))
			ic++;
			icm = 0;
	}

	*pArgc = i;
}

