#pragma once
#ifndef _LinkedList_int_h
#define _LinkedList_int_h
#include "Node_int.h"

typedef struct {
	Node* m_pHead;
	Node* m_pTail;
	unsigned int m_uCount;
	Node* m_pCurrent;
}LinkedList;


#endif // !_LinkedList_int_h