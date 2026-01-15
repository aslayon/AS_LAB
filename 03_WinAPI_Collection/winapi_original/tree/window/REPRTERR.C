#include "EvryThng.h"

VOID ReportError (LPCTSTR UserMessage, DWORD ExitCode, BOOL PrintErrorMsg)

/* General-purpose function for reporting system errors.
	Obtain the error number and turn it into the system error message.
	Display this information and the user-specified message to the standard error device.
	UserMessage:		Message to be displayed to standard error device.
	ExitCode:		0 - Return.
				\x11> 0 - ExitProcess with this code.
	PrintErrorMessage:	Display the last system error message if this flag is set. */
{
	DWORD eMsgLen, ErrNum = GetLastError ();
	LPTSTR lpvSysMsg;
	HANDLE hStdErr;
	hStdErr = GetStdHandle (STD_ERROR_HANDLE);
	PrintMsg (hStdErr, UserMessage);
	if (PrintErrorMsg) {
		eMsgLen = FormatMessage (FORMAT_MESSAGE_ALLOCATE_BUFFER |
				FORMAT_MESSAGE_FROM_SYSTEM, NULL,
				ErrNum, MAKELANGID (LANG_NEUTRAL, SUBLANG_DEFAULT),
				(LPTSTR) &lpvSysMsg, 0, NULL);
		PrintStrings (hStdErr, TEXT ("\n"), lpvSysMsg, TEXT ("\n"), NULL);
		HeapFree (GetProcessHeap (), 0, lpvSysMsg);
				/* Explained in Chapter 6. */

	}

	if (ExitCode > 0)
		ExitProcess (ExitCode);
	else
		return;
}

/* Extension of ReportError to generate a user exception
	code rather than terminating the process. */

VOID ReportException (LPCTSTR UserMessage, DWORD ExceptionCode)
			
/* Report as a non-fatal error.
	Print the system error message only if the message is non-null. */
{	
	if (lstrlen (UserMessage) > 0)
		ReportError (UserMessage, 0, TRUE);
			/* If fatal, raise an exception. */

	if (ExceptionCode != 0) 
		RaiseException (
			(0x0FFFFFFF & ExceptionCode) | 0xE0000000, 0, 0, NULL);
	
	return;
}