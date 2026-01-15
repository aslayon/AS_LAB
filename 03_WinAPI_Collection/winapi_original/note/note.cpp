// note.cpp : 응용 프로그램에 대한 진입점을 정의합니다.
//

//lParam = y + x  마우스 클릭 이벤트 시
//x = lParma & 0x00001111)  // x = LOWORD(lParam)
//y = lParam & 0x11110000)>>16//  y = HIWORD(lParam)


#include "stdafx.h"
#include "note.h"
#include "tchar.h"
#include <iostream>
#define MAX_LOADSTRING 100000
#include <fstream>
#include <tchar.h>
#include <commdlg.h>
#define MAX_TEXT_LENGTH 10000
#include<string>
#include<string.h>
#include <locale>
// 전역 변수:
HINSTANCE hInst;								// 현재 인스턴스입니다.
TCHAR szTitle[MAX_LOADSTRING] = _T("NotePad");					// 제목 표시줄 텍스트입니다.
TCHAR szWindowClass[MAX_LOADSTRING] = _T("NewWin");			// 기본 창 클래스 이름입니다.
int xPointer = 0;
int yPointer = 0;
int CapsLock = 1;
int langu = 1;
int ime =1;
HWND hWnd;
wchar_t Cstr[10];
int ime_Counter = 0;
int scrollH = 0;
int scrollV = 0;
RECT RectErase;
int scrollRange = 255;
int scrollRange_ = 255;
struct TextData {
    wchar_t* text;
    int count;
};
TextData* texts; // 텍스트 데이터 배열

int textCount = 0; // 현재 텍스트의 개수
int pointerCount =0;
int focusingFlag =1;
int InsertFlag = 1;
int MAX_yPointer =0;

// 이 코드 모듈에 들어 있는 함수의 정방향 선언입니다.
ATOM				MyRegisterClass(HINSTANCE hInstance);
BOOL				InitInstance(HINSTANCE, int);
LRESULT CALLBACK	WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK	About(HWND, UINT, WPARAM, LPARAM);
void SaveDataToFile(HWND hWnd, HDC hdc);
void LoadDataFromFile(HWND hWnd,HDC hdc);
void ResetNote(HDC hdc);
void IME_RESULT(HWND hWnd, HDC hdc);
void IME_COMP(HWND hWnd,HDC hdc);
void LeftClick(HDC hdc);
void Return(HDC hdc);
void Back(HDC hdc);
void BKTAB(HDC hdc);
void AutoScroll(HWND hWnd);


int APIENTRY _tWinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPTSTR    lpCmdLine,
                     int       nCmdShow)
{
	UNREFERENCED_PARAMETER(hPrevInstance);
	UNREFERENCED_PARAMETER(lpCmdLine);

 	// TODO: 여기에 코드를 입력합니다.
	MSG msg;
	HACCEL hAccelTable;

	// 전역 문자열을 초기화합니다.
	LoadString(hInstance, IDS_APP_TITLE, szTitle, MAX_LOADSTRING);
	LoadString(hInstance, IDC_NOTE, szWindowClass, MAX_LOADSTRING);
	MyRegisterClass(hInstance);

	// 응용 프로그램 초기화를 수행합니다.
	if (!InitInstance (hInstance, nCmdShow))
	{
		return FALSE;
	}

	

	hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_NOTE));

	// 기본 메시지 루프입니다.
	while (GetMessage(&msg, NULL, 0, 0))
	{
		if (!TranslateAccelerator(msg.hwnd, hAccelTable, &msg))
		{
			TranslateMessage(&msg);
			DispatchMessage(&msg);
		}
	}

	return (int) msg.wParam;
}



//
//  함수: MyRegisterClass()
//
//  목적: 창 클래스를 등록합니다.
//
//  설명:
//
//    Windows 95에서 추가된 'RegisterClassEx' 함수보다 먼저
//    해당 코드가 Win32 시스템과 호환되도록
//    하려는 경우에만 이 함수를 사용합니다. 이 함수를 호출해야
//    해당 응용 프로그램에 연결된
//    '올바른 형식의' 작은 아이콘을 가져올 수 있습니다.
//
ATOM MyRegisterClass(HINSTANCE hInstance)
{
	WNDCLASSEX wcex;

	wcex.cbSize = sizeof(WNDCLASSEX);

	wcex.style			= CS_HREDRAW | CS_VREDRAW;
	wcex.lpfnWndProc	= WndProc;
	wcex.cbClsExtra		= 0;
	wcex.cbWndExtra		= 0;
	wcex.hInstance		= hInstance;
	wcex.hIcon			= LoadIcon(hInstance, MAKEINTRESOURCE(IDI_NOTE));
	wcex.hCursor		= LoadCursor(NULL, IDC_ARROW);
	wcex.hbrBackground	= (HBRUSH)(COLOR_WINDOW+1);
	wcex.lpszMenuName	= MAKEINTRESOURCE(IDC_NOTE);
	wcex.lpszClassName	= szWindowClass;
	wcex.hIconSm		= LoadIcon(wcex.hInstance, MAKEINTRESOURCE(IDI_SMALL));

	return RegisterClassEx(&wcex);
}

//
//   함수: InitInstance(HINSTANCE, int)
//
//   목적: 인스턴스 핸들을 저장하고 주 창을 만듭니다.
//
//   설명:
//
//        이 함수를 통해 인스턴스 핸들을 전역 변수에 저장하고
//        주 프로그램 창을 만든 다음 표시합니다.
//

BOOL InitInstance(HINSTANCE hInstance, int nCmdShow)
{
   

  // long WinStyle; // 스타일 저장할 목적

   hInst = hInstance; // 인스턴스 핸들을 전역 변수에 저장합니다.

   texts = new TextData[MAX_LOADSTRING];

   hWnd = CreateWindow(szWindowClass, szTitle, WS_OVERLAPPEDWINDOW | WS_HSCROLL | WS_VSCROLL,
      CW_USEDEFAULT, CW_USEDEFAULT, CW_USEDEFAULT,CW_USEDEFAULT , NULL, NULL, hInstance, NULL);

  // WinStyle = GetWindowLong(hWnd,GWL_STYLE); // 스타일 받아오기.
   //WinStyle = WinStyle | WS_HSCROLL; // 스크롤 추가
   //SetWindowLong(hWnd, GWL_STYLE,WinStyle); // 스타일 적용

   if (!hWnd)
   {
      return FALSE;
   }



   if (!SetWindowTextA (hWnd, "메모장")) // 타이틀 제목----------------------------------------------------------
	{
		return FALSE;
	}

   ShowWindow(hWnd, nCmdShow);
   //UpdateWindow(hWnd);

   return TRUE;
}

