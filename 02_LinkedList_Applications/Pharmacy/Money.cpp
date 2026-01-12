#define _CRT_SECURE_NO_WARNINGS
#include "LinkedList_int.h"
#include <iostream>
#include <string>
#include <stdlib.h>
#include<Windows.h>
using namespace std;


void Create(LinkedList** _ptList) {
	//0으로 초기화된 관리구조를 생성
	*_ptList = (LinkedList*)calloc(1, sizeof(LinkedList));
}

void Destroy(LinkedList** _ptList) {
	if ((*_ptList) == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");

		return;				//비어 있으면 종료
	}
	if (!(*_ptList)->m_pHead) {
		free(*_ptList);
		*_ptList = NULL;
		return;				//비어 있으면 종료
	}
	while ((*_ptList)->m_uCount != 0) {
		(*_ptList)->m_pCurrent = (*_ptList)->m_pHead;
		(*_ptList)->m_pCurrent->m_pCurrent = (*_ptList)->m_pCurrent->m_pHead;
		while ((*_ptList)->m_pCurrent->m_uCount != 0) {
			(*_ptList)->m_pCurrent->m_pHead = (*_ptList)->m_pCurrent->m_pCurrent->m_pNext;
			free((*_ptList)->m_pCurrent);
			(*_ptList)->m_pCurrent->m_uCount--;
			(*_ptList)->m_pCurrent->m_pCurrent = (*_ptList)->m_pCurrent->m_pHead;
		}
		(*_ptList)->m_pCurrent = (*_ptList)->m_pHead->m_pNext;
		free((*_ptList)->m_pHead);
		(*_ptList)->m_pHead = (*_ptList)->m_pCurrent;

		(*_ptList)->m_uCount--;

	}
	free(*_ptList);
	*_ptList = NULL;
}

NodeList* GetNodeList(LinkedList** _ptList, string String) {
	NodeList* _NodeList = new NodeList();
	
	(_NodeList)->m_Date = String;

	return _NodeList;
}

Node* GetNode(int _iObject, string String) {
	Node* pNode = new Node();
	pNode->m_pNext = pNode;
	pNode->m_pPrevious = pNode;

	pNode->m_String = String;
	cout << "@@@@@@" << pNode->m_String << endl << endl;
	pNode->m_iObject = _iObject;
	return pNode;
}

//date data read
int Read(LinkedList* _ptList, unsigned int i) {
	int sum_ = 0;
	int sum = 0;
	int sum__ = 0;
	if (!(_ptList)) {
		cout << ("해당리스트는 비어있습니다.\n");

		return 0;				//비어 있으면 종료
	}
	if (_ptList->m_uCount < i) {
		cout << "해당 리스트는 " <<  _ptList->m_uCount<<"개의 날짜들만 갖고있습니다.\n";

		return 0;				//벗어나면 종료
	}
	int count = 0;
	_ptList->m_pCurrent = _ptList->m_pHead;
	while (count < i) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		count++;
	}
	if (_ptList->m_pCurrent->m_uCount == 0) {
		cout << _ptList->m_pCurrent->m_Date << "는 0개의 데이터만 가지고 있습니다." << endl;
		return 0;
	}
	count = 0;
	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
	while (count < _ptList->m_pCurrent->m_uCount) { 
		sum += _ptList->m_pCurrent->m_pCurrent->m_iObject;
		if (_ptList->m_pCurrent->m_pCurrent->m_iObject > 0) {
			sum__ += _ptList->m_pCurrent->m_pCurrent->m_iObject;
		}
		else sum_ += _ptList->m_pCurrent->m_pCurrent->m_iObject;
		cout <<count<<".\t"<<_ptList->m_pCurrent->m_pCurrent->m_String << '\t' << _ptList->m_pCurrent->m_pCurrent->m_iObject << endl;
	
		
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		count++;
	}
	cout << "총액 : " << sum << "," << "\t+ :" << sum__ << "\t- :" << sum_ << endl;
	cout << "--------------------" << _ptList->m_pCurrent->m_Date << "-------------------------" << endl;
	return 1;
}

void Traversal(LinkedList* _ptList) {
	int count = 0;/*
	_ptList->m_pCurrent = _ptList->m_pHead;
	cout <<("순회 시작\n");
	while (count < _ptList->m_uCount) {
		cout <<("%d\n", _ptList->m_pCurrent->m_iObject);
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		count++;
	}
	*/
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");

		return;
	}
	if (!_ptList->m_pHead) { cout << ("Empty\n");; return; }
	int count_2 = 0;
	NodeList* curr = _ptList->m_pHead;

	cout << "총 금액 :" << _ptList->m_Total << endl;


	while (count_2 < _ptList->m_uCount) {
		count = 0;
		cout << ("-----------------------------")<<curr->m_Date<<("----------------------------- ") << endl;
		Node* cur = curr->m_pHead;
		while (count < curr->m_uCount) {
			
			cout << "    "<<cur->m_String << '\t' << cur->m_iObject << endl;
			cur = cur->m_pNext;
			count++;
		}
		cout << ('\n');
		curr = curr->m_pNext;
		count_2++;
	}
	return;
}

void AppendFromHead(LinkedList* _ptList, unsigned int i, int _iObject, string String) {
	if (!_ptList) { cout << ("해당리스트는 비어있습니다.\n");  return; }
	if (i > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount<<("개의 날짜만 갖고있습니다.\n");

		return;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < i; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	_ptList->m_pCurrent->m_pCurrent = GetNode(_iObject, String);
	if (_ptList->m_pCurrent->m_pHead) {
		_ptList->m_pCurrent->m_pCurrent->m_pNext = _ptList->m_pCurrent->m_pHead; // 비어있지 않으면 추가할 노드의 넥스트를  이전의 헤드로
		_ptList->m_pCurrent->m_pHead->m_pPrevious = _ptList->m_pCurrent->m_pCurrent; //이전 헤드의 prev 를 추가할 노드로
	}
	else {
		_ptList->m_pCurrent->m_pTail = _ptList->m_pCurrent->m_pCurrent;			//비어있으면 tail 만 갱신
	}
	_ptList->m_pCurrent->m_pHead = _ptList->m_pCurrent->m_pCurrent;				//관리구조 갱신
	_ptList->m_Total += _iObject;
	(_ptList->m_pCurrent->m_uCount)++;

	return;
}





void AppendFromAllHead(LinkedList* _ptList, int _iObject, string String) {
	if (!_ptList) { cout << ("해당리스트는 비어있습니다.\n");  return; }
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		AppendFromHead(_ptList, i, _iObject, String);
	}
	return;
}


