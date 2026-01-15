// paint1231.cpp : 응용 프로그램에 대한 진입점을 정의합니다.
//

#include "stdafx.h"
#include "paint1231.h"
#include <windowsx.h>
#define MAX_LOADSTRING 100
#include <iostream>
#include <string.h>
#include "Resource.h"
HDC hdc;
void CreateButton(const WCHAR* name, LONG x, LONG y, LONG width, LONG height, HMENU id, HWND hWnd, HINSTANCE hInst);

void CreateRGB(const WCHAR* name, LONG left, LONG top, LONG right, LONG bottom, HMENU id, HWND hWnd, HINSTANCE hInst);

void SetMode(WPARAM wParam, LPARAM lParam,HWND hWnd);
void SetScrollFunction(WPARAM wParam, LPARAM lParam);
void SetColor(HWND hWnd,HDC hdc);
void CreateBackPage(HWND hWnd, HINSTANCE hInst, HDC* memDC , HBITMAP* memBitmap);
POINT Draw(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam,POINT stPos) ;
POINT Eraser(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam, POINT stPos);

void CreateThicknessTable(const WCHAR* name, LONG left, LONG top, LONG right, LONG bottom, HMENU id, HWND hWnd, HINSTANCE hInst);
void SetThickness(HWND hWnd,HDC hdc);
POINT Drawsquare(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam,POINT stPos) ;
POINT  DrawRectangle(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam);
POINT  DrawCircle(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam);
POINT  FillCircle(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam);
POINT  FillRectangle(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam);

// 전역 변수:
HINSTANCE hInst;								// 현재 인스턴스입니다.
TCHAR szTitle[MAX_LOADSTRING];					// 제목 표시줄 텍스트입니다.
TCHAR szWindowClass[MAX_LOADSTRING];			// 기본 창 클래스 이름입니다.
HDC memDC;
HBITMAP memBitmap;	
POINT stPos;
int thickness = 5;
BOOL bImageChanged = TRUE;
bool circle = FALSE;
bool square = FALSE;
bool pen = FALSE;
bool eraser = FALSE;
BOOL isDrawing = FALSE;
bool fill = FALSE;
int count;