//
//  함수: WndProc(HWND, UINT, WPARAM, LPARAM)
//
//  목적: 주 창의 메시지를 처리합니다.
//
//  WM_COMMAND	- 응용 프로그램 메뉴를 처리합니다.
//  WM_PAINT	- 주 창을 그립니다.
//  WM_DESTROY	- 종료 메시지를 게시하고 반환합니다.
//
//
LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam)
{

	
	int wmId, wmEvent;
	PAINTSTRUCT ps;
	HDC hdc;
	int len;
	hdc = GetDC(hWnd);
	if(scrollH<0){
	scrollH =0;
	}
	{
	
	
	}
	if(textCount == 0){
	xPointer = 0;}


	
	if(pointerCount<0) {
		pointerCount =0;
	}
	
	switch (message)
	{
		case WM_CREATE:{
			CreateCaret(hWnd,NULL,1,17);
			ShowCaret(hWnd);
			scrollRange_ = 255;
			scrollRange = 0;
			SetScrollRange(hWnd, SB_VERT, 0, scrollRange_, TRUE);
			
			SetScrollRange(hWnd, SB_HORZ, 0, scrollRange, TRUE);
			break;
				   }
		case WM_IME_COMPOSITION:{
			HideCaret(hWnd);
			HIMC Himc = ImmGetContext(hWnd);
			
			
			if(lParam & GCS_RESULTSTR){
				IME_RESULT(hWnd, hdc);
				AutoScroll(hWnd);
			}
			else if(lParam & GCS_COMPSTR){
				IME_COMP(hWnd, hdc);
			}
			ShowCaret(hWnd);
			break;
		}
		
		case WM_LBUTTONDOWN:{
				LeftClick(hdc);
					break;		
							}
		case WM_CHAR:
		{
		SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);	
		HDC hdc = GetDC(hWnd); // 윈도우의 클라이언트 영역에 대한 출력 장치 컨텍스트 핸들을 가져옵니다.
		 HideCaret(hWnd);

	
		if (message != WM_IME_COMPOSITION){
			switch (wParam)
			{

			case VK_RETURN:{
				Return(hdc);
				AutoScroll(hWnd);
						   }
					SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
			ShowCaret(hWnd);
            break;

			


			case VK_BACK:{
			
            Back(hdc);
			AutoScroll(hWnd);
							 }





        
			case VK_HANGUL:
			langu = langu *(-1);
			break;


			case VK_TAB:{
					BKTAB(hdc);
					AutoScroll(hWnd);

					break;
							}
			 default:{
			
            wchar_t ch = (wchar_t)wParam;          //눌린 키 정보
            wchar_t str[2] = { ch, L'\0' };        //눌린키 + \0 (문자열의 끝을 표시) 하는 정보로 바꿈

            if (CapsLock < 0) {
                CharUpperW(str);
            }
            else {
                CharLowerW(str);
            }

            TextOut(hdc,xPointer- (scrollV) * (-15), yPointer - (scrollH)*15, str, 1);
            xPointer += 10;


			


			if(InsertFlag ==1 && pointerCount < textCount){
				for(int i=textCount; i>pointerCount; i--){
					if(i ==0)break;
					texts[i].text = texts[i-1].text;
					texts[i].count = texts[i-1].count;
				}
			}
			if(InsertFlag == -1){
				if(pointerCount != textCount){}
				else{texts[pointerCount].text = new wchar_t[2];}
				
			}
			else{
				texts[pointerCount].text = new wchar_t[2];}
            wcscpy(texts[pointerCount].text, str);
            texts[pointerCount].count = 10;
			if(InsertFlag == -1 && textCount != pointerCount){}
			else{
				textCount++;}
			pointerCount++;
			
			
			if(pointerCount == textCount){
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
				ShowCaret(hWnd);
				AutoScroll(hWnd);
				break;
			}
			{
				RECT clientRect;
				GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
				int windowWidth = clientRect.right - clientRect.left;
				int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
				RectErase.left = 0; // 왼쪽 x 좌표
				RectErase.top = yPointer; // 시작 y 좌표
				RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
				RectErase.bottom = RectErase.top + 17; // 아래쪽 y 좌표 (가정한 높이를 사용)

				AutoScroll(hWnd);
				InvalidateRect(hWnd,NULL,FALSE);
				

			
				


			}
					 }  
		}
		SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
		ShowCaret(hWnd);

	
		}
		break; 
}


		case WM_KEYDOWN:{
			
			switch(wParam){

			case VK_DELETE:{
						   
				if(textCount == pointerCount) break;
				
				HideCaret(hWnd);
				if (textCount > 0 && texts[pointerCount].count >= 15) { //이전입력이 글자일때
			
				
				
				
				delete[] (texts[pointerCount ].text);
				
				texts[pointerCount ].count =0;
                textCount--;
				
                
                TextOut(hdc,xPointer- (scrollV) * (-15), yPointer, L"    ", 4);

				if(pointerCount < textCount){
				for(int i=pointerCount; i<textCount;i++){
					if(!texts[i+1].text)break;
					texts[i].text = texts[i+1].text;
					texts[i].count = texts[i+1].count;
				}
				texts[textCount+1].text = NULL;
			}


				{
					RECT clientRect;
					GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
					int windowWidth = clientRect.right - clientRect.left;
					int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
					RectErase.left = 0; // 왼쪽 x 좌표
					RectErase.top = yPointer; // 시작 y 좌표
					RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
					RectErase.bottom = RectErase.top + 17; // 아래쪽 y 좌표 (가정한 높이를 사용)


					
					

					InvalidateRect(hWnd,NULL,FALSE);
					//UpdateWindow(hWnd);

					int x= 0;
					int y=0;
					HDC hdc = GetDC(hWnd);
					for(int i =0; i< textCount; i++) {
					
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					x= 0;
					y += 17;
					continue;
					}
					if(textCount >0 && texts[i].count >= 15){
				
						
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					x += texts[i].count;
					
					continue;
					}
					
						
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					
					x += 10;
					
					continue;
					}
				

				
				}
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
			ShowCaret(hWnd);
				break;
            }
				else if (textCount > 0 && texts[pointerCount].count == 0) { //이전 입력이 엔터일때
                
                delete[] (texts[pointerCount].text);
                textCount--;
				
				
				
				if(pointerCount < textCount){
				for(int i=pointerCount; i<textCount;i++){
					if(!texts[i+1].text)break;
					texts[i].text = texts[i+1].text;
					texts[i].count = texts[i+1].count;
				}
				texts[textCount+1].text = NULL;
			}
				
				{
				
					RECT clientRect;
					GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
					int windowWidth = clientRect.right - clientRect.left;
					int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
					RectErase.left = 0; // 왼쪽 x 좌표
					RectErase.top = yPointer; // 시작 y 좌표
					RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
					RectErase.bottom = RectErase.top + windowHeight; // 아래쪽 y 좌표 (가정한 높이를 사용)


					
					

					InvalidateRect(hWnd,NULL,FALSE);
					
				


				}

				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
			ShowCaret(hWnd);

				break;
            }
				else if(textCount >0 && texts[pointerCount].count == 10){
				delete[] (texts[pointerCount].text);
                textCount--;
				
                
				TextOut(hdc,xPointer- (scrollV) * (-15), yPointer, L"   ", 3);
				
				
				if(pointerCount < textCount){
				for(int i=pointerCount; i<textCount;i++){
					if(!texts[i+1].text)break;
					texts[i].text = texts[i+1].text;
					texts[i].count = texts[i+1].count;
				}
				texts[textCount+1].text = NULL;
			}
				
				
				{
				
					RECT clientRect;
					GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
					int windowWidth = clientRect.right - clientRect.left;
					int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
					RectErase.left = 0; // 왼쪽 x 좌표
					RectErase.top = yPointer; // 시작 y 좌표
					RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
					RectErase.bottom = RectErase.top + windowHeight; // 아래쪽 y 좌표 (가정한 높이를 사용)


					
					

					InvalidateRect(hWnd,NULL,FALSE);
					
				

				}
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
			ShowCaret(hWnd);
				break;
			}
               
						   
						   }

			case VK_CAPITAL:
					CapsLock = CapsLock * (-1);
					break;
			case VK_LEFT:{
					if(pointerCount ==0){break;}
					if(texts[pointerCount-1].count == 0 && texts[pointerCount-1].text[0] == '\0'){break;}
					HideCaret(hWnd);
					pointerCount--; 
					if(textCount > 0 &&texts[pointerCount].count == 0 && texts[pointerCount].text[0] == '\0'){
				
					}
					else{
						xPointer -= texts[pointerCount].count;
						
					}
					AutoScroll(hWnd);
					SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
					ShowCaret(hWnd);
					break;


					



				}
			

				 break;


				


			case VK_RIGHT:{
					if(pointerCount ==textCount){break;}
					if(texts[pointerCount].count == 0 && texts[pointerCount].text[0] == '\0'){break;}
					HideCaret(hWnd);
					
					if(textCount > 0 &&texts[pointerCount+1].count == 0 && texts[pointerCount+1].text[0] == '\0'){
						pointerCount++;
						xPointer += texts[pointerCount-1].count;
					}
					else{
						pointerCount++;
						xPointer += texts[pointerCount-1].count;
						
					}
					
					AutoScroll(hWnd);
					SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
					ShowCaret(hWnd);
					break;
				}
			case VK_UP:{
				if(textCount == 0)break;
				if(yPointer == 0){break;}
				
				HideCaret(hWnd);
				yPointer -= 17;
				int x=0;
				int y=0;

				for(int i=0;i<textCount;i++){
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					x =0;
					y += 17;
					}
					else{
					x += texts[i].count;
					}
					if(xPointer - x<6 && yPointer == y){
						xPointer = x;
						pointerCount = i+1;
						AutoScroll(hWnd);
						SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
						ShowCaret(hWnd);
						break;
					}
				}
				if(xPointer == x && yPointer == y){
					AutoScroll(hWnd);
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
				ShowCaret(hWnd);
				break;
				}
				else{
					x=0;
					y=0;
					for(int i=0;i<textCount;i++){
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					x =0;
					y += 17;
					}
					else{
					x += texts[i].count;
					}
					if(texts[i+1].count == 0 && texts[i+1].text[0] == '\0' && yPointer == y){
						pointerCount = i+1;
						xPointer += texts[pointerCount].count;
						xPointer = x;
						AutoScroll(hWnd);
						SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
						ShowCaret(hWnd);

						break;
					}
					}
				}
				


				


				
				}
				break;

				case VK_DOWN:{
					if(textCount == 0)break;
					if(yPointer == MAX_yPointer){break;}
					int x=0;
					int y=0;
					int FFF = 0;
					yPointer +=17;
					for(int i=0;i<textCount;i++){
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
						if(yPointer == y){//아래가 더 작음.
						FFF = 1;
						 xPointer = x;
						 pointerCount = i;
						 break;
						}
					x =0;
					y += 17;
					}
					else{
					x += texts[i].count;
					if(xPointer - x <6&& yPointer == y){//아래가 크거나 같
						xPointer = x;
						FFF = -1;
						pointerCount = i+1;
						break;
					
					}
					}
					
					}
					if(FFF ==1){//아래가 더 작
					
					}
					if(FFF == -1){//아래 더 크거나 같

					}
					if(FFF == 0){
						pointerCount = textCount;
						xPointer = x;}
					
				

				AutoScroll(hWnd);
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
				ShowCaret(hWnd);
				break;
				}
							 
				case VK_HOME:{
					if(textCount == 0)break;
					int x=0;
					int y=0;
					for(int i=0;i<textCount;i++){
						if(yPointer == 0){
							pointerCount = 0;
							xPointer = 0;
							break;}
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					
					x =0;
					y += 17;
					if(y == yPointer){
						pointerCount = i+1;
						xPointer = 0;
					}
					}
					else{
					x += texts[i].count;										
					}

					}
					AutoScroll(hWnd);
					SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
				ShowCaret(hWnd);
					
							 }
							 break;
				case VK_END:{
						if(textCount == 0)break;
						int x = 0;
						int y = 0;
						int fff = 0;
						for(int i=0;i<textCount;i++){
						
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					if(y == yPointer){
						fff = 1;
						pointerCount = i;
						xPointer = x;
						break;
					}
					x =0;
					y += 17;
					
					}
					else{
					x += texts[i].count;
					
					}

					}
				
						if(fff ==0){
						pointerCount = textCount;
						xPointer = x;
						}
						
				AutoScroll(hWnd);
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
				ShowCaret(hWnd);
				break;
							}
				
				case VK_INSERT:{
							InsertFlag *= -1;
							break;
							   }
				default:{}
						}
						
						}
