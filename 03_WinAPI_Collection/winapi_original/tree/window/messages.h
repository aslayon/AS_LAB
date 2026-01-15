/* messages.h - Used with numerous Chapter 9, 10 programs */

#define DATA_SIZE 256
typedef struct msg_block_tag { /* Message block */
	HANDLE	mguard;	/* Mutex for  the message block	*/
	HANDLE  mconsumed; /* Event: Message consumed;		*/
				/* Produce a new one or stop	*/
	HANDLE  mready; /* Event: Message ready		*/
	/* Note: the mutex and events are not used by some programs, such
	 * as Program 10-3, 4, 5 (the multi-stage pipeline) as the messages
	 * are part of a protected quueue */
	volatile DWORD source; /* Creating producer identity 	*/
	volatile DWORD destination;/* Identity of receiving thread*/

	volatile DWORD f_consumed;
	volatile DWORD f_ready;
	volatile DWORD f_stop; 
		/* Consumed & ready state flags, stop flag	*/
	volatile DWORD sequence; /* Message block sequence number	*/
	time_t timestamp;
	DWORD checksum; /* Message contents checksum		*/
	DWORD data[DATA_SIZE]; /* Message Contents		*/
} msg_block_t;

VOID message_fill (msg_block_t *, DWORD, DWORD, DWORD);
VOID message_display (msg_block_t *);