Node* AppendFromTail(LinkedList* _ptList, unsigned int i, int _iObject, string String) {
	if (!_ptList) { cout << ("해당리스트는 비어있습니다.\n");  return NULL; }
	if (i > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");

		return NULL;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < i; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	_ptList->m_pCurrent->m_pCurrent = GetNode(_iObject, String);
	if (_ptList->m_pCurrent->m_pHead) {
		_ptList->m_pCurrent->m_pCurrent->m_pPrevious = _ptList->m_pCurrent->m_pTail; // 비어있지 않으면 추가할 노드의 넥스트를  이전의 tail로
		_ptList->m_pCurrent->m_pTail->m_pNext = _ptList->m_pCurrent->m_pCurrent; //이전 헤드의 next 를 추가할 노드로
	}
	else {
		_ptList->m_pCurrent->m_pHead = _ptList->m_pCurrent->m_pCurrent;			//비어있으면 head 만 갱신
	}
	_ptList->m_pCurrent->m_pTail = _ptList->m_pCurrent->m_pCurrent;				// 관리구조 갱신
	_ptList->m_Total += _iObject;
	(_ptList->m_pCurrent->m_uCount)++;

	return NULL;
}


Node* AppendFromTail_(LinkedList* _ptList, string Date) {
	if (!_ptList) { cout << ("해당리스트는 비어있습니다.\n");  return NULL; }



	_ptList->m_pCurrent = GetNodeList(&_ptList, Date);
	if (_ptList->m_pHead) {
		_ptList->m_pCurrent->m_pPrevious = _ptList->m_pTail; // 비어있지 않으면 추가할 노드의 넥스트를  이전의 tail로
		_ptList->m_pTail->m_pNext = _ptList->m_pCurrent; //이전 헤드의 next 를 추가할 노드로
	}
	else {
		_ptList->m_pHead = _ptList->m_pCurrent;			//비어있으면 head 만 갱신
	}
	_ptList->m_pTail = _ptList->m_pCurrent;				// 관리구조 갱신
	(_ptList->m_uCount)++;

	return NULL;
}


Node* InsertBefore(LinkedList* _ptList, unsigned int k, Node* _ptNode, int Object, string String) {
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return _ptNode;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	int Isin = 0;
	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		if (_ptList->m_pCurrent->m_pCurrent == _ptNode) {
			cout << ("기준 노드 찾음.\n");
			Isin = 1;

		}
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
	}
	if (Isin == 0) {
		cout << ("기준노드 없음\n");

		return _ptNode;

	}

	if (_ptList->m_pCurrent->m_pHead == _ptNode) {
		AppendFromHead(_ptList, k, Object, String);
		return NULL;
	}

	_ptList->m_pCurrent->m_pCurrent = GetNode(Object, String);
	_ptList->m_pCurrent->m_pCurrent->m_pPrevious = _ptNode->m_pPrevious;
	_ptList->m_pCurrent->m_pCurrent->m_pNext = _ptNode;
	_ptList->m_pCurrent->m_pCurrent->m_pPrevious->m_pNext = _ptList->m_pCurrent->m_pCurrent;
	_ptNode->m_pPrevious = _ptList->m_pCurrent->m_pCurrent;
	_ptList->m_Total += Object;
	_ptList->m_uCount++;
	return _ptList->m_pCurrent->m_pCurrent;
}

Node* InsertAfter(LinkedList* _ptList, unsigned int k, Node* _ptNode, int Object, string String) {
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return _ptNode;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");

		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	int Isin = 0;
	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		if (_ptList->m_pCurrent->m_pCurrent == _ptNode) {
			cout << ("기준 노드 찾음.\n");
			Isin = 1;

		}
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
	}
	if (Isin == 0) {
		cout << ("기준노드 없음\n");

		return _ptNode;
	}

	if (_ptList->m_pCurrent->m_pTail == _ptNode) {
		AppendFromTail(_ptList, k, Object, String);
		return NULL;
	}
	_ptList->m_pCurrent->m_pCurrent = GetNode(Object, String);
	_ptList->m_pCurrent->m_pCurrent->m_pNext = _ptNode->m_pNext;
	_ptList->m_pCurrent->m_pCurrent->m_pPrevious = _ptNode;
	_ptList->m_pCurrent->m_pCurrent->m_pNext->m_pPrevious = _ptList->m_pCurrent->m_pCurrent;
	_ptNode->m_pNext = _ptList->m_pCurrent->m_pCurrent;
	_ptList->m_Total += Object;
	_ptList->m_pCurrent->m_uCount++;
	return _ptList->m_pCurrent->m_pCurrent;
}

Node* Insert_Count_Before(LinkedList* _ptList, unsigned int k, int Count, int Object, string String) {
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (_ptList->m_uCount == 0) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	if (Count > _ptList->m_pCurrent->m_uCount) {
		cout <<  _ptList->m_pCurrent->m_Date<<"는 %d 개의 요소만 갖고있습니다.\n";
		return NULL;
	}
	Node* tmp = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < Count; i++) {
		tmp = tmp->m_pNext;
	}
	return(InsertBefore(_ptList, k, tmp, Object, String));
}

Node* Insert_Count_After(LinkedList* _ptList, unsigned int k, int Count, int Object, string String) {
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (_ptList->m_uCount == 0) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	if (Count > _ptList->m_pCurrent->m_uCount) {
		cout << _ptList->m_pCurrent->m_Date << "는 "<<_ptList->m_pCurrent->m_uCount <<"개의 요소만 갖고있습니다.\n";
		return NULL;
	}
	Node* tmp = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < Count; i++) {
		tmp = tmp->m_pNext;
	}
	return(InsertAfter(_ptList, k, tmp, Object, String));
}