case WM_VSCROLL:
    // 수직 스크롤바 메시지 처리
{
    SCROLLINFO si;
    int yPos, nScrollCode;
	HideCaret(hWnd);
    // 현재 스크롤 정보를 가져옵니다.
    ZeroMemory(&si, sizeof(si));
    si.cbSize = sizeof(si);
    si.fMask = SIF_ALL;
    GetScrollInfo(hWnd, SB_VERT, &si);

    // 스크롤 이벤트를 처리합니다.
    nScrollCode = LOWORD(wParam);
    switch (LOWORD(wParam))
    {
        case SB_LINEUP:
			if(scrollH ==0) break;
            si.nPos -= 1;
			scrollH--;
			
            break;

        case SB_LINEDOWN:
            si.nPos += 1;
			scrollH++;
			
            break;
		case SB_PAGEUP:{
			if(scrollH ==0) break;

			if(scrollH <5){
			scrollH = 0;
			si.nPos = 0;
			}
			else{
				si.nPos -= 5;
				scrollH -= 5;}
            
			break;
					   }
		case SB_PAGEDOWN:{
			
            si.nPos += 5;
			
			scrollH += 5;
			break;
					   }
		
		
        

        default:
            break;
    }

    // 스크롤 위치가 최소값보다 작거나 최대값보다 크면 조정합니다.
    si.nPos = max(0, min(si.nPos, si.nMax - si.nPage));

    // 새로운 스크롤 위치를 설정합니다.
    SetScrollPos(hWnd, SB_VERT, si.nPos, TRUE);

    // 화면을 다시 그립니다.
    
	{
				RECT clientRect;
				GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
				int windowWidth = clientRect.right - clientRect.left;
				int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
				RectErase.left = 0; // 왼쪽 x 좌표
				RectErase.top = 0; // 시작 y 좌표
				RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
				RectErase.bottom = RectErase.top + windowHeight; // 아래쪽 y 좌표 (가정한 높이를 사용)	
				InvalidateRect(hWnd,NULL,FALSE);
				//UpdateWindow(hWnd);

				
				


			}
	SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
						ShowCaret(hWnd);

    break;
}


