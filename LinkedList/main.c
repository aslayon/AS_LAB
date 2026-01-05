#define _CRT_SECURE_NO_WARNINGS
#include <stdio.h>
#include <stdlib.h>
#include "LinkedList_int.h"
#include <CoreWindow.h>
#include <windows.h>
#include <limits.h>
#define Max 10




void Create(LinkedList** _ptList);
void Destroy(LinkedList** _ptList);
Node* GetNode(int _iObject);
Node* Read(LinkedList* _ptList, unsigned int i);
void Traversal(LinkedList* _ptList);
Node* AppendFromHead(LinkedList* _ptList, int _iObject);
Node* AppendFromTail(LinkedList* _ptList, int _iObject);
Node* InsertBefore(LinkedList* _ptList, Node*, int Object);
Node* InsertAfter(LinkedList* _ptList, Node* _ptNode, int Object);
Node* DeleteFromHead(LinkedList* _ptList);
Node* DeleteFromTail(LinkedList* _ptList);
Node* Delete(LinkedList* _ptList, Node* _ptNode);
Node* DeleteNode_Count(LinkedList* _ptList, int count);
void DeleteAll(LinkedList* _ptList);
Node* Modify(LinkedList* _ptList, Node* _ptNode, int iObject);
Node* LinearSearchByUnique(LinkedList* _ptList, int Object);
void LinearSearchByDuplicate(LinkedList* _ptList, int Object, int* _resultSize, Node*** _resultArray);
Node* BinarySearchByUnique(LinkedList* _ptList, int Object);
void BinarySearchByDuplicate(LinkedList* _ptList, int Object, int* _resultSize, Node*** _resultArray);
void Change(LinkedList* _ptList, Node* _ptNode1, Node* _ptNode2);
void SortByBubble(LinkedList* _ptList);
void SortByInsertion(LinkedList* _ptList);
void SortBySelection(LinkedList* _ptList);
Node* Modify_by_Count(LinkedList* _ptList, int count, int iObject);
Node* Insert_Count_Before(LinkedList* _ptList, int Count, int Object);
Node* Insert_Count_After(LinkedList* _ptList, int Count, int Object);

void cur(short x, short y)		//화면의 원하는 x, y좌표로 보냄
{
	COORD pos = { x, y };
	SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
}



