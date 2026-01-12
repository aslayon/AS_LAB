#pragma once
#ifndef _Node_int_H
#define _Node_int_H
#include<iostream>
#include<string>
using namespace std;
typedef struct _Node {
	struct _Node* m_pPrevious;
	string m_String;
	int m_iObject;
	struct _Node* m_pNext;
}Node;


#endif // !_Node_int_H