case WM_HSCROLL:
{
    SCROLLINFO si;
    int xPos, nScrollCode;
	HideCaret(hWnd);
    // 현재 수평 스크롤 정보를 가져옵니다.
    ZeroMemory(&si, sizeof(si));
    si.cbSize = sizeof(si);
    si.fMask = SIF_ALL;
    GetScrollInfo(hWnd, SB_HORZ, &si);

    // 스크롤 이벤트를 처리합니다.
    nScrollCode = LOWORD(wParam);
    switch (LOWORD(wParam))
    {
        case SB_LINELEFT:
			if(scrollV ==0) break;
            si.nPos -= 1;
			scrollV++;
			
            break;

        case SB_LINERIGHT:
            si.nPos += 1;
			scrollV--;
			
            break;

       case SB_PAGELEFT:{
			if(scrollV ==0) break;
			if(scrollV >-5){
			scrollV = 0;
			si.nPos = 0;
			}
			else{
				scrollV += 5;
			si.nPos -= 5;
			}
			
			break;
					   }
            
			
		case SB_PAGERIGHT:{
			
            si.nPos += 5;
			
			scrollV -= 5;
			break;
					   }

        default:
            break;
    }

    // 스크롤 위치가 최소값보다 작거나 최대값보다 크면 조정합니다.
    si.nPos = max(0, min(si.nPos, si.nMax - si.nPage));

    // 새로운 스크롤 위치를 설정합니다.
    SetScrollPos(hWnd, SB_HORZ, si.nPos, TRUE);

    // 화면을 다시 그립니다.
    

	{
				RECT clientRect;
				GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
				int windowWidth = clientRect.right - clientRect.left;
				int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
				RectErase.left = 0; // 왼쪽 x 좌표
				RectErase.top = 0; // 시작 y 좌표
				RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
				RectErase.bottom = RectErase.top + windowHeight; // 아래쪽 y 좌표 (가정한 높이를 사용)	
				InvalidateRect(hWnd,NULL,FALSE);
				//UpdateWindow(hWnd);

				
				


			}
	SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
						ShowCaret(hWnd);

    break;
}

	case WM_COMMAND:
		wmId    = LOWORD(wParam);
		wmEvent = HIWORD(wParam);
		// 메뉴 선택을 구문 분석합니다.
		switch (wmId)
		{
		case IDM_ABOUT:
			DialogBox(hInst, MAKEINTRESOURCE(IDD_ABOUTBOX), hWnd, About);
			break;
		case IDM_EXIT:
			DestroyWindow(hWnd);
			break;
		case ID_32771:{
					  SaveDataToFile(hWnd,hdc);
					  break;
					  }
					  break;
		case ID_32772:{
					  ResetNote(hdc);
					  LoadDataFromFile(hWnd,hdc);
					  break;
					  }
					  break;

		case ID_32773:{
					  ResetNote(hdc);
					  
					  break;
					  }
					  break;
		default:
			return DefWindowProc(hWnd, message, wParam, lParam);
		}
		break;
	case WM_SIZE:{
		{
				RECT clientRect;
				GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
				int windowWidth = clientRect.right - clientRect.left;
				int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
				RectErase.left = 0; // 왼쪽 x 좌표
				RectErase.top = 0; // 시작 y 좌표
				RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
				RectErase.bottom = RectErase.top + windowHeight; // 아래쪽 y 좌표 (가정한 높이를 사용)	
				InvalidateRect(hWnd,NULL,FALSE);
				//UpdateWindow(hWnd);

	
				

				
				}
        ReleaseDC(hWnd, hdc);
				 }
		break;
	case WM_SETFOCUS:
		{
			hdc = GetDC(hWnd);
			CreateCaret(hWnd,NULL,1, 17);
			ShowCaret(hWnd);
			SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
		}
		break;

	case WM_KILLFOCUS:
		{
			hdc = GetDC(hWnd);
			HideCaret(hWnd);
			DestroyCaret();
		}
		break;
	case WM_PAINT:
	{
			RECT clientRect;
					GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
					int windowWidth = clientRect.right - clientRect.left;
					int windowHeight = clientRect.bottom - clientRect.top;
		/** 더블버퍼링 시작처리입니다. **/
        HDC hdc, MemDC, tmpDC;
        HBITMAP BackBit, oldBackBit;
        RECT bufferRT;
        hdc = BeginPaint(hWnd, &ps);
       
        GetClientRect(hWnd, &bufferRT);
        MemDC = CreateCompatibleDC(hdc);
        BackBit = CreateCompatibleBitmap(hdc, bufferRT.right, bufferRT.bottom);
        oldBackBit = (HBITMAP)SelectObject(MemDC, BackBit);
        PatBlt(MemDC,0,0,bufferRT.right, bufferRT.bottom, WHITENESS);
       

        // TODO: 여기에 그리기 코드를 추가합니다.
		RECT rc;
        GetClientRect(hWnd, &rc);
        FillRect(hdc, &rc, (HBRUSH)(COLOR_WINDOW+1));
        int x= 0;
		int y=0;
		hdc = GetDC(hWnd);
		for(int i =0; i< textCount; i++) {
					
			if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
				x= 0;
				y += 17;
				continue;
			}
			if(textCount >0 && texts[i].count >= 15){
				
				if(y - (scrollH)*15 > -50 && y - (scrollH)*15  < windowHeight + 50 )
					TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
				x += texts[i].count;
					
			continue;
		}
					
				if(y - (scrollH)*15 > -50 && y - (scrollH)*15  < windowHeight + 50 )
					TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					
				x += 10;
					
				continue;
		}

        /** 더블버퍼링 끝처리 입니다. **/
        tmpDC=hdc;
        hdc=MemDC;
        MemDC=tmpDC;
        GetClientRect(hWnd, &bufferRT);
        BitBlt(hdc, 0, 0, bufferRT.right, bufferRT.bottom, MemDC, 0, 0, SRCCOPY);
        SelectObject(MemDC, oldBackBit);
        DeleteObject(BackBit);
        DeleteDC(MemDC);
        EndPaint(hWnd, &ps);
        break;


	}
	break;
	case WM_DESTROY:
		PostQuitMessage(0);
		break;
	default:
		return DefWindowProc(hWnd, message, wParam, lParam);
	}
	return 0;
}

