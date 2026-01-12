#define _CRT_SECURE_NO_WARNINGS
#include <iostream>
#include<string>
#include <stdlib.h>
#include "LinkedList_int.h"
#include <CoreWindow.h>
#include <windows.h>
#include <limits.h>
#define Max 10
using namespace std;

void AppendFromAllHead(LinkedList* _ptList, int _iObject, string String);
void Create(LinkedList** _ptList);
void Destroy(LinkedList** _ptList);
NodeList* GetNodeList(LinkedList** _NodeList, string String);
Node* GetNode(int _iObject, string String);
int Read(LinkedList* _ptList, unsigned int i);
void Traversal(LinkedList* _ptList);
void AppendFromHead(LinkedList* _ptList, unsigned int i, int _iObject, string String);
Node* AppendFromTail(LinkedList* _ptList, unsigned int i, int _iObject, string String);
Node* AppendFromTail_(LinkedList* _ptList, string Date);
Node* InsertBefore(LinkedList* _ptList, unsigned int k, Node* _ptNode, int Object, string String);
Node* InsertAfter(LinkedList* _ptList, unsigned int k, Node* _ptNode, int Object, string String);
Node* Insert_Count_Before(LinkedList* _ptList, unsigned int k, int Count, int Object, string String);
Node* Insert_Count_After(LinkedList* _ptList, unsigned int k, int Count, int Object, string String);
Node* DeleteFromHead(LinkedList* _ptList, unsigned int k);
Node* DeleteFromTail(LinkedList* _ptList, unsigned int k);
Node* Delete(LinkedList* _ptList, Node* _ptNode, unsigned int k);
Node* DeleteNode_Count(LinkedList* _ptList, unsigned int k, int count);
void DeleteAll(LinkedList* _ptList, unsigned int k);
Node* Modify(LinkedList* _ptList, Node* _ptNode, unsigned int k, int iObject, string String);
Node* Modify_String(LinkedList* _ptList, Node* _ptNode, unsigned int k, string String);
Node* Modify_by_Count_String(LinkedList* _ptList, unsigned int k, int count, string String);
Node* Modify_Object(LinkedList* _ptList, Node* _ptNode, unsigned int k, int iObject);
Node* Modify_by_Count_Object(LinkedList* _ptList, unsigned int k, int count, int iObject);
void LinearSearchByDuplicate_KyeWord_String(LinkedList* _ptList, string String, int* _resultSize, Node*** _resultArray);
void Merger(LinkedList* _ptList, unsigned int i, unsigned int k);
void SortBySelection_Object(LinkedList* _ptList);
void SortBySelection_String(LinkedList* _ptList);
NodeList* DeleteNode_Count_k(LinkedList* _ptList, int count);
Node* Modify_by_Count(LinkedList* _ptList, unsigned int k, int count, int iObject, string String);
Node* Modify_Date(LinkedList* _ptList, unsigned int k, string String);
void cur(short x, short y)		//화면의 원하는 x, y좌표로 보냄
{
	COORD pos = { x, y };
	SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
}