int main() {
	long long L =(-2147483647 -1 );
	int R = 2147483647;
	char Cont;
	int flag = 0;
	LinkedList* Lists[Max] = { NULL, };
	int List_num = 0;
	long long Num_tmp = 0;
	long long Num_tmp2 = 0;
	long long Num_tmp3 = 0;
	Node* Node_tmp = NULL;
	int SearchResultSize;
	Node** SearchSortResultArr;
	COORD pos = { 0,0 };
	
	while (flag == 0) {
		int Selection_flag = 0;
		printf("---------------------------------------------------------------------------\n");
		printf("0. 관리 구조 생성\t\t1. 앞 노드 추가\t\t2. 뒤 노드 추가\n3. 임의 위치 값 읽기\t\t");
		printf("4. 노드 순회\t\t5. 관리구조 소멸\n---------------------------------------------------------------------------\n");
		printf("6. 기준 노드 앞 삽입\t\t7. 기준 노드 뒤 삽입\n8. 임의 노드 앞 삽입\t\t9. 임의 노드 뒤 삽입\n---------------------------------------------------------------------------\n");
		printf("11. 앞 노드 삭제\t\t12. 뒤 노드 삭제\n");
		printf("13. 기준 위치 삭제\t\t14. 임의 노드 삭제\t15. 모든 노드 삭제\n---------------------------------------------------------------------------\n");
		printf("32. 기준 노드 수정\t\t31. 임의 노드 수정\n---------------------------------------------------------------------------\n41. 단일 선형 탐색\t\t");
		printf("42. 다중 선형 탐색\n43. 단일 이진 탐색\t\t");
		printf("44. 다중 이진 탐색\n---------------------------------------------------------------------------\n51. 거품 정렬\t");
		printf("52. 삽입 정렬\t53. 선택 정렬\n54. 종료\n");
		printf("---------------------------------------------------------------------------\n");
		printf("리스트는 최대 10개까지 생성 가능.");
		printf("\n\n");
		long long Num_tmp = 0;
		long long Num_tmp2 = 0;
		long long Num_tmp3 = 0;
		if (!Node_tmp) Node_tmp == NULL;

		if (List_num == 0) {
			printf("None..\n");
			printf("\n");
		}
		else {
			printf("현재 존재하는 리스트들 _\n");
			for (int i = 0; i < Max; i++) {
				int count = 0;
				if (Lists[i] != NULL) {
					printf("\nList %d :", i);
					if (!Lists[i]->m_pHead) { printf("Empty"); continue; }
					Node* curr = Lists[i]->m_pHead;
					while (count < Lists[i]->m_uCount) {
						if (curr == Node_tmp) {
							printf(" '%d' ", curr->m_iObject);
							curr = curr->m_pNext;
							count++;
							continue;
						}
						printf(" %d ", curr->m_iObject);
						curr = curr->m_pNext;
						count++;
					}

				}
				else printf("\n@ ");

			}
			printf("\n\n");
		}




		int Selection = -1;

		printf("\n기능 선택:");
		int err = scanf("%d", &Selection);
		if (err != 1) {

			printf("\n잘못된 입력\n");
			Sleep(300);
			while (getchar() != '\n')
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

		}
		
		printf("\n\n");
		if (Selection == 0) {
			Selection_flag = 1;
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			if (List_num < Max) {
				for (int i = 0; i < Max; i++) {
					if (Lists[i] == NULL) {
						Create(&Lists[i]);
						List_num++;
						break;

					}
				}
				
			}
			
		}
		if (Selection == 5) {
			Selection_flag = 1;
			printf("지울 리스트 ? :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			Destroy(&Lists[Num_tmp]);
			List_num--;
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);

		}

		if (Selection == 3) {
			Selection_flag = 1;
			printf("몇번째 리스트에서 ? :");
			err = scanf("%d", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp2 <= 9 && Num_tmp2 >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("몇번째 노드를 ? :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Node_tmp = Read(Lists[Num_tmp2], Num_tmp);
		}
		if (Selection == 4) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Traversal(Lists[Num_tmp]);
		}
		if (Selection == 1) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("넣을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
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
			if (Lists[Num_tmp] != NULL) {
				Node_tmp = AppendFromHead(Lists[Num_tmp], Num_tmp2);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 없음\n\n");
				

			}
		}
		if (Selection == 2) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("넣을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
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
			if (Lists[Num_tmp] != NULL) {
				Node_tmp = AppendFromTail(Lists[Num_tmp], Num_tmp2);
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 없음\n\n");


			}

		}
		if (Selection == 6) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("넣을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
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
			Node_tmp = InsertBefore(Lists[Num_tmp], Node_tmp, Num_tmp2);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}



		if (Selection == 7) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("넣을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
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
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Node_tmp = InsertAfter(Lists[Num_tmp], Node_tmp, Num_tmp2);
		}

		if (Selection == 8) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("몇번째 노드 앞에 ? :");
			
			err = scanf("%lld", &Num_tmp3);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			printf("넣을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
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
			Node_tmp = Insert_Count_Before(Lists[Num_tmp], Num_tmp3, Num_tmp2);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}

		if (Selection == 9) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%d", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("몇번째 노드 앞에 ? :");

			err = scanf("%lld", &Num_tmp3);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			printf("넣을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
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
			Node_tmp = Insert_Count_After(Lists[Num_tmp], Num_tmp3, Num_tmp2);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}

		if (Selection == 11) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			Node_tmp = DeleteFromHead(Lists[Num_tmp]);
			free(Node_tmp);
			Node_tmp = NULL;
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
		if (Selection == 12) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			Node_tmp = DeleteFromTail(Lists[Num_tmp]);
			free(Node_tmp);
			Node_tmp = NULL;
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
		if (Selection == 13) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			Node_tmp = Delete(Lists[Num_tmp], Node_tmp);
			free(Node_tmp);
			Node_tmp = NULL;
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
		if (Selection == 14) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");
				
				continue;
			}
			printf("몇번째 요소 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			Node_tmp = DeleteNode_Count(Lists[Num_tmp], Num_tmp2);
			free(Node_tmp);
			Node_tmp = NULL;
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
		if (Selection == 15) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			DeleteAll(Lists[Num_tmp]);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
		if (Selection == 32) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("수정할 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Node_tmp = Modify(Lists[Num_tmp], Node_tmp, Num_tmp2);
			
		}
		if (Selection == 31) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("몇번째 노드 ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			printf("수정할 Object ? :");
			err = scanf("%lld", &Num_tmp3);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Node_tmp = Modify_by_Count(Lists[Num_tmp], Num_tmp2, Num_tmp3);
			
		}
		if (Selection == 41) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("찾을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Node_tmp = LinearSearchByUnique(Lists[Num_tmp], Num_tmp2);
		}
		if (Selection == 42) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("찾을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			LinearSearchByDuplicate(Lists[Num_tmp], Num_tmp2, &SearchResultSize, &SearchSortResultArr);

		}
		if (Selection == 43) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("찾을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			Node_tmp = BinarySearchByUnique(Lists[Num_tmp], Num_tmp2);
		}
		if (Selection == 44) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			printf("찾을 Object ? :");
			err = scanf("%lld", &Num_tmp2);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
			BinarySearchByDuplicate(Lists[Num_tmp], Num_tmp2, &SearchResultSize, &SearchSortResultArr);

		}
		if (Selection == 51) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			SortByBubble(Lists[Num_tmp]);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
		if (Selection == 52) {
			Selection_flag = 1;
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			SortByInsertion(Lists[Num_tmp]);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
		if (Selection == 53) {
			printf("몇번째 리스트 ? :");
			err = scanf("%lld", &Num_tmp);
			if (err != 1) {
				printf("\n잘못된 입력\n");
				Sleep(300);
				while (getchar() != '\n') {}
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				continue;

			}
			if (Num_tmp <= 9 && Num_tmp >= 0) {

			}
			else {
				system("cls");
				SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
				printf("리스트 범위 초과입니다.(0~9까지만 가능)\n");

				continue;
			}
			SortBySelection(Lists[Num_tmp]);
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
		if (Selection == 54) {
			printf("종료\n");
			flag = 1;
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}

		if (Selection_flag == 0) {
			system("cls");
			SetConsoleCursorPosition(GetStdHandle(STD_OUTPUT_HANDLE), pos);
		}
	}


	return 0;
}