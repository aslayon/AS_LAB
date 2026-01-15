/* pcstats.h. Definitions for Chapter 10.				*/

typedef struct statistics_tag { /* Thread-specific statistics */
	msg_block_t *pmblock;
	DWORD th_number;		/* Sequential thread id		*/
	DWORD nmsgs;		/* Number of messages consumed	*/
	DWORD ngood;		/* Number of good messages	*/
	DWORD nbad;		/* Number of bad messages	*/
	double data_sum; 	/* Sum of all data		*/
	time_t firstmsg;	/* Time stamp of first message	*/
	time_t lastmsg;		/* Time stamp of last message	*/
} statistics_t;

DWORD ts_index;		/* Index of thread specific key */
static DWORD thread_number = 0;

LIBSPEC VOID report_statistics (VOID);
LIBSPEC VOID accumulate_statistics (VOID);