// 이 코드 모듈에 들어 있는 함수의 정방향 선언입니다.
ATOM				MyRegisterClass(HINSTANCE hInstance);
BOOL				InitInstance(HINSTANCE, int);
LRESULT CALLBACK	WndProc(HWND, UINT, WPARAM, LPARAM);
INT_PTR CALLBACK	About(HWND, UINT, WPARAM, LPARAM);

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
	LoadString(hInstance, IDC_PAINT1231, szWindowClass, MAX_LOADSTRING);
	MyRegisterClass(hInstance);

	// 응용 프로그램 초기화를 수행합니다.
	if (!InitInstance (hInstance, nCmdShow))
	{
		return FALSE;
	}

	hAccelTable = LoadAccelerators(hInstance, MAKEINTRESOURCE(IDC_PAINT1231));

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
	wcex.hIcon			= LoadIcon(hInstance, MAKEINTRESOURCE(IDI_PAINT1231));
	wcex.hCursor		= LoadCursor(NULL, IDC_ARROW);
	wcex.hbrBackground	= (HBRUSH)(COLOR_WINDOW+1);
	wcex.lpszMenuName	= NULL;
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
   HWND hWnd;

   hInst = hInstance; // 인스턴스 핸들을 전역 변수에 저장합니다.

   hWnd = CreateWindowW(szWindowClass, szTitle,  WS_MAXIMIZE| WS_SYSMENU | WS_CLIPSIBLINGS | WS_CLIPCHILDREN,
      CW_USEDEFAULT, 0, 1100, 700, NULL, LoadMenu(hInstance,MAKEINTRESOURCE(IDC_PAINT1231)), hInstance, NULL);

   if (!hWnd)
   {
      return FALSE;
   }

   ShowWindow(hWnd, nCmdShow);
   UpdateWindow(hWnd);

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
	ReleaseDC(hWnd, hdc);
	hdc = GetDC(hWnd);
	
	
	
	ReleaseDC(hWnd, hdc);
	switch (message)
	{
	case WM_CREATE:{
		hdc = GetDC(hWnd);
		CreateButton(L"Pen",800,20,50,50,(HMENU)1, hWnd, hInst); 
        CreateButton(L"Erase", 800, 75, 50, 50, (HMENU)2, hWnd, hInst);
		
		CreateButton(L"1",489,75,25,25,(HMENU)15, hWnd, hInst); 
        CreateButton(L"3", 519, 75, 25, 25, (HMENU)16, hWnd, hInst);
		CreateButton(L"5",549,75,25,25,(HMENU)17, hWnd, hInst); 
        CreateButton(L"7", 579, 75, 25, 25, (HMENU)18, hWnd, hInst);
		CreateButton(L"9",609,75,25,25,(HMENU)19, hWnd, hInst); 
		CreateButton(L"ㅇ",855,20,50,50,(HMENU)3, hWnd, hInst); 
        CreateButton(L"ㅁ",855,75,50,50,(HMENU)4, hWnd, hInst); 
		CreateButton(L"fill",910,20,50,105,(HMENU)5, hWnd, hInst); 

        //버튼 생성 및 이미지 씌우기

        //색상 테이블 생성
        CreateRGB(L"RGBtable", 20, 30, 0, 120, (HMENU)10, hWnd, hInst);


		CreateButton(L"red",330,40,25,25,(HMENU)41, hWnd, hInst); 
        CreateButton(L"blue", 360, 40, 25, 25, (HMENU)42, hWnd, hInst);
		CreateButton(L"green",360,75,25,25,(HMENU)44, hWnd, hInst);
		CreateButton(L"black",330,75,25,25,(HMENU)43, hWnd, hInst); 
		 

		//두께 테이블 생성
		CreateThicknessTable(L"Thickness", 80, 30, 160, 120, (HMENU)30, hWnd, hInst);


		CreateBackPage(hWnd, hInst, &memDC , &memBitmap);
		RECT rect;
		GetClientRect(hWnd,&rect);

		SetColor(hWnd,memDC);
		SetThickness(hWnd,memDC);

		SetColor(hWnd,hdc);
		SetThickness(hWnd,hdc);
		ReleaseDC(hWnd,hdc);

		BitBlt(memDC, 0, 0, rect.right, rect.bottom, hdc, 0, 0, SRCCOPY);
			

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
			hdc = GetDC(hWnd);
			
			RECT rect;
			GetClientRect(hWnd,&rect);
			
			
			
			
			PatBlt(memDC,0,0,rect.right, rect.bottom, WHITENESS);
			
			BitBlt(hdc, 0, 0, rect.right, rect.bottom, memDC, 0, 0, SRCCOPY);
			SetColor(hWnd,hdc);
			SetThickness(hWnd,hdc);
			count = -1;
			ReleaseDC(hWnd,hdc);
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
				  break; 
				   }
		case 1:
			pen = TRUE;
			eraser = FALSE;
			circle = FALSE;
			square = FALSE;
			//TextOut(hdc,100,100,L"test1",5);
			break;
		case 2:
			pen = FALSE;
			eraser = TRUE;
			circle = FALSE;
			square = FALSE;
			//TextOut(hdc,100,100,L"test2",5);
			break;
		case 3:
			pen = FALSE;
			eraser = FALSE;
			circle = TRUE;
			square = FALSE;
			//TextOut(hdc,100,100,L"test1",5);
			break;
		case 4:
			pen = FALSE;
			eraser = FALSE;
			circle = TRUE;
			square = TRUE;
			//TextOut(hdc,100,100,L"test2",5);
			break;
		case 5:
			if(fill == TRUE){ fill = FALSE; break;}
			if(fill == FALSE) fill = TRUE;
			break;
		case 15:
			
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"Thickness"),SB_CTL,1,TRUE);
			thickness = 1;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;
		case 16:
			
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"Thickness"),SB_CTL,3,TRUE);
			thickness = 3;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;
		case 17:
			
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"Thickness"),SB_CTL,5,TRUE);
			thickness = 5;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;
		case 18:
		
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"Thickness"),SB_CTL,7,TRUE);
			thickness = 7;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;
		case 19:
			
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"Thickness"),SB_CTL,9,TRUE);
			thickness = 9;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;
		case 41:
			
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"R"),SB_CTL,255,TRUE);
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"G"),SB_CTL,0,TRUE);
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"B"),SB_CTL,0,TRUE);
			SetColor(hWnd,hdc);
			count = -1;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;
		case 42:
		
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"R"),SB_CTL,0,TRUE);
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"G"),SB_CTL,0,TRUE);
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"B"),SB_CTL,255,TRUE);
			SetColor(hWnd,hdc);
			count = -1;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;
		case 43:
			
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"R"),SB_CTL,0,TRUE);
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"G"),SB_CTL,0,TRUE);
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"B"),SB_CTL,0,TRUE);
			SetColor(hWnd,hdc);
			count = -1;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;

		case 44:
			
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"R"),SB_CTL,0,TRUE);
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"G"),SB_CTL,255,TRUE);
			SetScrollPos(FindWindowExW(hWnd,NULL,L"scrollbar", L"B"),SB_CTL,0,TRUE);
			SetColor(hWnd,hdc);
			count = -1;
			InvalidateRect(hWnd, NULL, FALSE);
			UpdateWindow(hWnd);
			ReleaseDC(hWnd, hdc);
			break;
		default:
			return DefWindowProc(hWnd, message, wParam, lParam);
		}
		break;
	case WM_MOUSEMOVE:{
		hdc = GetDC(hWnd);
		
		RECT rect;
		GetClientRect(hWnd,&rect);
		if (wParam == MK_LBUTTON && stPos.y >=150 && stPos.y <= rect.bottom - rect.top && stPos.x > rect.left && stPos.x < rect.right - rect.left){
			if(pen == TRUE){
				stPos = Draw(hWnd,memDC,wParam,lParam,stPos);
				
				
				BitBlt(hdc, 0, 0, rect.right, rect.bottom, memDC, 0, 0,  SRCCOPY);
				ReleaseDC(hWnd, hdc);
			}
			else if(eraser == TRUE){
				stPos = Eraser(hWnd, memDC, wParam, lParam, stPos);
                
				
				BitBlt(hdc, 0, 0, rect.right, rect.bottom, memDC, 0, 0, SRCCOPY);
				ReleaseDC(hWnd, hdc);
			}
			else if(square == TRUE){
				
				if(isDrawing == FALSE){
					isDrawing = TRUE;
				}
				//HDC hdcBuffer;
				//HBITMAP hbmBuffer, hbmOld;
				

    
				//hdcBuffer = CreateCompatibleDC(hdc);
				//hbmBuffer = CreateCompatibleBitmap(hdc, rect.right, rect.bottom);
				//hbmOld = (HBITMAP)SelectObject(hdcBuffer, hbmBuffer);

				BitBlt(hdc, 0, 0, rect.right, rect.bottom, memDC, 0, 0, SRCCOPY);
				if(fill == FALSE)
					DrawRectangle( hWnd,  hdc,  wParam,  lParam);
				else
					FillRectangle(hWnd,hdc,wParam,lParam);

				//BitBlt(memDC, 0, 0, rect.right, rect.bottom, hdc, 0, 0, SRCCOPY);
				
				//BitBlt(hdc, 0, 0, rect.right, rect.bottom, hdcBuffer, 0, 0, SRCCOPY);

				//BitBlt(hdc, 0, 0, rect.right, rect.bottom, memDC, 0, 0, SRCCOPY);
				
				//SelectObject(hdcBuffer, hbmOld);
				//DeleteObject(hbmBuffer);
				//DeleteDC(hdcBuffer);
			}
			else if(circle == TRUE){
				if(isDrawing == FALSE){
					isDrawing = TRUE;
				}
				//HDC hdcBuffer;
				//HBITMAP hbmBuffer, hbmOld;
				

    
				//hdcBuffer = CreateCompatibleDC(hdc);
				//hbmBuffer = CreateCompatibleBitmap(hdc, rect.right, rect.bottom);
				//hbmOld = (HBITMAP)SelectObject(hdcBuffer, hbmBuffer);

				BitBlt(hdc, 0, 0, rect.right, rect.bottom, memDC, 0, 0, SRCCOPY);

				if(fill == FALSE)
					DrawCircle( hWnd,  hdc,  wParam,  lParam);
				else
					FillCircle( hWnd,  hdc,  wParam,  lParam);

				//BitBlt(memDC, 0, 0, rect.right, rect.bottom, hdc, 0, 0, SRCCOPY);
				
				//BitBlt(hdc, 0, 0, rect.right, rect.bottom, hdcBuffer, 0, 0, SRCCOPY);

				//BitBlt(hdc, 0, 0, rect.right, rect.bottom, memDC, 0, 0, SRCCOPY);
				//SelectObject(hdcBuffer, hbmOld);
				//DeleteObject(hbmBuffer);
				//DeleteDC(hdcBuffer);
				
			}
			
		
		}
		break;
					  }

	 case WM_LBUTTONDOWN:
    
        //좌 클릭시 초기 좌표 값 저장
        stPos.x = GET_X_LPARAM(lParam);
        stPos.y = GET_Y_LPARAM(lParam);

		
		RECT rect;
		GetClientRect(hWnd,&rect);

		BitBlt(memDC, 0, 0, rect.right, rect.bottom, hdc, 0, 0, SRCCOPY);

        break;
    
    case WM_LBUTTONUP:
		if(isDrawing == TRUE && square == TRUE){
			//TextOut(memDC,100,100,L"test1",5);
			hdc = GetDC(hWnd);
	
			RECT rect;
			GetClientRect(hWnd,&rect);

			//DrawRectangle( hWnd,  memDC,  wParam,  lParam);
			BitBlt(memDC, 0, 0, rect.right, rect.bottom, hdc, 0, 0, SRCCOPY);
			isDrawing = FALSE;
			ReleaseDC(hWnd,hdc);
		}
		if(isDrawing == TRUE && circle == TRUE){
			//TextOut(memDC,100,100,L"test1",5);
			hdc = GetDC(hWnd);
	
			RECT rect;
			GetClientRect(hWnd,&rect);

			//DrawCircle( hWnd,  memDC,  wParam,  lParam);
			BitBlt(memDC, 0, 0, rect.right, rect.bottom, hdc, 0, 0, SRCCOPY);
			isDrawing = FALSE;
			ReleaseDC(hWnd,hdc);
		}
        break;
    
    case WM_RBUTTONDOWN:
    
        break;
    
    case WM_RBUTTONUP:
    
        break;
    
	case WM_PAINT:
		PAINTSTRUCT ps;
        hdc = BeginPaint(hWnd, &ps);
		
	
		//RECT rect;
		GetClientRect(hWnd,&rect);
		
		
		SetColor(hWnd,memDC);
       
		SetThickness(hWnd,memDC);
		

		
		SetColor(hWnd,hdc);
       
		SetThickness(hWnd,hdc);
		


        EndPaint(hWnd, &ps);
		hdc = GetDC(hWnd);
		if(count <= 0){
		SetColor(hWnd,hdc);
		SetThickness(hWnd,hdc);
		count++;
		}
		ReleaseDC(hWnd,hdc);
		break;
	case WM_DESTROY:
		DeleteObject(memBitmap);
        DeleteDC(memDC);
        PostQuitMessage(0);
		break;
	 case WM_HSCROLL:{
		hdc = GetDC(hWnd);
		HWND hScrollBar = (HWND)lParam;
        int scrollBarId = LOWORD(wParam);
        SetScrollFunction(wParam, lParam);
		if(scrollBarId >=10 && scrollBarId <=12)
			SetColor(hWnd,hdc);
		else{
			thickness = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"Thickness"),SB_CTL);
			wchar_t temp[10];
			wsprintf(temp,L"%d",thickness);
			TextOut(hdc,440,100,temp,lstrlenW(temp));
			SetThickness(hWnd,hdc);
		}
        InvalidateRect(hWnd, NULL, FALSE);
        UpdateWindow(hWnd);
		ReleaseDC(hWnd, hdc);
        break;
					 }
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

