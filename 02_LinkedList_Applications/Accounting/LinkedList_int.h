#pragma once
#ifndef _LinkedList_int_h
#define _LinkedList_int_h
#include<string>
#include<iostream>
#include "Node_int.h"
#include "NodeList_int.h"
using namespace std;
typedef struct {
	NodeList* m_pHead;
	NodeList* m_pTail;

	long long m_Total;
	unsigned int m_uCount;
	NodeList* m_pCurrent;
}LinkedList;


#endif // !_LinkedList_int_h