// 정보 대화 상자의 메시지 처리기입니다.
INT_PTR CALLBACK About(HWND hDlg, UINT message, WPARAM wParam, LPARAM lParam)
{
	UNREFERENCED_PARAMETER(lParam);
	switch (message)
	{
	case WM_INITDIALOG:
		return (INT_PTR)TRUE;

	case WM_COMMAND:
		if (LOWORD(wParam) == IDOK || LOWORD(wParam) == IDCANCEL)
		{
			EndDialog(hDlg, LOWORD(wParam));
			return (INT_PTR)TRUE;
		}
		break;
	}
	return (INT_PTR)FALSE;
}



void SaveDataToFile(HWND hWnd, HDC hdc) {
    OPENFILENAME ofn;
    TCHAR szFile[MAX_PATH] = { 0 };

    ZeroMemory(&ofn, sizeof(ofn));
    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hWnd;
    ofn.lpstrFilter = _T("Text Files (*.txt)\0*.txt\0All Files (*.*)\0*.*\0");
    ofn.lpstrFile = szFile;
    ofn.lpstrFile[0] = '\0';
    ofn.nMaxFile = sizeof(szFile);
    ofn.Flags = OFN_EXPLORER | OFN_PATHMUSTEXIST | OFN_HIDEREADONLY | OFN_OVERWRITEPROMPT;

    if (GetSaveFileName(&ofn) == TRUE) {
        std::wofstream file(ofn.lpstrFile);
		file.imbue(std::locale(std::locale("kor")));
        if (file.is_open()) {
            for (int i = 0; i < textCount; ++i) {
                // 문자열의 내용을 파일에 저장
				int length = wcslen(texts[i].text);
				wchar_t* tmp = new wchar_t[length+1];
				wcscpy(tmp, texts[i].text);
				//TextOut(hdc,i*15,17,tmp,1);
                file << tmp << std::endl;
                file << texts[i].count << std::endl;
				delete[] tmp;
            }
            file.close();
            MessageBox(hWnd, _T("저장됐습니다."), _T("저장됐니?"), MB_OK | MB_ICONINFORMATION);
        } else {
            MessageBox(hWnd, _T("저장실패"), _T("저장됐니?"), MB_OK | MB_ICONERROR);
        }
    }
}