Node* DeleteFromHead(LinkedList* _ptList, unsigned int k) {
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (_ptList->m_uCount == 0) {						//비어있으면 리턴
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}

	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	Node* deletedNode;

	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;

	_ptList->m_Total -= _ptList->m_pCurrent->m_pHead->m_iObject;
	_ptList->m_pCurrent->m_pHead = _ptList->m_pCurrent->m_pCurrent->m_pNext;
	_ptList->m_pCurrent->m_pHead->m_pPrevious = _ptList->m_pCurrent->m_pHead;
	(_ptList->m_pCurrent->m_uCount)--;

	if (_ptList->m_pCurrent->m_uCount == 0) {
		_ptList->m_pCurrent->m_pTail = NULL;
		_ptList->m_pCurrent->m_pHead = NULL;
	}
	_ptList->m_pCurrent->m_pCurrent->m_pNext = NULL;
	_ptList->m_pCurrent->m_pCurrent->m_pPrevious = NULL;	//혹시모를 접근 방지

	deletedNode = _ptList->m_pCurrent->m_pCurrent;
	_ptList->m_pCurrent = NULL;					//삭제된 노드 접근불가

	return deletedNode;
}

Node* DeleteFromTail(LinkedList* _ptList, unsigned int k) {
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (_ptList->m_uCount == 0) {						//비어있으면 리턴
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}

	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	Node* deletedNode;

	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pTail;
	_ptList->m_Total -= _ptList->m_pCurrent->m_pTail->m_iObject;

	_ptList->m_pCurrent->m_pTail = _ptList->m_pCurrent->m_pCurrent->m_pPrevious;
	_ptList->m_pCurrent->m_pTail->m_pNext = _ptList->m_pCurrent->m_pTail;
	(_ptList->m_pCurrent->m_uCount)--;
	if (_ptList->m_pCurrent->m_uCount == 0) {
		_ptList->m_pCurrent->m_pHead = NULL;
		_ptList->m_pCurrent->m_pTail = NULL;
	}
	_ptList->m_pCurrent->m_pCurrent->m_pNext = NULL;
	_ptList->m_pCurrent->m_pCurrent->m_pPrevious = NULL;	//혹시모를 접근 방지

	deletedNode = _ptList->m_pCurrent->m_pCurrent;
	_ptList->m_pCurrent->m_pCurrent = NULL;					//삭제된 노드 접근불가

	return deletedNode;
}


Node* Delete(LinkedList* _ptList, Node* _ptNode, unsigned int k) {
	if (!_ptList || !_ptNode) {
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}

	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	Node* deletedNode;
	if (_ptNode == _ptList->m_pCurrent->m_pHead) {
		deletedNode = DeleteFromHead(_ptList, k);
		return deletedNode;
	}
	if (_ptNode == _ptList->m_pCurrent->m_pTail) {
		deletedNode = DeleteFromTail(_ptList, k);
		return deletedNode;
	}
	int count = 0;
	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
	while (_ptNode != _ptList->m_pCurrent->m_pCurrent && count < _ptList->m_pCurrent->m_uCount) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		count++;
	}
	if (count == _ptList->m_pCurrent->m_uCount) {
		cout << ("리스트에서 해당 노드를 찾을 수 없습니다.\n");

		return NULL;
	}
	else {
		_ptList->m_pCurrent->m_pCurrent->m_pPrevious->m_pNext = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		_ptList->m_pCurrent->m_pCurrent->m_pNext->m_pPrevious = _ptList->m_pCurrent->m_pCurrent->m_pPrevious;
		_ptList->m_Total -= _ptList->m_pCurrent->m_pCurrent->m_iObject;
		_ptList->m_pCurrent->m_pCurrent->m_pNext = NULL;
		_ptList->m_pCurrent->m_pCurrent->m_pPrevious = NULL;	//혹시모를 접근 방지

		_ptList->m_pCurrent->m_uCount--;
	}

	deletedNode = _ptList->m_pCurrent->m_pCurrent;
	_ptList->m_pCurrent->m_pCurrent = NULL;					//삭제된 노드 접근불가

	return deletedNode;

}

Node* DeleteNode_Count(LinkedList* _ptList, unsigned int k, int count) {
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}

	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	if (count >= _ptList->m_pCurrent->m_uCount) {
		cout << _ptList->m_pCurrent->m_Date << "는 " << _ptList->m_pCurrent->m_uCount << "개의 요소만 갖고있습니다.\n";
		return NULL;
	}




	Node* tmp = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < count; i++) {
		tmp = tmp->m_pNext;
	}
	return (Delete(_ptList, tmp, k));
}


void DeleteAll(LinkedList* _ptList, unsigned int k) {
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");

		return;
	}
	if (_ptList->m_uCount == 0) {
		cout << ("해당리스트는 비어있습니다.\n");

		return;
	}

	if (k > _ptList->m_uCount) {
		cout << "0 ~" << _ptList->m_uCount -1 << ("사이에서 골라야 합니다.\n");
		return;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	while ((_ptList)->m_pCurrent->m_uCount != 0) {
		(_ptList)->m_pCurrent->m_pCurrent = (_ptList)->m_pCurrent->m_pHead;;
		(_ptList)->m_pCurrent->m_pHead = (_ptList)->m_pCurrent->m_pCurrent->m_pNext;
		_ptList->m_Total -= _ptList->m_pCurrent->m_pCurrent->m_iObject;
		free((_ptList)->m_pCurrent->m_pCurrent);
		(_ptList)->m_pCurrent->m_uCount--;
	}
	_ptList->m_pCurrent->m_pCurrent = NULL;
	_ptList->m_pCurrent->m_pHead = NULL;
	_ptList->m_pCurrent->m_pTail = NULL;
}


