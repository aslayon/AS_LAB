#pragma once

#ifndef _NODELIST_INT_H
#define _NODELIST_INT_H
#include<string>
#include<iostream>
using namespace std;
#include "Node_int.h"

typedef struct _NodeList {
    Node* m_pHead;
    Node* m_pTail;
    struct _NodeList* m_pNext;
    struct _NodeList* m_pPrevious;
    unsigned int m_uCount;
    string m_Date;
    Node* m_pCurrent;
} NodeList;

#endif // _NODELIST_INT_H