void LoadDataFromFile(HWND hWnd,HDC hdc) {
    OPENFILENAME ofn;
    TCHAR szFile[MAX_PATH] = { 0 };
	
    ZeroMemory(&ofn, sizeof(ofn));
    ofn.lStructSize = sizeof(ofn);
    ofn.hwndOwner = hWnd;
    ofn.lpstrFilter = _T("Text Files (*.txt)\0*.txt\0All Files (*.*)\0*.*\0");
    ofn.lpstrFile = szFile;
    ofn.lpstrFile[0] = '\0';
    ofn.nMaxFile = sizeof(szFile);
    ofn.Flags = OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST;
	
    if (GetOpenFileName(&ofn) == TRUE) {
        std::wifstream file(ofn.lpstrFile);
		file.imbue(std::locale(std::locale("kor")));
        if (file.is_open()) {
            int i = 0;
            while (!file.eof()) {

				texts[i].text = new wchar_t[2];
				wchar_t* tmp = new wchar_t[3];
				file.getline(tmp,sizeof(wchar_t)*2);
				std::wstring line(tmp);
				if(line.empty()){
					file.getline(tmp,sizeof(wchar_t)*2);
					std::wstring line(tmp);
					if(line.empty()){
						delete[] texts[i].text;
						delete[] tmp;
						break;}
					else{
						texts[i].text[0] = L'\0';
						texts[i].text[1] = L'\0';
						texts[i].count = 0;
						delete[] tmp;
						i++;
						continue;
					}
				}
				wcscpy(texts[i].text,tmp);
				TextOut(hdc,i*17,i*17,texts[i].text,1);

				
				file.getline(tmp,sizeof(wchar_t)*2);
				std::wstring wstr(tmp);
				
				int numtmp = std::stoi(wstr);
				texts[i].count = numtmp;
				delete[] tmp;
				
				
				i++;
            }
            textCount = i;
            file.close();


			{
				
				InvalidateRect(hWnd,NULL,FALSE);
				//UpdateWindow(hWnd);

				int x= 0;
				int y=0;
					HDC hdc = GetDC(hWnd);
					for(int i =0; i< textCount; i++) {
					
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					x= 0;
					y += 17;
					MAX_yPointer = y;
					continue;
					}
					if(textCount >0 && texts[i].count >= 15){
				
						
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					x += texts[i].count;
					
					continue;
					}
					
						
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					
					x += 10;
					
					continue;
					}
				

				
				}


            MessageBox(hWnd, _T("File loaded successfully."), _T("Success"), MB_OK | MB_ICONINFORMATION);
        } else {
            MessageBox(hWnd, _T("Failed to open file for reading."), _T("Error"), MB_OK | MB_ICONERROR);
        }
    }
}

void ResetNote(HDC hdc){
	pointerCount = textCount;
	for(int i=textCount;i>0;i--){
	{
		delete[] (texts[i-1].text);		
		texts[i-1].count = 0;
	}  
	xPointer = 0;
yPointer = 0;
CapsLock = 1;
langu = 1;
ime =1;


ime_Counter = 0;
scrollH = 0;
scrollV = 0;



textCount = 0; // 현재 텍스트의 개수
pointerCount =0;
focusingFlag =1;
InsertFlag = 1;
MAX_yPointer =0;
	InvalidateRect(hWnd,NULL,FALSE);
            //UpdateWindow(hWnd);
							 }
	
	
}

void IME_RESULT(HWND hWnd, HDC hdc){
	int len;
	HIMC Himc = ImmGetContext(hWnd);
	hdc = GetDC(hWnd);
	if((len = ImmGetCompositionString(Himc,GCS_RESULTSTR,NULL,0))>0){
					ime_Counter = 0;
					ImmGetCompositionString(Himc,GCS_RESULTSTR,Cstr,len);
					Cstr[len] = L'\0';
					TextOut(hdc,xPointer- (scrollV) * (-15), yPointer - (scrollH)*15, Cstr, 1);
					



					int xPt = xPointer + 15;
					SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
					xPointer += 15;
					ime = 1;

					if(InsertFlag == 1 && pointerCount != textCount){
						for(int i = textCount; i> pointerCount;i--){
							if(i ==0) break;
							texts[i].text = texts[i-1].text;
							texts[i].count = texts[i-1].count;
						}
					}

					if(InsertFlag == -1){
					if(pointerCount != textCount){}
					else{texts[pointerCount].text = new wchar_t[2];}
				
					}
					else{					
						texts[pointerCount].text = new wchar_t[2];}

					wcscpy(texts[pointerCount].text, Cstr);
					texts[pointerCount].count = 15;
					if(InsertFlag == -1 && textCount != pointerCount){}
					else{
						textCount++;}
					pointerCount++;
					if(InsertFlag  ==1&& pointerCount < textCount){

					RECT clientRect;
					GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
					int windowWidth = clientRect.right - clientRect.left;
					int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
					RectErase.left = 0; // 왼쪽 x 좌표
					RectErase.top = yPointer; // 시작 y 좌표
					RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
					RectErase.bottom = RectErase.top + 17; // 아래쪽 y 좌표 (가정한 높이를 사용)


					InvalidateRect(hWnd,NULL,FALSE);
					//UpdateWindow(hWnd);

					int x= 0;
					int y=0;
					HDC hdc = GetDC(hWnd);
					for(int i =0; i< textCount; i++) {
					
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					x= 0;
					y += 17;
					continue;
					}
					if(textCount >0 && texts[i].count >= 15){
				
						
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					x += texts[i].count;
					
					continue;
					}
					
						
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					
					x += 10;
					
					continue;

					}
					
					}
				}

}

void IME_COMP(HWND hWnd,HDC hdc){
	int len;
	ime_Counter++;
	HIMC Himc = ImmGetContext(hWnd);
	hdc = GetDC(hWnd);
	if(ime == 1) 
			ime =  (-1);
	len =ImmGetCompositionString(Himc,GCS_COMPSTR,NULL,0);
	ImmGetCompositionString(Himc,GCS_COMPSTR,Cstr,len);
	Cstr[len] = L'\0';
	int xPt = xPointer + 15;
	if(Cstr[0] != L'\0'){
			AutoScroll(hWnd);
			TextOut(hdc,xPointer- (scrollV) * (-15),  yPointer - (scrollH)*15, Cstr, 1);
	}
	else {
			TextOut(hdc,xPointer- (scrollV) * (-15),  yPointer - (scrollH)*15, L"    ", 4);
			xPt -= 15;
	}
				


				
	xPointer +=15;
	ShowCaret(hWnd);
	SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
	xPointer -=15;
	
}

void LeftClick(HDC hdc){
	HideCaret(hWnd);
				POINT cur;
				int xCur=0;
			
				
				int yCur=0;
			

				int x = 0;
				int y = 0;

				int Found =0;
				if(GetCursorPos(&cur)){
					ScreenToClient(hWnd, &cur);
					xCur = cur.x- (scrollV) * (15);
					yCur = cur.y - (scrollH)*(-15);
					
					if(yCur > MAX_yPointer){
						Found = -1;
					}
					for(int i=0;i<textCount;i++){
						if(yCur - y >=0 && yCur - y <= 17){
							if(xCur-x >=0 && xCur - x <= texts[i].count){
								Found = 1;
								xPointer = x;
								yPointer = y;
								pointerCount = i;
								break;
							}
						}
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
						
					x =0;
					y += 17;
					}
					else{
					x += texts[i].count;
					
						}
					
					}



				}
				else{
				ShowCaret(hWnd);
				return;
				}
				if(Found !=1){
					xPointer = x;
					yPointer = y;
					pointerCount = textCount;
				}
				
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
				ShowCaret(hWnd);

}