NodeList* Delete_k(LinkedList* _ptList,NodeList * _List, unsigned int k) {
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}


	DeleteAll(_ptList, k);

	NodeList * deletedNodeList;
	if (_List == _ptList->m_pHead) {
		NodeList* deletedNode;

		_ptList->m_pCurrent = _ptList->m_pHead;


		_ptList->m_pHead = _ptList->m_pCurrent->m_pNext;
		_ptList->m_pHead->m_pPrevious = _ptList->m_pHead;
		(_ptList->m_uCount)--;
		if (_ptList->m_uCount == 0) {
			_ptList->m_pTail = NULL;
			_ptList->m_pHead = NULL;
		}
		_ptList->m_pCurrent->m_pNext = NULL;
		_ptList->m_pCurrent->m_pPrevious = NULL;	//혹시모를 접근 방지

		deletedNode = _ptList->m_pCurrent;
		_ptList->m_pCurrent = NULL;					//삭제된 노드 접근불가
		free(deletedNode);
		return NULL;
	}
	if (_List == _ptList->m_pTail) {
		NodeList* deletedNode;

		_ptList->m_pCurrent = _ptList->m_pTail;


		_ptList->m_pTail = _ptList->m_pCurrent->m_pPrevious;
		_ptList->m_pTail->m_pNext = _ptList->m_pTail;
		(_ptList->m_uCount)--;
		if (_ptList->m_uCount == 0) {
			_ptList->m_pHead = NULL;
			_ptList->m_pTail = NULL;
		}
		_ptList->m_pCurrent->m_pNext = NULL;
		_ptList->m_pCurrent->m_pPrevious = NULL;	//혹시모를 접근 방지

		deletedNode = _ptList->m_pCurrent;
		_ptList->m_pCurrent = NULL;					//삭제된 노드 접근불가
		free(deletedNode);
		return NULL;
	}
	int count = 0;
	_ptList->m_pCurrent = _ptList->m_pHead;
	while (_List != _ptList->m_pCurrent && count < _ptList->m_uCount) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		count++;
	}
	if (count == _ptList->m_pCurrent->m_uCount) {
		cout << ("리스트에서 해당 노드를 찾을 수 없습니다.\n");

		return NULL;
	}
	else {
		_ptList->m_pCurrent->m_pPrevious->m_pNext = _ptList->m_pCurrent->m_pNext;
		_ptList->m_pCurrent->m_pNext->m_pPrevious = _ptList->m_pCurrent->m_pPrevious;
		
		_ptList->m_pCurrent->m_pNext = NULL;
		_ptList->m_pCurrent->m_pPrevious = NULL;	//혹시모를 접근 방지

		_ptList->m_uCount--;
	}

	deletedNodeList = _ptList->m_pCurrent;
	_ptList->m_pCurrent = NULL;					//삭제된 노드 접근불가

	free(deletedNodeList);
	return NULL;

}


NodeList* DeleteNode_Count_k(LinkedList* _ptList, int count) {
	if (!_ptList) {
		printf("해당리스트는 비어있습니다.\n");

		return NULL;
	}
	if (count > _ptList->m_uCount) {
		printf("해당리스트는 %d 개의 날짜만 가지고 있습니다.\n", _ptList->m_uCount);
		return NULL;
	}
	NodeList* tmp = _ptList->m_pHead;
	for (int i = 0; i < count; i++) {
		tmp = tmp->m_pNext;
	}
	return (Delete_k(_ptList, tmp,count));
}

Node* Modify_Date(LinkedList* _ptList, unsigned int k, string String) {
	if (!_ptList ) {
		cout << ("리스트나 기준노드가 비어있습니다.\n");
		return NULL;
	}
	if (_ptList == NULL) {
		cout << ("리스트나 기준노드가 비어있습니다.\n");
		return NULL;
	}

	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 날짜만 갖고있습니다.\n");
		return NULL;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int i = 0; i < k; i++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	_ptList->m_pCurrent->m_Date = String;

	return _ptList->m_pCurrent->m_pCurrent;
}



Node* Modify(LinkedList* _ptList, Node* _ptNode, unsigned int k, int iObject, string String) {
	if (!_ptList || !_ptNode) {
		cout << ("리스트나 기준노드가 비어있습니다.\n");
		return NULL;
	}
	if (_ptList == NULL || _ptNode == NULL) {
		cout << ("리스트나 기준노드가 비어있습니다.\n");
		return NULL;
	}

	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}


	int count = 0;


	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
	while (_ptNode != _ptList->m_pCurrent->m_pCurrent && count < _ptList->m_pCurrent->m_uCount) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		count++;
	}
	if (count == _ptList->m_uCount) {
		cout << ("해당 노드를 찾을 수 없습니다.\n");
		return NULL;
	}
	else {
		_ptList->m_Total -= _ptList->m_pCurrent->m_pCurrent->m_iObject;
		_ptList->m_Total += iObject;
		_ptList->m_pCurrent->m_pCurrent->m_iObject = iObject;
		_ptList->m_pCurrent->m_pCurrent->m_String = String;
	}
	return _ptList->m_pCurrent->m_pCurrent;
}



Node* Modify_by_Count(LinkedList* _ptList, unsigned int k, int count, int iObject, string String) {
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	if (count > _ptList->m_pCurrent->m_uCount) {
		cout << _ptList->m_pCurrent->m_Date << "는 " << _ptList->m_pCurrent->m_uCount << "개의 요소만 갖고있습니다.\n";
		return NULL;
	}
	Node* tmp = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < count; i++) {
		tmp = tmp->m_pNext;
	}
	return (Modify(_ptList, tmp, k, iObject, String));
}

Node* Modify_String(LinkedList* _ptList, Node* _ptNode, unsigned int k, string String) {
	if (!_ptList || !_ptNode) {
		cout << ("리스트나 기준노드가 비어있습니다.\n");
		return NULL;
	}
	if (_ptList == NULL || _ptNode == NULL) {
		cout << ("리스트나 기준노드가 비어있습니다.\n");
		return NULL;
	}

	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	int count = 0;
	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
	while (_ptNode != _ptList->m_pCurrent->m_pCurrent && count < _ptList->m_pCurrent->m_uCount) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		count++;
	}
	if (count == _ptList->m_pCurrent->m_uCount) {
		cout << ("해당 노드를 찾을 수 없습니다.\n");
		return NULL;
	}
	else {

		_ptList->m_pCurrent->m_pCurrent->m_String = String;
	}
	return _ptList->m_pCurrent->m_pCurrent;
}

Node* Modify_by_Count_String(LinkedList* _ptList, unsigned int k, int count, string String) {
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	if (count > _ptList->m_pCurrent->m_uCount) {
		cout << _ptList->m_pCurrent->m_Date << "는 " << _ptList->m_pCurrent->m_uCount << "개의 요소만 갖고있습니다.\n";
		return NULL;
	}
	Node* tmp = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < count; i++) {
		tmp = tmp->m_pNext;
	}
	return (Modify_String(_ptList, tmp, k, String));
}

