#pragma once
#ifndef _Node_int_H
#define _Node_int_H


typedef struct _Node {
	struct _Node* m_pPrevious;
	int m_iObject;
	struct _Node* m_pNext;
}Node;


#endif // !_Node_int_H