void Return(HDC hdc){
	HideCaret(hWnd);
            yPointer += 17;
            xPointer = 0;
			if(MAX_yPointer <yPointer){
				MAX_yPointer = yPointer;}

			if(InsertFlag == 1 && pointerCount < textCount){
				for(int i=textCount; i>pointerCount;i--){
					
					texts[i].text = texts[i-1].text;
					texts[i].count = texts[i-1].count;
				}
			}
            texts[pointerCount].text = new wchar_t[2];
            texts[pointerCount].text[0] = L'\0';
            texts[pointerCount].text[1] = L'\0';
            texts[pointerCount].count = 0; 
            textCount++;
			pointerCount++;


			RECT clientRect;
			GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
			int windowWidth = clientRect.right - clientRect.left;
			int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
			RectErase.left = 0; // 왼쪽 x 좌표
			RectErase.top = yPointer-17; // 시작 y 좌표
			RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
			RectErase.bottom = RectErase.top + windowHeight; // 아래쪽 y 좌표 (가정한 높이를 사용)


			InvalidateRect(hWnd,NULL,FALSE);
			/*
            //UpdateWindow(hWnd);

			int x= 0;
				int y=0;
					hdc = GetDC(hWnd);
					for(int i =0; i< textCount; i++) {
					
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					x= 0;
					y += 17;
					continue;
					}
					if(textCount >0 && texts[i].count >= 15){
				
						
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					x += texts[i].count;
					
					continue;
					}
					
						
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					
					x += 10;
					
					continue;
			
					}*/


}

void Back(HDC hdc){
				
				if(textCount ==0) return;
				if(pointerCount == 0){
					return;
				ShowCaret(hWnd);
				}
				
				
				HideCaret(hWnd);
				if (textCount > 0 && texts[pointerCount - 1].count >= 15) { //이전입력이 글자일때
			
				
				
				
				delete[] (texts[pointerCount - 1].text);
				xPointer -= texts[pointerCount - 1].count;
				texts[pointerCount - 1].count =0;
                textCount--;
				pointerCount--;
                
                TextOut(hdc,xPointer- (scrollV) * (-15), yPointer, L"    ", 4);

				if(pointerCount < textCount){
				for(int i=pointerCount; i<textCount;i++){
					if(!texts[i+1].text)break;
					texts[i].text = texts[i+1].text;
					texts[i].count = texts[i+1].count;
				}
				texts[textCount+1].text = NULL;
			}

				if(pointerCount == textCount){
					InvalidateRect(hWnd,NULL,FALSE);
					SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
					ShowCaret(hWnd);
					return;
				}
				{
				
				RECT clientRect;
				GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
				int windowWidth = clientRect.right - clientRect.left;
				int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
				RectErase.left = 0; // 왼쪽 x 좌표
				RectErase.top = yPointer; // 시작 y 좌표
				RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
				RectErase.bottom = RectErase.top + 17; // 아래쪽 y 좌표 (가정한 높이를 사용)
				InvalidateRect(hWnd,NULL,FALSE);	
				//UpdateWindow(hWnd);
				
				

				
				}
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
			ShowCaret(hWnd);
				return;
            }
				else if (textCount > 0 && texts[pointerCount - 1].count == 0) { //이전 입력이 엔터일때
                yPointer -= 17;
                xPointer = 0; // 변경된 부분
                delete[] (texts[pointerCount - 1].text);
                textCount--;
				pointerCount--;
				
				
				if(pointerCount < textCount){
				for(int i=pointerCount; i<textCount;i++){
					if(!texts[i+1].text)break;
					texts[i].text = texts[i+1].text;
					texts[i].count = texts[i+1].count;
				}
				texts[textCount+1].text = NULL;
			}
				int x=0;
				int y=0;
				for(int i =0; i< pointerCount; i++) {
					
					if(textCount > 0 &&texts[i].count == 0 && texts[i].text[0] == '\0'){
					x= 0;
					y += 17;
					continue;
					}
					if(textCount >0 && texts[i].count >= 15){
				
						if(y >= yPointer)
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					x += texts[i].count;
					
					continue;
					}
					
						if(y >= yPointer)
						TextOut(hdc,x- (scrollV) * (-15), y - (scrollH)*15, texts[i].text, 1);
						
					
					
					
					x += 10;
					
					continue;
					}
				xPointer = x;

				if(pointerCount == textCount){
					InvalidateRect(hWnd,NULL,FALSE);
					SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
					ShowCaret(hWnd);
					return;
				}
				{
				RECT clientRect;
				GetClientRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
				int windowWidth = clientRect.right - clientRect.left;
				int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
				
				RectErase.left = 0; // 왼쪽 x 좌표
				RectErase.top = yPointer; // 시작 y 좌표
				RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
				RectErase.bottom = RectErase.top + windowHeight; // 아래쪽 y 좌표 (가정한 높이를 사용)

				InvalidateRect(hWnd,NULL,FALSE);
				//UpdateWindow(hWnd);			
				

				
				

				}

				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
				ShowCaret(hWnd);

				return;
            }
				else if(textCount >0 && texts[pointerCount-1].count == 10){
				delete[] (texts[pointerCount - 1].text);
                textCount--;
				pointerCount--;
                xPointer -= 10;
				TextOut(hdc,xPointer- (scrollV) * (-15), yPointer, L"   ", 3);
				
				
				if(pointerCount < textCount){
				for(int i=pointerCount; i<textCount;i++){
					if(!texts[i+1].text)break;
					texts[i].text = texts[i+1].text;
					texts[i].count = texts[i+1].count;
				}
				texts[textCount+1].text = NULL;
				}
				
				if(pointerCount == textCount){
					InvalidateRect(hWnd,NULL,FALSE);
					SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
					ShowCaret(hWnd);
					return;
				}
				{
				RECT clientRect;
				GetClientRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
				int windowWidth = clientRect.right - clientRect.left;
				int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
				
				RectErase.left = 0; // 왼쪽 x 좌표
				RectErase.top = yPointer; // 시작 y 좌표
				RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
				RectErase.bottom = RectErase.top + 17; // 아래쪽 y 좌표 (가정한 높이를 사용)

			
				InvalidateRect(hWnd,NULL,FALSE);
				//UpdateWindow(hWnd);
				
				
				
				
				}
				SetCaretPos(xPointer- (scrollV) * (-15),yPointer - (scrollH)*15);
			ShowCaret(hWnd);
				return;
			}
}