Node* Modify_Object(LinkedList* _ptList, Node* _ptNode, unsigned int k, int iObject) {
	if (!_ptList || !_ptNode) {
		cout << ("리스트나 기준노드가 비어있습니다.\n");
		return NULL;
	}
	if (_ptList == NULL || _ptNode == NULL) {
		cout << ("리스트나 기준노드가 비어있습니다.\n");
		return NULL;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}


	int count = 0;
	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
	while (_ptNode != _ptList->m_pCurrent->m_pCurrent && count < _ptList->m_pCurrent->m_uCount) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		count++;
	}
	if (count == _ptList->m_pCurrent->m_uCount) {
		cout << ("해당 노드를 찾을 수 없습니다.\n");
		return NULL;
	}
	else {
		_ptList->m_Total -= _ptList->m_pCurrent->m_pCurrent->m_iObject;
		_ptList->m_Total += iObject;
		_ptList->m_pCurrent->m_pCurrent->m_iObject = iObject;

	}
	return _ptList->m_pCurrent->m_pCurrent;
}

Node* Modify_by_Count_Object(LinkedList* _ptList, unsigned int k, int count, int iObject) {
	if (_ptList == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");
		return NULL;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return NULL;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	if (count > _ptList->m_pCurrent->m_uCount) {
		cout << _ptList->m_pCurrent->m_Date << "는 " << _ptList->m_pCurrent->m_uCount << "개의 요소만 갖고있습니다.\n";
		return NULL;
	}

	Node* tmp = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < count; i++) {
		tmp = tmp->m_pNext;
	}
	return (Modify_Object(_ptList, tmp, k, iObject));
}