void CreateButton(const WCHAR* name,LONG x,LONG y,LONG width ,LONG height, HMENU id, HWND hWnd, HINSTANCE hInst)
{
    CreateWindowW(L"button", name, WS_CHILD | WS_VISIBLE | BS_PUSHBUTTON, x,y,width,height, hWnd, id, hInst,NULL);
}

void CreateRGB(const WCHAR* name, LONG left, LONG top, LONG right, LONG bottom, HMENU id, HWND hWnd, HINSTANCE hInst)
{
    
    //RGB의 스크롤 바 생성 및 범위 설정
    CreateWindowW(L"scrollbar", L"R", WS_CHILD | WS_VISIBLE | SBS_HORZ, right+20, top+10, 180, 15, hWnd, id, hInst, NULL);
    SetScrollRange(FindWindowExW(hWnd,NULL,L"scrollbar", L"R"), SB_CTL, 0, 255, TRUE);
    CreateWindowW(L"scrollbar", L"G", WS_CHILD | WS_VISIBLE | SBS_HORZ, right+20, top+35, 180, 15, hWnd, id+1, hInst, NULL);
    SetScrollRange(FindWindowExW(hWnd,NULL,L"scrollbar", L"G"), SB_CTL, 0, 255, TRUE);
    CreateWindowW(L"scrollbar", L"B", WS_CHILD | WS_VISIBLE | SBS_HORZ, right+20, top+60, 180, 15, hWnd, id+2, hInst, NULL);
    SetScrollRange(FindWindowExW(hWnd,NULL,L"scrollbar", L"B"), SB_CTL, 0, 255, TRUE);
    SetColor(hWnd,GetDC(hWnd));
}