void BKTAB(HDC hdc){
			wchar_t str[2] = { L' ', L'\0' };
			TextOut(hdc,xPointer- (scrollV) * (-15), yPointer, str, 4);
			xPointer += 40;


			if(InsertFlag ==1 && pointerCount < textCount){
				for(int i=textCount; i>pointerCount; i--){
					if(i ==0)break;
					texts[i].text = texts[i-1].text;
					texts[i].count = texts[i-1].count;
				}
			}
			if(InsertFlag == -1){
				if(pointerCount != textCount){}
				else{texts[pointerCount].text = new wchar_t[2];}
				
			}
			else{
				texts[pointerCount].text = new wchar_t[2];}
				wcscpy(texts[pointerCount].text, str);
				texts[pointerCount].count = 40;
			if(InsertFlag == -1 && textCount != pointerCount){}
			else{
				textCount++;}
				pointerCount++;
			
			
			
			{
				RECT clientRect;
				GetWindowRect(hWnd, &clientRect); // hWnd는 윈도우의 핸들

				// 윈도우의 폭과 높이를 계산
				int windowWidth = clientRect.right - clientRect.left;
				int windowHeight = clientRect.bottom - clientRect.top;

				// RECT 구조체 만들기
				RectErase.left = 0; // 왼쪽 x 좌표
				RectErase.top = yPointer; // 시작 y 좌표
				RectErase.right = RectErase.left + windowWidth; // 오른쪽 x 좌표 (윈도우의 폭을 사용)
				RectErase.bottom = RectErase.top + 17; // 아래쪽 y 좌표 (가정한 높이를 사용)


				InvalidateRect(hWnd,NULL,FALSE);
				//UpdateWindow(hWnd);

		
				


			}

}

void AutoScroll(HWND hWnd) {



	RECT tempRect;
	GetWindowRect(hWnd, &tempRect); // hWnd는 윈도우의 핸들

	// 윈도우의 폭과 높이를 계산
	int Widthh = tempRect.right - tempRect.left - 50;
	int Heightt = tempRect.bottom - tempRect.top - 50;

	if (xPointer - (scrollV) * (-15) > Widthh - 50)
	{
		SCROLLINFO si;
		int xPos, nScrollCode;
		HideCaret(hWnd);
		// 현재 수평 스크롤 정보를 가져옵니다.
		ZeroMemory(&si, sizeof(si));
		si.cbSize = sizeof(si);
		si.fMask = SIF_ALL;
		GetScrollInfo(hWnd, SB_HORZ, &si);
		while (xPointer - (scrollV) * (-15) > Widthh - 50) {
			si.nPos += 10;
			scrollV -= 10;
		}
		if(si.nPos>scrollRange){
		scrollRange += 50;
		 SetScrollRange(hWnd, SB_HORZ, 0, scrollRange, TRUE);
		}
		SetScrollPos(hWnd, SB_HORZ, si.nPos, TRUE);
		InvalidateRect(hWnd, NULL, FALSE);
		SetCaretPos(xPointer - (scrollV) * (-15), yPointer - (scrollH) * 15);
		ShowCaret(hWnd);
	}
	if (xPointer - (scrollV) * (-15) < 0)
	{
		SCROLLINFO si;
		int xPos, nScrollCode;
		HideCaret(hWnd);
		// 현재 수평 스크롤 정보를 가져옵니다.
		ZeroMemory(&si, sizeof(si));
		si.cbSize = sizeof(si);
		si.fMask = SIF_ALL;
		GetScrollInfo(hWnd, SB_HORZ, &si);
		while (xPointer - (scrollV) * (-15) < 0) {
			si.nPos -= 10;
			scrollV += 10;
		}
		SetScrollPos(hWnd, SB_HORZ, si.nPos, TRUE);
		InvalidateRect(hWnd, NULL, FALSE);
		SetCaretPos(xPointer - (scrollV) * (-15), yPointer - (scrollH) * 15);
		ShowCaret(hWnd);
	}

	if (yPointer - (scrollH) * 15 > Heightt - 50)
	{
		SCROLLINFO si;
		int xPos, nScrollCode;
		HideCaret(hWnd);
		// 현재 수평 스크롤 정보를 가져옵니다.
		ZeroMemory(&si, sizeof(si));
		si.cbSize = sizeof(si);
		si.fMask = SIF_ALL;
		GetScrollInfo(hWnd, SB_VERT, &si);
		while (yPointer - (scrollH) * 15 > Heightt - 50) {
			si.nPos += 2;
			scrollH += 2;
		}

		if(si.nPos>scrollRange){
			scrollRange_ += 50;
			SetScrollRange(hWnd, SB_VERT, 0, scrollRange_, TRUE);
		}
		SetScrollPos(hWnd, SB_VERT, si.nPos, TRUE);
		InvalidateRect(hWnd, NULL, FALSE);
		SetCaretPos(xPointer - (scrollV) * (-15), yPointer - (scrollH) * 15);
		ShowCaret(hWnd);
	}
	if (yPointer - (scrollH) * 15 < -40)
	{
		SCROLLINFO si;
		int xPos, nScrollCode;
		HideCaret(hWnd);
		// 현재 수평 스크롤 정보를 가져옵니다.
		ZeroMemory(&si, sizeof(si));
		si.cbSize = sizeof(si);
		si.fMask = SIF_ALL;
		GetScrollInfo(hWnd, SB_VERT, &si);
		while (yPointer - (scrollH) * 15 < 40) {
			si.nPos -= 2;
			scrollH -= 2;
		}
		SetScrollPos(hWnd, SB_VERT, si.nPos, TRUE);
		InvalidateRect(hWnd, NULL, FALSE);
		SetCaretPos(xPointer - (scrollV) * (-15), yPointer - (scrollH) * 15);
		ShowCaret(hWnd);
	}



}