Node* LinearSearchByUnique(LinkedList* _ptList, int Object, string String) {

	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}

	if (_ptList->m_pHead == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
		for (int j = 0; j < _ptList->m_pCurrent->m_uCount; j++) {
			if (_ptList->m_pCurrent->m_pCurrent->m_iObject == Object && _ptList->m_pCurrent->m_pCurrent->m_String == String) {
				cout << _ptList->m_pCurrent->m_Date << "의 " << j << "번째에 있습니다.\n";
				return _ptList->m_pCurrent->m_pCurrent;
			}
			_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	cout << ("%d 리스트 내에 없습니다.\n", Object);

	return NULL;


}
/*
Node* LinearSearchByUnique_String(LinkedList* _ptList, char* String) {

	if (!_ptList) {
		cout <<("해당리스트는 비어있습니다.\n");

		return NULL;
	}

	if (_ptList->m_pHead == NULL) {
		cout <<("해당리스트는 비어있습니다.\n");

		return NULL;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int i = 0; i < _ptList->m_uCount; i++) {

		if (strcmp(_ptList->m_pCurrent->m_String, String) ==0) {
			//Node* RTN = (Node*)malloc(sizeof(Node*));
			Node* RTN;
			cout <<("%d 번째에 있습니다.\n", i);
			cout <<("%s\t%d\n", String, _ptList->m_pCurrent->m_iObject);
			RTN = _ptList->m_pCurrent;
			return RTN;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	cout <<("%s 리스트 내에 없습니다.\n", String);

	return NULL;


}
*/
Node* LinearSearchByUnique_Object(LinkedList* _ptList, int Object) {

	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}

	if (_ptList->m_pHead == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");

		return NULL;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
		for (int j = 0; j < _ptList->m_pCurrent->m_uCount; j++) {
			if (_ptList->m_pCurrent->m_pCurrent->m_iObject == Object) {
				cout << _ptList->m_pCurrent->m_Date << "의 " << j << "번째에 있습니다.\n";
				return _ptList->m_pCurrent->m_pCurrent;
			}
			_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	cout << ("%d 리스트 내에 없습니다.\n", Object);

	return NULL;


}

void LinearSearchByDuplicate(LinkedList* _ptList, int Object, string String, int* _resultSize, Node*** _resultArray) {
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");
		return;
	}
	if (_ptList->m_pHead == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");

		return;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	int Match_Count = 0;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
		for (int j = 0; j < _ptList->m_pCurrent->m_uCount; j++) {

			if (_ptList->m_pCurrent->m_pCurrent->m_iObject == Object && _ptList->m_pCurrent->m_pCurrent->m_String.find(String) != std::string::npos) {
				if (i % 4 == 0) {
					cout << ("\n");
				}
				cout << _ptList->m_pCurrent->m_Date << "의 " << j << "번째에 있습니다.\n";
				cout << _ptList->m_pCurrent->m_pCurrent->m_String<<'\t' << _ptList->m_pCurrent->m_pCurrent->m_iObject;
				Match_Count++;

			}

			_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		}

		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}



	cout << ("\n");
	if (Match_Count == 0) {
		cout << String << '\t' << Object;
		return;						// 없을 경우
	}


	*_resultSize = Match_Count;
	/*
	*_resultArray = (Node**)calloc(Match_Count, sizeof(Node*));	//수만큼 동적 할당
	_ptList->m_pCurrent = _ptList->m_pHead;

	Match_Count = 0;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		if (_ptList->m_pCurrent->m_iObject == Object) {
			(*_resultArray)[Match_Count++] = _ptList->m_pCurrent;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	*/
}

void LinearSearchByDuplicate_Object(LinkedList* _ptList, int Object, int* _resultSize, Node*** _resultArray) {
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");
		return;
	}
	if (_ptList->m_pHead == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");

		return;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	int Match_Count = 0;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
		for (int j = 0; j < _ptList->m_pCurrent->m_uCount; j++) {

			if (_ptList->m_pCurrent->m_pCurrent->m_iObject == Object) {
				if (i % 4 == 0) {
					cout << ("\n");
				}
				cout << _ptList->m_pCurrent->m_Date << "의 " << j << "번째에 있습니다.\n";
				cout << _ptList->m_pCurrent->m_pCurrent->m_String << '\t' << _ptList->m_pCurrent->m_pCurrent->m_iObject;
				Match_Count++;

			}

			_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		}

		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	cout << ("\n");
	if (Match_Count == 0) {
		cout << ("%d 리스트 내에 없습니다.\n", Object);
		return;						// 없을 경우
	}


	*_resultSize = Match_Count;
	/*
	*_resultArray = (Node**)calloc(Match_Count, sizeof(Node*));	//수만큼 동적 할당
	_ptList->m_pCurrent = _ptList->m_pHead;

	Match_Count = 0;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		if (_ptList->m_pCurrent->m_iObject == Object) {
			(*_resultArray)[Match_Count++] = _ptList->m_pCurrent;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	*/
}

void LinearSearchByDuplicate_KyeWord_String(LinkedList* _ptList, string String, int* _resultSize, Node*** _resultArray) {
	if (!_ptList) {
		cout << ("해당리스트는 비어있습니다.\n");
		return;
	}
	if (_ptList->m_pHead == NULL) {
		cout << ("해당리스트는 비어있습니다.\n");

		return;
	}
	_ptList->m_pCurrent = _ptList->m_pHead;
	int Match_Count = 0;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
		for (int j = 0; j < _ptList->m_pCurrent->m_uCount; j++) {

			if (_ptList->m_pCurrent->m_pCurrent->m_String.find(String) != std::string::npos) {
				if (i % 4 == 0) {
					cout << ("\n");
				}
				cout << _ptList->m_pCurrent->m_Date << "의 " << j << "번째에 있습니다.\n";
				cout << _ptList->m_pCurrent->m_pCurrent->m_String << '\t' << _ptList->m_pCurrent->m_pCurrent->m_iObject;
				Match_Count++;

			}

			_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
		}

		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	cout << ("\n");
	if (Match_Count == 0) {
		cout << String<< "리스트 내에 없습니다.\n";
		return;						// 없을 경우
	}


	*_resultSize = Match_Count;
	/*
	*_resultArray = (Node**)calloc(Match_Count, sizeof(Node*));	//수만큼 동적 할당
	_ptList->m_pCurrent = _ptList->m_pHead;

	Match_Count = 0;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		if (_ptList->m_pCurrent->m_iObject == Object) {
			(*_resultArray)[Match_Count++] = _ptList->m_pCurrent;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	*/
}

/*

Node* BinarySearchByUnique_ObjectSorted(LinkedList* _ptList, int Object) {
	if (!_ptList) {
		cout <<("해당리스트는 비어있습니다.\n");

		return NULL;

	}
	if (_ptList->m_pHead == NULL) {
		cout <<("해당리스트는 비어있습니다.\n");

		return NULL;
	}
	int FoundFlag = 0;
	int Start = 0;
	int End = _ptList->m_uCount;
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		if (_ptList->m_pCurrent->m_iObject > _ptList->m_pCurrent->m_pNext->m_iObject) {
			cout <<("정렬되지 않은 리스트 입니다.\n");
			return;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	_ptList->m_pCurrent = NULL;
	while (Start <= End) {

		int Mid = (Start + End) / 2;
		_ptList->m_pCurrent = _ptList->m_pHead;
		for (int i = 0; i < Mid; i++) {
			_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		}

		if (Object == _ptList->m_pCurrent->m_iObject) {
			FoundFlag = 1;
			cout <<("%d :", Mid);
			cout <<("%s\t%d\n", _ptList->m_pCurrent->m_String, _ptList->m_pCurrent->m_iObject);
			break;
		}
		if (Object < _ptList->m_pCurrent->m_iObject) {
			End = Mid - 1;
		}
		else {
			Start = Mid + 1;
		}

	}
	if (FoundFlag == 0) {
		cout <<("%d 리스트 내에 없습니다.\n", Object);

		return NULL;
	}
	Node* RTN = _ptList->m_pCurrent;
	_ptList->m_pCurrent = NULL;
	return RTN;
}

Node* BinarySearchByUnique_StringSorted(LinkedList* _ptList, int Object,char* String) {
	if (!_ptList) {
		cout <<("해당리스트는 비어있습니다.\n");

		return NULL;

	}
	if (_ptList->m_pHead == NULL) {
		cout <<("해당리스트는 비어있습니다.\n");

		return NULL;
	}
	int FoundFlag = 0;
	int Start = 0;
	int End = _ptList->m_uCount;
	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int i = 0; i < _ptList->m_uCount; i++) {
		if (strcmp(_ptList->m_pCurrent->m_String, _ptList->m_pCurrent->m_pNext->m_String)>0) {
			cout <<("정렬되지 않은 리스트 입니다.\n");
			return;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}

	_ptList->m_pCurrent = NULL;
	while (Start <= End) {

		int Mid = (Start + End) / 2;
		_ptList->m_pCurrent = _ptList->m_pHead;
		for (int i = 0; i < Mid; i++) {
			_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		}

		if (strcmp(_ptList->m_pCurrent->m_String,String)==0) {
			FoundFlag = 1;
			cout <<("%d :", Mid);
			cout <<("%s\t%d\n", _ptList->m_pCurrent->m_String, _ptList->m_pCurrent->m_iObject);
			break;
		}
		if (Object < _ptList->m_pCurrent->m_iObject) {
			End = Mid - 1;
		}
		else {
			Start = Mid + 1;
		}

	}
	if (FoundFlag == 0) {
		cout <<("%d 리스트 내에 없습니다.\n", Object);

		return NULL;
	}
	Node* RTN = _ptList->m_pCurrent;
	_ptList->m_pCurrent = NULL;
	return RTN;
}

void dfs(LinkedList* _ptList, int start, int end) {
	if (start > end)return;
	cout <<("%d :%s\t%d \n", (start + end) / 2);



	dfs(_ptList, start, (start + end) / 2 - 1);
	dfs(_ptList, (start + end) / 2 + 1, end);
}

void BinarySearchByDuplicate_Object(LinkedList* _ptList, int Object, int* _resultSize, Node*** _resultArray) {
	if (!_ptList) {
		cout <<("해당리스트는 비어있습니다.\n");

		return;
	}
	if (_ptList->m_pHead == NULL) {
		cout <<("해당리스트는 비어있습니다.\n");

		return;
	}
	int FoundFlag = 0;
	int Start = 0;
	int End = _ptList->m_uCount;
	_ptList->m_pCurrent = _ptList->m_pHead;

	for (int i = 0; i < _ptList->m_uCount; i++) {
		if (_ptList->m_pCurrent->m_iObject > _ptList->m_pCurrent->m_pNext->m_iObject) {
			cout <<("정렬되지 않은 리스트 입니다.\n");
			return;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	_ptList->m_pCurrent = NULL;
	int S_tmp = 0;

	//cout <<("\n가장 왼쪽 요소 찾기 시작.\n");
	while (Start < End) {


		int Mid = (Start + End) / 2;

		_ptList->m_pCurrent = _ptList->m_pHead;
		for (int i = 0; i < Mid; i++) {
			_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		}

		if (Object == _ptList->m_pCurrent->m_iObject && FoundFlag == 0) {
			FoundFlag = 1;


		}
		if (Object <= _ptList->m_pCurrent->m_iObject) {
			End = Mid;
			if (Object == _ptList->m_pCurrent->m_iObject) {
				//cout <<("%d ", Mid);
			}
		}
		else {
			Start = Mid + 1;
		}
	}
	S_tmp = Start;
	//cout <<("\n가장 오른쪽 요소 찾기 시작.\n");
	Start = 0;
	End = _ptList->m_uCount;
	Node* Prev_tmp = NULL;
	while (Start < End) {


		int Mid = (Start + End) / 2;

		_ptList->m_pCurrent = _ptList->m_pHead;
		for (int i = 0; i < Mid; i++) {
			_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		}


		if (Object == _ptList->m_pCurrent->m_iObject && FoundFlag == 0) {
			FoundFlag = 1;


		}
		if (Object >= _ptList->m_pCurrent->m_iObject) {
			Start = Mid;
			if (Object == _ptList->m_pCurrent->m_iObject) {
				//cout <<("%d ", Mid);
			}
		}
		else {
			End = Mid - 1;
		}
		if (Prev_tmp == _ptList->m_pCurrent) {
			if (_ptList->m_pCurrent->m_pNext->m_iObject == Object) {
				if (_ptList->m_pTail != _ptList->m_pCurrent) {
					Start = Mid + 1;
					break;
				}
			}
			Start = Mid;
			break;
		}
		Prev_tmp = _ptList->m_pCurrent;
	}

	if (FoundFlag == 0) {
		cout <<("%d 은(는) 리스트 내에 없습니다.\n", Object);

		return;
	}

	//cout <<("%d\n", Start);
	dfs(_ptList, S_tmp, Start);
	cout <<("\n-%d- 이 있는 범위 : %d~%d   \n", Object, S_tmp, Start);
	*_resultSize = Start - S_tmp + 1;
	cout <<("%d 개 찾음\n", *_resultSize);
	int Found_Count = 0;
	int resultS = S_tmp;
	int resultE = Start;
	int resultMid = (S_tmp + Start) / 2;

	//*_resultArray = (Node**)calloc(*_resultSize, sizeof(Node*));	//수만큼 동적 할당

	//_ptList->m_pCurrent = _ptList->m_pHead;
	/*
	int Count = 0;
	int i = 0;
	while (Count < _ptList->m_uCount) {
		if (Count >= Start && Count <= End) {
			(*_resultArray)[i++] = _ptList->m_pCurrent;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		Count++;
	}
	*/
	/*
		_ptList->m_pCurrent = NULL;
		return;

	}

	void BinarySearchByDuplicate_String(LinkedList* _ptList, int Object,char* String, int* _resultSize, Node*** _resultArray) {
		if (!_ptList) {
			cout <<("해당리스트는 비어있습니다.\n");

			return;
		}
		if (_ptList->m_pHead == NULL) {
			cout <<("해당리스트는 비어있습니다.\n");

			return;
		}
		int FoundFlag = 0;
		int Start = 0;
		int End = _ptList->m_uCount;
		_ptList->m_pCurrent = _ptList->m_pHead;

		for (int i = 0; i < _ptList->m_uCount; i++) {
			if (strcmp(_ptList->m_pCurrent->m_String, _ptList->m_pCurrent->m_pNext->m_String) > 0) {
				cout <<("문자열 기준으로 정렬되지 않은 리스트 입니다.\n");
				return;
			}
			_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		}
		_ptList->m_pCurrent = NULL;
		int S_tmp = 0;

		//cout <<("\n가장 왼쪽 요소 찾기 시작.\n");
		while (Start < End) {


			int Mid = (Start + End) / 2;

			_ptList->m_pCurrent = _ptList->m_pHead;
			for (int i = 0; i < Mid; i++) {
				_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
			}

			if (strcmp(String,_ptList->m_pCurrent->m_String)==0 && FoundFlag == 0) {
				FoundFlag = 1;


			}
			if (strcmp(String , _ptList->m_pCurrent->m_String)<=0) {
				End = Mid;
				//if (Object == _ptList->m_pCurrent->m_iObject) {
					//cout <<("%d ", Mid);
				//}
			}
			else {
				Start = Mid + 1;
			}
		}
		S_tmp = Start;
		//cout <<("\n가장 오른쪽 요소 찾기 시작.\n");
		Start = 0;
		End = _ptList->m_uCount;
		Node* Prev_tmp = NULL;
		while (Start < End) {


			int Mid = (Start + End) / 2;

			_ptList->m_pCurrent = _ptList->m_pHead;
			for (int i = 0; i < Mid; i++) {
				_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
			}


			if (strcmp(String, _ptList->m_pCurrent->m_String) == 0 && FoundFlag == 0 && FoundFlag == 0) {
				FoundFlag = 1;


			}
			if (strcmp(String , _ptList->m_pCurrent->m_String)>=0) {
				Start = Mid;
				if (Object == _ptList->m_pCurrent->m_iObject) {
					//cout <<("%d ", Mid);
				}
			}
			else {
				End = Mid - 1;
			}
			if (Prev_tmp == _ptList->m_pCurrent) {
				if (_ptList->m_pCurrent->m_pNext->m_iObject == Object) {
					if (_ptList->m_pTail != _ptList->m_pCurrent) {
						Start = Mid + 1;
						break;
					}
				}
				Start = Mid;
				break;
			}
			Prev_tmp = _ptList->m_pCurrent;
		}

		if (FoundFlag == 0) {
			cout <<("%s 은(는) 리스트 내에 없습니다.\n", String);

			return;
		}

		//cout <<("%d\n", Start);
		dfs(_ptList, S_tmp, Start);
		cout <<("\n-%d- 이 있는 범위 : %d~%d   \n", Object, S_tmp, Start);
		*_resultSize = Start - S_tmp + 1;
		cout <<("%d 개 찾음\n", *_resultSize);
		int Found_Count = 0;
		int resultS = S_tmp;
		int resultE = Start;
		int resultMid = (S_tmp + Start) / 2;

		//*_resultArray = (Node**)calloc(*_resultSize, sizeof(Node*));	//수만큼 동적 할당

		//_ptList->m_pCurrent = _ptList->m_pHead;
		/*
		int Count = 0;
		int i = 0;
		while (Count < _ptList->m_uCount) {
			if (Count >= Start && Count <= End) {
				(*_resultArray)[i++] = _ptList->m_pCurrent;
			}
			_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
			Count++;
		}
		*/
		/*
			_ptList->m_pCurrent = NULL;
			return;

		}
		*/
void Change(LinkedList* _ptList, unsigned int k, Node* _ptNode1, Node* _ptNode2) {
	if (!_ptList || !_ptNode1 || !_ptNode2 || _ptNode1 == _ptNode2) return;


	int Node1_flag = 0, Node2_flag = 0;

	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 요소만 갖고있습니다.\n");
		return;
	}

	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}


	_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
	for (int i = 0; i < _ptList->m_pCurrent->m_uCount; i++) {
		if (Node1_flag == 1 && Node2_flag == 1) break;
		if (_ptList->m_pCurrent->m_pCurrent == _ptNode1)  Node1_flag = 1;
		if (_ptList->m_pCurrent->m_pCurrent == _ptNode2)  Node2_flag = 1;
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;

	}

	if (Node1_flag != 1 || Node2_flag != 1) {
		cout << ("두 노드를 같은 리스트에서 찾을 수 없습니다.\n");
		return;
	}

	Node* Prev1 = _ptNode1->m_pPrevious;
	Node* Next1 = _ptNode1->m_pNext;
	Node* Prev2 = _ptNode2->m_pPrevious;
	Node* Next2 = _ptNode2->m_pNext;


	if (_ptNode1 == _ptList->m_pCurrent->m_pHead) {			//1이 헤드
		_ptList->m_pCurrent->m_pHead = _ptNode2;


		Prev1 = _ptNode2;


	}
	else if (_ptNode2 == _ptList->m_pCurrent->m_pHead) {		//2가 헤드 
		_ptList->m_pCurrent->m_pHead = _ptNode1;

		Prev2 = _ptNode1;


	}
	if (_ptNode1 == _ptList->m_pCurrent->m_pTail) {
		_ptList->m_pCurrent->m_pTail = _ptNode2;

		Next1 = _ptNode2;


	}
	else if (_ptNode2 == _ptList->m_pCurrent->m_pTail) {
		_ptList->m_pCurrent->m_pTail = _ptNode1;

		Next2 = _ptNode1;


	}

	if (_ptNode1->m_pNext == _ptNode2) { //붙어있을
		Prev2 = _ptNode2;
		Next1 = _ptNode1;
	}

	if (_ptNode2->m_pNext == _ptNode1) {	//붙어있을때
		Prev1 = _ptNode1;
		Next2 = _ptNode2;
	}

	Next2->m_pPrevious = _ptNode1;
	Prev2->m_pNext = _ptNode1;
	Next1->m_pPrevious = _ptNode2;
	Prev1->m_pNext = _ptNode2;
	_ptNode1->m_pNext = Next2;
	_ptNode1->m_pPrevious = Prev2;

	_ptNode2->m_pNext = Next1;
	_ptNode2->m_pPrevious = Prev1;


}