int main() {

	long long L = (-2147483647 - 1);
	int R = 2147483647;
	char Cont;
	int flag = 0;
	LinkedList* Lists = { NULL };
	string String = "asdfsa";
	long long Num_tmp = 0;
	long long Num_tmp2 = 0;
	long long Num_tmp3 = 0;
	Node* Node_tmp = NULL;
	int SearchResultSize;
	Node** SearchSortResultArr;
	COORD pos = { 0,0 };
	int k = 0;
	Create(&Lists);

	while (flag == 0) {



		int Selection_flag = 0;
		int selection_flag2 = 0;

		printf("내부 구성//// 리스트(관리구조) -> 날짜(디렉터리) -> 항목(데이터)////");
		printf("\n\n");
		long long Num_tmp = 0;
		long long Num_tmp2 = 0;
		long long Num_tmp3 = 0;
		if (!Node_tmp) Node_tmp == NULL;

		printf("날짜(디렉터리)들 _-----------------------------------------------\n");

		if (Lists != NULL) {
			int count = 0;
			printf("\n");
			if (!Lists->m_pHead) { printf("Empty"); }
			NodeList* curr = Lists->m_pHead;
			while (count < Lists->m_uCount) {

				cout << endl << curr->m_Date << "  _  " << curr->m_uCount;
				curr = curr->m_pNext;
				count++;
			}
			printf("\n\n");
			cout << "총액 :" << Lists->m_Total<<endl<<"------------------------------------------------------------------------------"<<endl;
		}
		else printf("\n@ \n----------------------------------------------------------------------------------------------------");


		

		cout << "1. 추가  2. 삭제. 3. 탐색  4. 변형" << endl;
		printf("\n\n->");

		int err = scanf("%d", &selection_flag2);
		if (err != 1) {

			printf("\n잘못된 입력\n");
			Sleep(300);
			while (getchar() != '\n') {}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			continue;

		}

		printf("\n\n");


		if (selection_flag2 != 1 && selection_flag2 != 2 && selection_flag2 != 3 && selection_flag2 != 4) { 
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			continue; }
		if (selection_flag2 == 1) {
			printf("---------------------------------------------------------------------------\n0. 관리 구조 생성\t\t1. 항목 헤드에 추가\t\t2. 항목 테일에 추가\n");
			printf("\n3. 원하는 위치 앞에 추가\t4. 원하는 위치 뒤 삽입\t\t5. 날짜 생성\t\t6. 모든 날짜에 항목 추가\n---------------------------------------------------------------------------\n");
		}
		if (selection_flag2 == 2) {
			printf("---------------------------------------------------------------------------\n1. 원하는 날짜의 앞 항목 삭제\t\t2.원하는 날짜의 뒤 항목 삭제\n");
			printf("3. 임의 항목 삭제\t\t4. 날짜 초기화\t5. 날짜 삭제\n---------------------------------------------------------------------------\n");
		}
		if (selection_flag2 == 3) {
			printf("---------------------------------------------------------------------------\n1. 원하는 날짜 읽기\t\t2. 전체 값 읽기\t\t3. 검색\n---------------------------------------------------------------------------\n");
		}
		if (selection_flag2 == 4) {
			printf("---------------------------------------------------------------------------\n1. 항목 수정\t\t2. 항목의 목적 수정\t\t3. 항목의 금액 수정\n4. 날짜 수정\t\t5. 금액 기준 정렬\t\t6. 날짜 병합\n---------------------------------------------------------------------------\n");
		}






		int Selection = -1;

		printf("\n기능 선택:");
		err = scanf("%d", &Selection);
		if (err != 1) {

			printf("\n잘못된 입력\n");
			Sleep(300);
			while (getchar() != '\n') {}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			continue;

		}

		printf("\n\n");
		if (Selection == 0 && selection_flag2 == 1) {
			Selection_flag = 1;
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);


			if (Lists == NULL) {
				Create(&Lists);



			}



			else { printf("이미 리스트는 존재합니다.\n"); }
			continue;
		}

		if (Selection == 5 && selection_flag2 == 1) {
			Selection_flag = 1;
			
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			printf("새로 생성할 날짜를 입력:");
			std::getline(cin, String);

			Lists->m_pCurrent = Lists->m_pHead;
			for (int i = 0; i < Lists->m_uCount; i++) {
				if (Lists->m_pCurrent->m_Date == String) {
					printf("이미 존재하는 날짜입니다.\n");
					continue;
				}
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			AppendFromTail_(Lists, String);


			continue;
		}

		if (Selection == 1 && selection_flag2 == 1) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << "." << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째에 추가 ? :");

			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}



			printf("금액 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp2 >= INT_MIN && Num_tmp2 <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			printf("목적은? :");
			std::getline(cin, String);

			if (Lists != NULL) {
				AppendFromHead(Lists, k, Num_tmp2, String);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}
		}

		if (Selection == 6 && selection_flag2 == 1) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			


			printf("금액 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp2 >= INT_MIN && Num_tmp2 <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			printf("목적은? :");
			std::getline(cin, String);

			if (Lists != NULL) {
				AppendFromAllHead(Lists, Num_tmp2, String);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}
		}

		if (Selection == 2 && selection_flag2 == 1) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째에 추가 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}



			printf("금액 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp2 >= INT_MIN && Num_tmp2 <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			printf("목적은? :");
			std::getline(cin, String);

			if (Lists != NULL) {
				AppendFromTail(Lists, k, Num_tmp2, String);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}
		}

		if (Selection == 1 && selection_flag2 == 3) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("생성된 날짜가 없습니다..\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n읽을 날짜는 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Read(Lists, k);
			cout << "\n---------------------------------------------------------------------------\n";



		}
		if (Selection == 2 && selection_flag2 == 3) {
			Selection_flag = 1;

			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Traversal(Lists);
			continue;
		}

		if (Selection == 3 && selection_flag2 == 1) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째에 추가 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			if (Read(Lists, k) == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue; }
			cout << "\n---------------------------------------------------------------------------\n";
			printf("몇번 앞에 추가 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp >= INT_MIN && Num_tmp <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}



			printf("금액 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp2 >= INT_MIN && Num_tmp2 <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			printf("목적은? :");
			std::getline(cin, String);

			if (Lists != NULL) {
				Insert_Count_Before(Lists, k, Num_tmp, Num_tmp2, String);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}
		}



		if (Selection == 4 && selection_flag2 == 1) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째 날짜 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			cout << "\n---------------------------------------------------------------------------\n";
			if (Read(Lists, k) == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("몇번째 항목 뒤에 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp >= INT_MIN && Num_tmp <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}

			printf("금액 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp2 >= INT_MIN && Num_tmp2 <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			printf("목적은? :");
			std::getline(cin, String);

			if (Lists != NULL) {
				Insert_Count_After(Lists, k, Num_tmp, Num_tmp2, String);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}

		}

		if (Selection == 1 && selection_flag2 == 2) {
			Selection_flag = 1;

			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째의 앞을 삭제 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}

			DeleteFromHead(Lists, k);
		}
		if (Selection == 2 && selection_flag2 == 1) {
			Selection_flag = 1;

			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째의 뒤를 삭제 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}

			DeleteFromTail(Lists, k);
			continue;
		}
		//원하는 위치의 항목 삭제
		if (Selection == 3 && selection_flag2 == 2) {
			Selection_flag = 1;

			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n 삭제할 항목이 있는 날짜 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			cout << "\n---------------------------------------------------------------------------\n";
			if (Read(Lists, k) == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n 몇번째 항목을 삭제 ? :");
			err = scanf("%d", &Num_tmp2);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}

			DeleteNode_Count(Lists, k, Num_tmp2);
			continue;
		}

		if (Selection == 4 && selection_flag2 == 2) {
			Selection_flag = 1;

			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n 초기화 할 날짜 ?:");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}



			DeleteAll(Lists, k);
			continue;

		}

		if (Selection == 5 && selection_flag2 == 2) {
			Selection_flag = 1;

			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째 날짜를 삭제 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}

			DeleteNode_Count_k(Lists, k);
		}

		if (Selection == 1 && selection_flag2 == 4) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째 날짜 수정 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			cout << "\n---------------------------------------------------------------------------\n";
			if (Read(Lists, k) == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("몇번째 항목을 수정 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp >= INT_MIN && Num_tmp <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}

			printf("금액 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp2 >= INT_MIN && Num_tmp2 <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			printf("목적은? :");
			getline(cin, String);

			if (Lists != NULL) {
				Modify_by_Count(Lists, k, Num_tmp, Num_tmp2, String);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}
		}

		if (Selection == 2 && selection_flag2 == 4) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째 날짜 수정 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			cout << "\n---------------------------------------------------------------------------\n";
			if (Read(Lists, k) == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("몇번째 항목을 수정 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp >= INT_MIN && Num_tmp <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}

			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};

			printf("수정할 목적은? :");
			std::getline(cin, String);

			if (Lists != NULL) {
				Modify_by_Count_String(Lists, k, Num_tmp, String);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}
		}

		if (Selection == 3 && selection_flag2 == 4) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("\n몇번째 날짜 수정 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			cout << "\n---------------------------------------------------------------------------\n";
			if (Read(Lists, k) == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			cout << "\n---------------------------------------------------------------------------\n";
			printf("몇번째 항목을 수정 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp >= INT_MIN && Num_tmp <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}

			printf("금액 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				int ch;
				while ((ch = getchar()) != '\n' && ch != EOF) {}

				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			else {
				if (Num_tmp2 >= INT_MIN && Num_tmp2 <= INT_MAX) {

				}
				else {
					system("cls");
					SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
					printf("오버,언더플로우 발생\n\n");


					continue;
				}
			}

			if (Lists != NULL) {
				Modify_by_Count_Object(Lists, k, Num_tmp, Num_tmp2);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}
		}

		if (Selection == 4 && selection_flag2 == 1) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);


				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";

			printf("\n몇번째 날짜 수정 ? :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < k; i++) {
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << Lists->m_pCurrent->m_Date << endl << "-> ";
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			std::getline(cin, String);

			if (Lists != NULL) {
				Modify_Date(Lists, k, String);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("해당리스트는 만들어지지 않았습니다.\n\n\n");
				continue;

			}
		}

		if (Selection == 3 && selection_flag2 == 3) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			int ch;
			while ((ch = getchar()) != '\n' && ch != EOF) {};
			cout << "검색어 :";
			getline(cin, String);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			LinearSearchByDuplicate_KyeWord_String(Lists, String, &SearchResultSize, &SearchSortResultArr);
		}

		if (Selection == 5 && selection_flag2 == 4) {
			Selection_flag = 1;
			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			SortBySelection_Object(Lists);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}

		if (Selection == 6 && selection_flag2 == 4) {
			Selection_flag = 1;

			if (!Lists) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("관리자 생성 필요\n");
				continue;
			}
			if (Lists->m_uCount == 0) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);


				printf("먼저 날짜를 추가해야 합니다.\n\n");
				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

			Lists->m_pCurrent = Lists->m_pHead;

			for (int i = 0; i < Lists->m_uCount; i++) {
				cout << endl << i << ".\t" << Lists->m_pCurrent->m_Date;
				Lists->m_pCurrent = Lists->m_pCurrent->m_pNext;
			}
			cout << "\n---------------------------------------------------------------------------\n";

			printf("\n병합할 날짜 ?( a += b)\n a :");
			err = scanf("%d", &k);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (k < 0 || k >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			printf("\nb :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {

				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("\n잘못된 입력\n");
				Sleep(300);
				continue;

			}
			if (Num_tmp < 0 || Num_tmp >= Lists->m_uCount) {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				cout << "0~" << Lists->m_uCount - 1 << "사이만 가능" << endl;

				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Merger(Lists, k, Num_tmp);
			continue;

		}

		if (Selection_flag == 0) {
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos); continue;
		}
	}


	return 0;
}

