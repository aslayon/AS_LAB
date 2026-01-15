/* PrintMsg.c:
	ConsolePrompt
	PrintStrings
	PrintMsg */

#include "EvryThng.h"
#include <stdarg.h>	 									  

BOOL PrintStrings (HANDLE hOut, ...)

/* Write the messages to the output handle. Frequently hOut
	will be standard out or error, but this is not required.
	Use WriteConsole (to handle Unicode) first, as the
	output will normally be the console. If that fails, use WriteFile.

	hOut:	Handle for output file. 
	... :	Variable argument list containing TCHAR strings.
		The list must be terminated with NULL. */
{
	DWORD MsgLen, Count;
	LPCTSTR pMsg;
	va_list pMsgList;	/* Current message string. */
	va_start (pMsgList, hOut);	/* Start processing msgs. */
	while ((pMsg = va_arg (pMsgList, LPCTSTR)) != NULL) {
		MsgLen = lstrlen (pMsg);
		if (!WriteConsole (hOut, pMsg, MsgLen, &Count, NULL)
				&& !WriteFile (hOut, pMsg, MsgLen * sizeof (TCHAR),
				&Count, NULL))
			return FALSE;
	}
	va_end (pMsgList);
	return TRUE;
}


BOOL PrintMsg (HANDLE hOut, LPCTSTR pMsg)

/* For convenience only - Single message version of PrintStrings so that
	you do not have to remember the NULL arg list terminator.

	hOut:	Handle of output file
	pMsg:	Single message to output. */
{
	return PrintStrings (hOut, pMsg, NULL);
}


BOOL ConsolePrompt (LPCTSTR pPromptMsg, LPTSTR pResponse, DWORD MaxTchar, BOOL Echo)

/* Prompt the user at the console and get a response
	which can be up to MaxTchar generic characters.

	pPromptMessage:	Message displayed to user.
	pResponse:	Programmer-supplied buffer that receives the response.
	MaxTchar:	Maximum size of the user buffer, measured as generic characters.
	Echo:		Do not display the user's response if this flag is FALSE. */
{
	HANDLE hStdIn, hStdOut;
	DWORD TcharIn, EchoFlag;
	BOOL Success;
	hStdIn = CreateFile (TEXT ("CONIN$"), GENERIC_READ | GENERIC_WRITE, 0,
			NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
	hStdOut = CreateFile (TEXT ("CONOUT$"), GENERIC_WRITE, 0,
			NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);

	/* Should the input be echoed? */

	EchoFlag = Echo ? ENABLE_ECHO_INPUT : 0;

	/* API "and" chain. If any test or system call fails, the
		rest of the expression is not evaluated, and the
		subsequent functions are not called. GetStdError ()
		will return the result of the failed call. */

	Success = SetConsoleMode (hStdIn, ENABLE_LINE_INPUT | 
			EchoFlag | ENABLE_PROCESSED_INPUT)
			&& SetConsoleMode (hStdOut,
				ENABLE_WRAP_AT_EOL_OUTPUT | ENABLE_PROCESSED_OUTPUT)
			&& PrintStrings (hStdOut, pPromptMsg, NULL)
			&& ReadConsole (hStdIn, pResponse, MaxTchar, &TcharIn, NULL);

	/* Replace the CR-LF by the null character. */

	if (Success)
		pResponse [TcharIn - 2] = '\0';

	CloseHandle (hStdIn);
	CloseHandle (hStdOut);
	return Success;
}