void SortBySelection_Object(LinkedList* _ptList) {
	if (!_ptList) {
		cout << ("해당 리스트는 비어있습니다.\n");
		return;
	}
	if (_ptList->m_uCount == 0) {
		return;									//정렬이 필요없는 경우
	}
	int Sorted_Index = 0;
	int count = 0; 
	Node* Least;

	_ptList->m_pCurrent = _ptList->m_pHead;

	while (count < _ptList->m_uCount) {
		
		while (Sorted_Index < _ptList->m_pCurrent->m_uCount) {
			Least = _ptList->m_pCurrent->m_pHead;


			for (int i = 0; i < Sorted_Index; i++) {
				Least = Least->m_pNext;
			}

			Node* Bottom = Least;

			_ptList->m_pCurrent->m_pCurrent = Least->m_pNext;

			for (int i = Sorted_Index; i < _ptList->m_pCurrent->m_uCount; i++) {
				if (Least->m_iObject > _ptList->m_pCurrent->m_pCurrent->m_iObject) {
					Least = _ptList->m_pCurrent->m_pCurrent;

				}
				_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
			}

			Change(_ptList, count, Least, Bottom);
			Sorted_Index++;
		}
		Sorted_Index = 0;
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		count++;
	}
}

void SortBySelection_String(LinkedList* _ptList) {
	if (!_ptList) {
		cout << ("해당 리스트는 비어있습니다.\n");
		return;
	}
	if (_ptList->m_uCount == 0) {
		return;									//정렬이 필요없는 경우
	}
	int Sorted_Index = 0;

	Node* Least;
	int count = 0;



	while (count < _ptList->m_uCount) {
		_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pHead;
		while (Sorted_Index < _ptList->m_pCurrent->m_uCount) {
			Least = _ptList->m_pCurrent->m_pHead;


			for (int i = 0; i < Sorted_Index; i++) {
				Least = Least->m_pNext;
			}

			Node* Bottom = Least;

			_ptList->m_pCurrent->m_pCurrent = Least->m_pNext;

			for (int i = Sorted_Index; i < _ptList->m_pCurrent->m_uCount; i++) {
				if (Least->m_String > _ptList->m_pCurrent->m_pCurrent->m_String) {
					Least = _ptList->m_pCurrent->m_pCurrent;

				}
				_ptList->m_pCurrent->m_pCurrent = _ptList->m_pCurrent->m_pCurrent->m_pNext;
			}

			Change(_ptList, count, Least, Bottom);
			Sorted_Index++;
		}
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
		count++;
	}
}



void Merger(LinkedList* _ptList, unsigned int i, unsigned int k) {
	if (!_ptList) { cout << ("해당리스트는 비어있습니다.\n");  return; }
	if (i == k) {
		cout << "자신과 합칠 수는 없습니다." << endl;
		return;
	}
	if (i > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 날짜만 갖고있습니다.\n");

		return;
	}
	if (k > _ptList->m_uCount) {
		cout << ("해당 리스트는") << _ptList->m_uCount << ("개의 날짜만 갖고있습니다.\n");

		return;
	}


	_ptList->m_pCurrent = _ptList->m_pHead;
	for (int j = 0; j < k; j++) {
		_ptList->m_pCurrent = _ptList->m_pCurrent->m_pNext;
	}
	NodeList* tmp = _ptList->m_pCurrent;
	int ct = tmp->m_uCount;
	Node* Nodetmp = tmp->m_pHead;
	for (int j = 0; j < ct; j++) {
		AppendFromTail(_ptList, i, Nodetmp->m_iObject, Nodetmp->m_String);
		Nodetmp = Nodetmp->m_pNext;
	}

	DeleteNode_Count_k(_ptList, k);

		return;
}