void CreateThicknessTable(const WCHAR* name, LONG left, LONG top, LONG right, LONG bottom, HMENU id, HWND hWnd, HINSTANCE hInst)
{
    
    hdc = GetDC(hWnd);
    HWND ID = CreateWindowW(L"scrollbar", L"Thickness", WS_CHILD | WS_VISIBLE | SBS_HORZ, right+330, top+15, right + 80, 15, hWnd, id, hInst, NULL);
    SetScrollRange(FindWindowExW(hWnd,NULL,L"scrollbar", L"Thickness"), SB_CTL, 0, 99, TRUE);
	SetScrollPos(ID,SB_CTL,5,TRUE);
    SetThickness(hWnd,hdc);
	ReleaseDC(hWnd, hdc);
	return;
}


void SetScrollFunction(WPARAM wParam, LPARAM lParam)
{
	int scrollBarId = LOWORD(wParam);
    switch (LOWORD(wParam))
    {
    case SB_LINELEFT:
        SetScrollPos((HWND)lParam, SB_CTL, max(0,GetScrollPos((HWND)lParam,SB_CTL)-1), TRUE);
		//if(scrollBarId == 13) thickness--;
		//if(thickness <0) thickness = 0;
        break;
    case SB_PAGELEFT:
        SetScrollPos((HWND)lParam, SB_CTL, max(0, GetScrollPos((HWND)lParam, SB_CTL) - 5), TRUE);
		//if(scrollBarId == 13) thickness -=5;
		//if(thickness <0) thickness = 0;
        break;
    case SB_LINERIGHT:
        SetScrollPos((HWND)lParam, SB_CTL, min(255, GetScrollPos((HWND)lParam, SB_CTL) + 1), TRUE);
		//if(scrollBarId == 13) thickness++;
        break;
    case SB_PAGERIGHT:
        SetScrollPos((HWND)lParam, SB_CTL, min(255, GetScrollPos((HWND)lParam, SB_CTL) + 5), TRUE);
		//if(scrollBarId == 13) thickness+=5;
        break;
    case SB_THUMBTRACK:
        SetScrollPos((HWND)lParam, SB_CTL, HIWORD(wParam), TRUE);
		//if(scrollBarId == 13) thickness = HIWORD(wParam);
        break;
    }
}

