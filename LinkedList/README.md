flowchart TD
    A["Object 입력: scanf('%lld', &Num_tmp2)"] --> B{scanf 반환값 == 1?}
    B -- 아니오(타입 에러) --> C[오류 메시지]
    C --> D[버퍼 비우기]
    D --> E[메뉴로 복귀]

    B -- 예 --> F{INT_MIN <= Num_tmp2 <= INT_MAX ?}
    F -- 아니오(Overflow/Underflow) --> G[오버/언더플로우 메시지]
    G --> E

    F -- 예 --> H[int로 안전 변환/사용]
    H --> I[연결리스트 연산 수행]
