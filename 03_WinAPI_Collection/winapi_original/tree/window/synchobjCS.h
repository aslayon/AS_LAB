#ifndef __synch_obj_h
#define __synch_obj_h
/* CRITICAL_SECTION Version */


#define CV_TIMEOUT 25  /* tunable parameter for the CV model */


/* THRESHOLD BARRIER - TYPE DEFINITION AND FUNCTIONS */
typedef struct THRESHOLD_BARRIER_TAG { 	/* Threshold barrier */
	CRITICAL_SECTION b_guard;	/* CRITICAL_SECTION for the object */
	HANDLE b_broadcast;	/* auto reset event: b_count >= b_threshold */
	volatile DWORD b_destroyed;	/* Is it valid */
	volatile DWORD b_count;		/* number of threads that have reaached the barrier */
	volatile DWORD b_threshold;	/* barrier threshold */
} THRESHOLD_BARRIER, *THB_HANDLE;

DWORD CreateThresholdBarrier (THB_HANDLE *, DWORD /* threshold */);
DWORD WaitThresholdBarrier (THB_HANDLE);
DWORD CloseThresholdBarrier (THB_HANDLE);

/*  SEMAPHORE - TYPE DEFINITION AND FUNCTIONS */
typedef struct ethread_semaphore_tag { 	/* Semaphore */
	CRITICAL_SECTION s_guard;	/* CRITICAL_SECTION for the object */
	HANDLE s_fcfs;		/* Used for fcfs semaphores */
	HANDLE s_broadcast;	/* s_count has increased */
	volatile DWORD s_max;	/* Maximum semaphore count */
	volatile DWORD s_count;	/* Current semaphore count */
	volatile int f_fcfs;		/* First come, first served, or first fit */
} ethread_semaphore_t;

/* Definitions of a sychronized, general bounded queue structure. */
/* Queues are implemented as arrays with indices to youngest */
/* and oldest messages, with wrap around. 					*/
/* Each queue also contains a guard mutex and			*/
/* "not empty" and "not full" condition variables.		*/
/* Finally, there is a pointer to an array of messages of	*/
/* arbitrary type						*/

typedef struct queue_tag { 	/* General purpose queue 	*/
	CRITICAL_SECTION	q_guard;/* Guard the message block	*/
	HANDLE	q_ne;	/* Queue is not empty		*/
	HANDLE	q_nf;	/* Queue is not full		*/
	volatile DWORD q_size;	/* Queue max size size		*/
	volatile DWORD q_first;	/* Index of oldest message	*/
	volatile DWORD q_last;	/* Index of youngest msg	*/
	volatile DWORD q_destroyed;/* Q receiver has terminated	*/
	PVOID	msg_array;	/* array of q_size messages	*/
} queue_t;

/* Queue management functions */
DWORD q_initialize (queue_t *, DWORD, DWORD);
DWORD q_destroy (queue_t *);
DWORD q_destroyed (queue_t *);
DWORD q_empty (queue_t *);
DWORD q_full (queue_t *);
DWORD q_get (queue_t *, PVOID, DWORD, DWORD);
DWORD q_put (queue_t *, PVOID, DWORD, DWORD);
DWORD q_remove (queue_t *, PVOID, DWORD);
DWORD q_insert (queue_t *, PVOID, DWORD);

#endif