void SetColor(HWND hWnd,HDC hdc)
{
    int status = 0;
    if (hdc == NULL) {
        hdc = GetDC(hWnd);
        status = 1;
    }


    //스크롤 Bar의 값 받아오기
    int R = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"R"), SB_CTL);
    int G = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"G"), SB_CTL);
    int B = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"B"), SB_CTL);

    HBRUSH newBrush = CreateSolidBrush(RGB(R, G, B));
    HBRUSH OldBrush = (HBRUSH)SelectObject(hdc, newBrush);
    //선택된 색상 보여주기
	
    Rectangle(hdc, 280, 40, 320, 100);

    //스크롤 Bar의 값 표시해주기
    WCHAR text[10];
    wsprintf(text, L"R : %d", R );
	TextOutW(hdc, 210, 40, L"R :         ", 12);
    TextOutW(hdc, 210, 40, text, lstrlenW(text));
    wsprintf(text, L"G : %d", G );
	TextOutW(hdc, 210, 65, L"R :         ", 12);
    TextOutW(hdc, 210, 65, text, lstrlenW(text));
    wsprintf(text, L"B : %d", B );
	TextOutW(hdc, 210, 90, L"R :         ", 12);
    TextOutW(hdc, 210, 90, text, lstrlenW(text));
    SelectObject(hdc, OldBrush);
    DeleteObject(newBrush);
    
    if (status == 1)
    {
        ReleaseDC(hWnd, hdc);
    }
}

