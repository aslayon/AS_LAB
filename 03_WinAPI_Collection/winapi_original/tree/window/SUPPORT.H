/* support.h */
/* Definitions of all symbolic constants and common
	utility functions used throughout the example programs. */

#ifdef _STATICLIB
#define LIBSPEC
#else

#ifdef UTILITY_EXPORTS
#define LIBSPEC _declspec (dllexport)
#else
#define LIBSPEC _declspec (dllimport)
#endif

#endif

#define EMPTY _T ("")
#define YES _T ("y")
#define NO _T ("n")
#define CR 0x0D
#define LF 0x0A
#define TSIZE sizeof (TCHAR)

/* Limits and constants. */

#define TYPE_FILE 1		/* Used in ls, rm, and lsFP */
#define TYPE_DIR 2
#define TYPE_DOT 3

#define MAX_OPTIONS 20	/* Max # command line options */
#define MAX_ARG 1000	/* Max # of command line arguments */
#define MAX_COMMAND_LINE MAX_PATH+50 /* Max size of a command line */
#define MAX_NAME 256    /* Name length - users and groups */

/* Commonly used functions. */

LIBSPEC BOOL ConsolePrompt (LPCTSTR, LPTSTR, DWORD, BOOL);
LIBSPEC BOOL PrintStrings (HANDLE, ...);
LIBSPEC BOOL PrintMsg (HANDLE, LPCTSTR);
LIBSPEC VOID ReportError (LPCTSTR, DWORD, BOOL);
LIBSPEC VOID ReportException (LPCTSTR, DWORD);
LIBSPEC DWORD Options (int, LPCTSTR *, LPCTSTR, ...);
LIBSPEC LPTSTR SkipArg (LPCTSTR);

/* Collection of generic string functions modeled after string.h.
	Created as required - there was only one!
	Implementations are derived from Plauger: The Standard C Library. */

LIBSPEC LPCTSTR wmemchr (LPCTSTR, TCHAR, DWORD);
LIBSPEC VOID GetArgs (LPCTSTR, int *, LPTSTR *);

/* Security Functions. */

LPSECURITY_ATTRIBUTES InitializeUnixSA (DWORD, LPTSTR, LPTSTR, LPDWORD, LPHANDLE);
DWORD ReadFilePermissions (LPTSTR, LPTSTR, LPTSTR);
BOOL ChangeFilePermissions (DWORD, LPTSTR, LPDWORD);
/*	Simpler forms available with Visual C++ Version 5.0 */
//PSECURITY_DESCRIPTOR InitializeSD (DWORD, LPTSTR, LPTSTR, LPDWORD);
/* Constants needed by the security functions. */

#define LUSIZE 1024
#define ACCT_NAME_SIZE LUSIZE

#ifdef _UNICODE /* This declaration had to be added. */
#define _tstrrchr wcsrchr
#else
#define _tstrrchr strrchr
#endif

#ifdef _UNICODE /* This declaration had to be added. */
#define _tstrstr wcsstr
#else
#define _tstrstr strstr
#endif

#ifdef _UNICODE /* This declaration had to be added. */
#define _memtchr wmemchr
#else
#define _memtchr memchr
#endif

/* 
 * Define a macro that delays for an amount of time proportional
 * to the integer parameter. The delay is a CPU delay and does not
 * voluntarily yield the processor. This simulates computation.
 */

#define delay_cpu(n)  {\
	int i=0, j=0;\
	/* Do some wasteful computations that will not be optimized to nothing */\
	while (i < n) {\
		j = (int)(i*i + (float)(2*j)/(float)(i+1));\
		i++;\
	}\
}