void SetThickness(HWND hWnd,HDC hdc)
{
    int status = 0;
    if (hdc == NULL) {
        hdc = GetDC(hWnd);
        status = 1;
    }

	HPEN newPen = CreatePen(PS_SOLID, 100, RGB(255, 255, 255));
    HPEN OldPen = (HPEN)SelectObject(hdc, newPen);
    
	

    MoveToEx(hdc, 430, 70, NULL);
    LineTo(hdc, 430, 70);
    
	SelectObject(hdc, OldPen);
    DeleteObject(newPen);

    newPen = CreatePen(PS_SOLID, thickness, RGB(0, 0, 0));
    OldPen = (HPEN)SelectObject(hdc, newPen);
    

    MoveToEx(hdc, 430, 70, NULL);
    LineTo(hdc, 430, 70);
    
	
    

    //스크롤 Bar의 값 표시해주기
    WCHAR text[10];
    wsprintf(text, L"%d", thickness );
	TextOutW(hdc, 640, 75, L"               ", 12);
    TextOutW(hdc, 640, 75, text, lstrlenW(text));
    
    SelectObject(hdc, OldPen);
    DeleteObject(newPen);
    
    if (status == 1)
    {
        ReleaseDC(hWnd, hdc);
    }
}

void CreateBackPage(HWND hWnd, HINSTANCE hInst, HDC* memDC , HBITMAP* memBitmap)
{
    hdc = GetDC(hWnd);
    *memDC = CreateCompatibleDC(hdc);
    RECT rect;
    GetClientRect(hWnd, &rect);
    *memBitmap = CreateCompatibleBitmap(hdc, rect.right, rect.bottom);
    (HBITMAP)SelectObject(*memDC, *memBitmap);
    FillRect(*memDC, &rect, (HBRUSH)GetStockObject(WHITE_BRUSH));
    ReleaseDC(hWnd, hdc);

}

POINT Draw(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam,POINT stPos) 
{

    //스크롤 Bar의 값 받아오기
    int R = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"R"), SB_CTL);
    int G = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"G"), SB_CTL);
    int B = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"B"), SB_CTL);

    HPEN newPen = CreatePen(PS_SOLID, thickness, RGB(R, G, B));
    HPEN oldPen = (HPEN)SelectObject(hdc, newPen);

    POINT pos;
    pos.x = GET_X_LPARAM(lParam);
    pos.y = GET_Y_LPARAM(lParam);

    MoveToEx(hdc, stPos.x, stPos.y, NULL);
    LineTo(hdc, pos.x, pos.y);

    SelectObject(hdc, oldPen);
    DeleteObject(newPen);

    stPos.x = pos.x;
    stPos.y = pos.y;
	bImageChanged = TRUE;

	


    return stPos;
}





POINT Eraser(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam, POINT stPos)
{
    HPEN newPen = CreatePen(PS_SOLID, thickness, RGB(255, 255, 255));
    HPEN oldPen = (HPEN)SelectObject(hdc, newPen);

    POINT pos;
    pos.x = GET_X_LPARAM(lParam);
    pos.y = GET_Y_LPARAM(lParam);

    MoveToEx(hdc, stPos.x, stPos.y, NULL);
    LineTo(hdc, pos.x, pos.y);

    SelectObject(hdc, oldPen);
    DeleteObject(newPen);

    stPos.x = pos.x;
    stPos.y = pos.y;
	bImageChanged = TRUE;

	


    return stPos;
}

POINT DrawCircle(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam) {
		
        int R = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"R"), SB_CTL);
        int G = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"G"), SB_CTL);
        int B = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"B"), SB_CTL);

        HPEN newPen = CreatePen(PS_SOLID, thickness, RGB(R, G, B));
		HBRUSH hBrush = (HBRUSH)GetStockObject(NULL_BRUSH);

        HPEN oldPen = (HPEN)SelectObject(hdc, newPen);
		HBRUSH hOldBrush = (HBRUSH)SelectObject(hdc, hBrush);

        POINT pos;
        pos.x = GET_X_LPARAM(lParam);
        pos.y = GET_Y_LPARAM(lParam);

       
		
		//TextOut(hdc,100,100,L"test1",5);
		
		
        Ellipse(hdc, stPos.x, stPos.y, pos.x, pos.y);

        SelectObject(hdc, oldPen);
		SelectObject(hdc, hOldBrush);
        DeleteObject(newPen);
		
		
		
		
		
		bImageChanged = TRUE;
		
		return stPos;
}

// 직사각형을 그리는 함수
POINT  DrawRectangle(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam) {
    
        int R = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"R"), SB_CTL);
        int G = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"G"), SB_CTL);
        int B = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"B"), SB_CTL);

        HPEN newPen = CreatePen(PS_SOLID, thickness, RGB(R, G, B));
		HBRUSH hBrush = (HBRUSH)GetStockObject(NULL_BRUSH);

        HPEN oldPen = (HPEN)SelectObject(hdc, newPen);
		HBRUSH hOldBrush = (HBRUSH)SelectObject(hdc, hBrush);

        POINT pos;
        pos.x = GET_X_LPARAM(lParam);
        pos.y = GET_Y_LPARAM(lParam);

       
		
		//TextOut(hdc,100,100,L"test1",5);
		
		
        Rectangle(hdc, stPos.x, stPos.y, pos.x, pos.y);

        SelectObject(hdc, oldPen);
		SelectObject(hdc, hOldBrush);
        DeleteObject(newPen);
		
		
		
		
		
		bImageChanged = TRUE;
		
		return stPos;
}

POINT  FillRectangle(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam) {
    
        int R = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"R"), SB_CTL);
        int G = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"G"), SB_CTL);
        int B = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"B"), SB_CTL);

        HPEN newPen = CreatePen(PS_SOLID, 1, RGB(R,G,B));
		HBRUSH hBrush = CreateSolidBrush(RGB(R,G,B));

        HPEN oldPen = (HPEN)SelectObject(hdc, newPen);
		HBRUSH hOldBrush = (HBRUSH)SelectObject(hdc, hBrush);

        POINT pos;
        pos.x = GET_X_LPARAM(lParam);
        pos.y = GET_Y_LPARAM(lParam);

       
		
		//TextOut(hdc,100,100,L"test1",5);
		
		
        Rectangle(hdc, stPos.x, stPos.y, pos.x, pos.y);

        SelectObject(hdc, oldPen);
		SelectObject(hdc, hOldBrush);
        DeleteObject(newPen);
		
		DeleteObject(hBrush);
		
		
		
		bImageChanged = TRUE;
		
		return stPos;
}

POINT  FillCircle(HWND hWnd, HDC hdc, WPARAM wParam, LPARAM lParam) {
    
        int R = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"R"), SB_CTL);
        int G = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"G"), SB_CTL);
        int B = GetScrollPos(FindWindowExW(hWnd, NULL, L"scrollbar", L"B"), SB_CTL);

        HPEN newPen = CreatePen(PS_SOLID, 1, RGB(R,G,B));
		HBRUSH hBrush = CreateSolidBrush(RGB(R,G,B));

        HPEN oldPen = (HPEN)SelectObject(hdc, newPen);
		HBRUSH hOldBrush = (HBRUSH)SelectObject(hdc, hBrush);

        POINT pos;
        pos.x = GET_X_LPARAM(lParam);
        pos.y = GET_Y_LPARAM(lParam);

       
		
		//TextOut(hdc,100,100,L"test1",5);
		
		
        Ellipse(hdc, stPos.x, stPos.y, pos.x, pos.y);

        SelectObject(hdc, oldPen);
		SelectObject(hdc, hOldBrush);
        DeleteObject(newPen);
		
		DeleteObject(hBrush);
		
		
		
		bImageChanged = TRUE;
		
		return stPos;
}
