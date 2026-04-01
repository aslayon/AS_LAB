// --- Global UI Variables ---
const DEFAULT_IMAGE_URL = '/static/images/default_npc.png';
window.reportMode = null;
window.isEditMode = false;
window.popupFetchController = null;

// --- Helper Functions ---
function showToast(message) {
    const existingToast = document.querySelector('.toast-notification');
    if (existingToast) {
        existingToast.remove();
    }

    const toast = document.createElement('div');
    toast.className = 'toast-notification';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function addToastStyles() {
    const styleId = 'toast-styles';
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
    style.innerHTML = `
        .toast-notification {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(0, 0, 0, 0.7);
            color: #fff;
            padding: 10px 20px;
            border-radius: 20px;
            z-index: 10000;
            font-size: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            transition: bottom 0.5s, opacity 0.5s;
        }
        #search-ui-container {
            position: absolute;
            top: 16px;
            left: 16px;
            z-index: 1000;
            width: min(360px, calc(100vw - 32px));
        }
        #search-panel {
            /* 라이트 글래스(덜 하얗게): 톤을 내려서 지도 위에서 튀지 않게 */
            background: rgba(230, 232, 238, 0.80);
            border: 1px solid rgba(10, 10, 20, 0.14);
            border-radius: 14px;
            padding: 12px;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
        }

        /* 패널 내부 요소 정렬(상하/좌우) */
        #search-panel * {
            box-sizing: border-box;
        }

        #map-search-input {
            width: 100%;
            margin: 0; /* 브라우저 기본 margin 제거 */
            /* 텍스트가 위로 뜨는 느낌이면 상하 패딩을 비대칭으로 살짝 보정 */
            padding: 12px 12px 10px;
            line-height: 20px;  /* 텍스트 수직정렬 안정화 */
            border: 1px solid rgba(10, 10, 20, 0.16);
            border-radius: 12px;
            color: #121318;
            background: rgba(245, 246, 249, 0.78);
            box-sizing: border-box;
        }

        #map-search-input::placeholder {
            color: rgba(18, 19, 24, 0.45);
        }

        #map-search-input:focus {
            outline: none;
            border-color: rgba(255, 200, 0, 0.9);
            box-shadow: 0 0 0 3px rgba(255, 200, 0, 0.25);
        }
        #search-results {
            margin-top: 8px;
            max-height: 260px;
            overflow-y: auto;
            padding: 2px; /* 가장자리 딱 붙는 느낌 완화 */
        }
        .search-result-item {
            padding: 10px;
            border-radius: 10px;
            color: #121318;
            cursor: pointer;
        }
        .search-result-item:hover {
            background: rgba(10, 10, 20, 0.06);
        }
        .search-result-title {
            font-size: 14px;
            font-weight: 700;
        }
        .search-result-meta {
            font-size: 12px;
            color: #666;
            margin-top: 4px;
        }
    `;
    document.head.appendChild(style);
}

addToastStyles();

// --- UI Setup & Event Listeners ---
function setupReportMenu() {
    const reportBtn = document.getElementById('reportBtn');
    const reportMenu = document.getElementById('reportMenu');

    reportBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
        reportMenu.style.display = reportMenu.style.display === 'block' ? 'none' : 'block';
    });

    document.addEventListener('click', () => {
        if (reportMenu.style.display === 'block') {
            reportMenu.style.display = 'none';
        }
    });

    reportMenu.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

function updateReportButtonState() {
    const reportBtn = document.getElementById('reportBtn');
    if (!reportBtn) return;

    if (window.reportMode) {
        reportBtn.textContent = '제보 모드';
        reportBtn.classList.add('active-mode');
    } else {
        reportBtn.textContent = '데이터 제보';
        reportBtn.classList.remove('active-mode');
    }
}

function updateEditModeMenuState() {
    // index.html의 "마커 위치 수정" 메뉴가 inline onclick 이라,
    // 클릭 전에는 비활성화가 적용되지 않아서, 스타일/상태는 여기서 DOM을 직접 건드린다.
    const reportMenu = document.getElementById('reportMenu');
    if (!reportMenu) return;

    const nodes = Array.from(reportMenu.querySelectorAll('div'));
    const editNode = nodes.find((n) => (n.textContent || '').trim() === '마커 위치 수정');
    if (!editNode) return;

    if (window.isEditMode) {
        editNode.classList.add('active-mode');
        editNode.setAttribute('aria-pressed', 'true');
    } else {
        editNode.classList.remove('active-mode');
        editNode.setAttribute('aria-pressed', 'false');
    }
}

function toggleEditMode() {
    window.isEditMode = !window.isEditMode;

    if (window.isEditMode) {
        window.reportMode = null;
    }

    Object.values(window.markerLayers || {}).forEach((layer) => {
        layer.eachLayer((marker) => {
            applyMarkerDraggableState(marker);
        });
    });

    updateReportButtonState();
    updateEditModeMenuState();
    showToast(window.isEditMode ? '마커 편집 모드 활성화' : '마커 편집 모드 종료');
}

function setReportMode(mode) {
    // 모드가 켜질 때 편집모드가 켜져있으면 끈다.
    if (mode && window.isEditMode) {
        toggleEditMode();
    }

    // (버그 수정) "모드 취소"(mode=null)일 때도 편집모드를 확실히 종료해야 함
    // 그렇지 않으면 '마커 위치 수정'이 계속 활성 상태로 남는다.
    if (!mode && window.isEditMode) {
        window.isEditMode = false;
        Object.values(window.markerLayers || {}).forEach((layer) => {
            layer.eachLayer((marker) => {
                applyMarkerDraggableState(marker);
            });
        });
        showToast('마커 편집 모드 종료');
    }

    // (중요) setReportMode는 두 파일(map_logic.js / ui_handlers.js)에 동시에 존재한다.
    // 여기서 window.setReportMode(...)로 "동기화"를 시도하면, 실제로는 자기 자신을 호출하며
    // 재귀에 빠지거나(try/catch로 조용히 삼켜짐), reportMode가 기대대로 설정되지 않는 케이스가 발생한다.
    window.reportMode = mode;
    try {
        window.__lastReportModeSetAt = new Date().toISOString();
    } catch {}

    try {
        console.log('[reportMode] set', {
            mode,
            from: 'ui_handlers.js',
            windowSetReportModeName: window.setReportMode?.name,
            sameRef: window.setReportMode === setReportMode,
        });
    } catch {}

    document.getElementById('reportMenu').style.display = 'none';

    const mapContainer = document.getElementById('map');
    mapContainer.style.cursor = mode === 'new-marker' || mode === 'new-zone' ? 'crosshair' : '';

    // "모드 취소" 시 열려있는 팝업(신규마커 제보 폼 등)도 함께 닫아줌
    // 단, new-zone 드래그 직후에는 popup이 잠깐 보였다가 사라지는 문제가 있어
    // 일정 시간 동안(close lock) closePopup을 무시한다.
    if (!mode && window.map) {
        const lockUntil = window.__newZonePopupLockUntil || 0;
        if (Date.now() < lockUntil) {
            console.log('[new-zone-ui] closePopup skipped by lock', { lockUntil });
        } else {
            window.map.closePopup();
        }
    }

    updateReportButtonState();
    updateEditModeMenuState();

    if (mode === 'add-item-master') {
        showItemMasterForm();
        window.reportMode = null;
        updateReportButtonState();
        if (typeof window.setReportMode === 'function' && window.setReportMode !== setReportMode) {
            try {
                window.setReportMode(null);
            } catch {}
        }
    }

    if (mode === 'update-item-image') {
        showUpdateItemImageForm();
        window.reportMode = null;
        updateReportButtonState();
        if (typeof window.setReportMode === 'function' && window.setReportMode !== setReportMode) {
            try {
                window.setReportMode(null);
            } catch {}
        }
    }

    if (mode === 'update-item-name') {
        showUpdateItemNameForm();
        window.reportMode = null;
        updateReportButtonState();
        if (typeof window.setReportMode === 'function' && window.setReportMode !== setReportMode) {
            try {
                window.setReportMode(null);
            } catch {}
        }
    }

    if (mode === 'update-map-image') {
        showUpdateMapImageForm();
        window.reportMode = null;
        updateReportButtonState();
        if (typeof window.setReportMode === 'function' && window.setReportMode !== setReportMode) {
            try {
                window.setReportMode(null);
            } catch {}
        }
    }
}

async function openNpcPopup(marker, npc, event) {
    if (event) {
        L.DomEvent.stopPropagation(event);
    }

    if (window.isEditMode) return;

    if (window.popupFetchController) {
        window.popupFetchController.abort();
    }

    const controller = new AbortController();
    window.popupFetchController = controller;

    if (marker.getPopup()) {
        marker.unbindPopup();
    }

    const loadingContent = `
        <div class="popup-content" style="min-width: 300px;">
            <h3>🏪 ${npc.name || '이름 없음'}</h3>
            <p>아이템 정보 로딩 중...</p>
        </div>
    `;
    marker.bindPopup(loadingContent).openPopup();

    try {
        const items = await fetchMarkerItems(npc.id, controller.signal);

        if (controller.signal.aborted || !marker.isPopupOpen()) return;

        const fullContent = `
            <div class="popup-content" style="min-width: 300px;">
                <div style="display:flex;align-items:center;justify-content:space-between;gap:10px;">
                    <h3 style="margin:0;">🏪 ${npc.name || '이름 없음'}</h3>
                    <div style="display:flex;align-items:center;gap:6px;">
                        <button type="button" id="btn-report-marker-${npc.id}" title="마커 신고" style="padding:4px 8px;background:#c55a5a;color:white;border:none;border-radius:999px;cursor:pointer;font-size:12px;line-height:1;">
                            🚨
                        </button>
                        <button type="button" id="btn-update-marker-image-${npc.id}" title="마커 이미지 재업로드" style="padding:4px 8px;background:#6b6b6b;color:white;border:none;border-radius:999px;cursor:pointer;font-size:12px;line-height:1;">
                            이미지
                        </button>
                        <input type="file" id="file-update-marker-image-${npc.id}" accept="image/*" style="display:none;">
                    </div>
                </div>

                <img src="${npc.image_url || DEFAULT_IMAGE_URL}" alt="${npc.name || ''}" style="width:100%;max-height:150px;object-fit:cover;border-radius:4px;margin:10px 0 10px;" onerror="this.src='${DEFAULT_IMAGE_URL}';">

                <p style="font-size:14px;color:#555;white-space:pre-wrap;margin:0;">${npc.description || '세부 정보 없음'}</p>
                <div id="item-list-container-${npc.id}" style="margin-top:15px;border-top:1px solid #eee;padding-top:10px;"></div>
            </div>
        `;
        marker.getPopup().setContent(fullContent);

        // 마커 신고 / 이미지 업데이트 버튼 바인딩
        try {
            const popupEl = marker.getPopup().getElement();

            const reportBtn = popupEl.querySelector(`#btn-report-marker-${npc.id}`);
            if (reportBtn) {
                reportBtn.addEventListener('click', async (e) => {
                    e.stopPropagation();
                    e.preventDefault();

                    const ok = confirm('이 마커를 신고할까요? (누적 5회 이상이면 지도/검색에서 숨김 처리됩니다)');
                    if (!ok) return;

                    try {
                        const result = await reportMarker(npc.id);
                        alert(result.message || '신고 완료');

                        // 누적 5회 이상이면 서버가 다음 /markers 응답에서 제외하므로
                        // 즉시 UX를 위해: 팝업 닫고, 현재 area 마커를 리로드한다.
                        if (result.hidden) {
                            try {
                                window.map.closePopup();
                            } catch {}

                            const area = window.MAP_CONFIG?.[window.currentMapId]?.areaForMarkers;
                            if (area && typeof loadNPCMarkers === 'function') {
                                await loadNPCMarkers(area);
                            }
                        }
                    } catch (err) {
                        console.error('reportMarker failed:', err);
                        alert(`신고 실패: ${err.message}`);
                    }
                });
            }

            const btn = popupEl.querySelector(`#btn-update-marker-image-${npc.id}`);
            const fileInput = popupEl.querySelector(`#file-update-marker-image-${npc.id}`);

            if (btn && fileInput) {
                btn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    fileInput.click();
                });

                fileInput.addEventListener('change', async (e) => {
                    const file = e.target?.files?.[0];
                    if (!file) return;

                    try {
                        const result = await updateMarkerImage(npc.id, file);
                        alert(result.message || '업데이트 완료');

                        // 팝업 이미지 즉시 갱신(캐시 우회용 querystring 추가)
                        const img = popupEl.querySelector('img');
                        if (img && result.image_url) {
                            img.src = `${result.image_url}?v=${Date.now()}`;
                        }
                    } catch (err) {
                        console.error('updateMarkerImage failed:', err);
                        alert(`업데이트 실패: ${err.message}`);
                    } finally {
                        // 같은 파일 재선택 가능하도록 초기화
                        try {
                            fileInput.value = '';
                        } catch {}
                    }
                });
            }
        } catch (e) {
            console.error('Failed to bind marker image update UI:', e);
        }

        const container = marker.getPopup().getElement().querySelector(`#item-list-container-${npc.id}`);
        if (!container) {
            throw new Error('Popup container not found in DOM');
        }

        let itemsHtml = '<ul style="list-style:none;padding:0;margin:0;max-height:200px;overflow-y:auto;">';
        if (items.length === 0) {
            itemsHtml += '<li style="font-size:13px;color:#888;">정보가 없습니다.</li>';
        } else {
            items.forEach((item) => {
                const price = item.price_value ? `${item.price_value.toLocaleString()} ${item.price_type}` : (item.price_type || '');
                const condition = item.acquisition_condition ? `<br><small style="color:#888;">(${item.acquisition_condition})</small>` : '';
                const dislikeBtn = `<button type="button" onclick="dislikeItemSource(${item.source_id})" style="background:none;border:none;font-size:14px;padding:0 5px;margin-left:8px;cursor:pointer;line-height:1;">🚨</button>`;
                itemsHtml += `
                    <li id="source-li-${item.source_id}" style="display:flex;align-items:center;margin-bottom:8px;font-size:14px;">
                        <img src="${item.image_url || DEFAULT_IMAGE_URL}" style="width:28px;height:28px;margin-right:8px;" onerror="this.src='${DEFAULT_IMAGE_URL}';">
                        <span style="flex-grow:1;">${item.item_name}${condition}</span>
                        <span style="color:#666;font-size:13px;">${price}</span>
                        ${dislikeBtn}
                    </li>
                `;
            });
        }
        itemsHtml += '</ul>';

        container.innerHTML = `
            <h4 style="margin:0 0 10px;">판매/획득 아이템</h4>
            ${itemsHtml}
            <button type="button" onclick="showReportFormForMarker(${npc.id}, '${String(npc.name || '').replace(/'/g, "\\'")}')" style="width:100%;padding:8px;margin-top:10px;background:#5a87c5;color:white;border:none;border-radius:4px;">이 위치에 정보 제보</button>
        `;
    } catch (err) {
        if (err.name !== 'AbortError') {
            console.error('Failed to get or render popup data:', err);
            if (marker.isPopupOpen()) {
                marker.getPopup().setContent('<div>데이터를 불러오는 데<br>실패했습니다.</div>');
            }
        }
    }
}

async function dislikeItemSource(source_id) {
    try {
        await postDislike(source_id);
        alert('신고되었습니다.');
        const listItem = document.getElementById(`source-li-${source_id}`);
        if (listItem) {
            listItem.remove();
        }
    } catch (e) {
        console.error('Failed to dislike item source:', e);
        alert(`신고 처리 중 오류가 발생했습니다: ${e.message}`);
    }
}

﻿// --- Debounce & Autocomplete ---
const debounce = (func, delay) => {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(this, args), delay);
    };
};

// IME(한글 입력기) 조합 중에는 input 이벤트가 여러 번 발생하며,
// 그 사이에 자동완성 fetch/DOM 갱신이 끼어들면 값이 "레레몬/레몬몬"처럼 중복되는 버그가 생길 수 있다.
// 따라서 composition 중에는 자동완성을 막고, compositionend 시점에 한 번만 실행한다.
window.__isComposingIme = false;

function bindImeCompositionGuard(inputEl, { onCommit } = {}) {
    if (!inputEl || inputEl.__imeGuardBound) return;
    inputEl.__imeGuardBound = true;

    inputEl.addEventListener('compositionstart', () => {
        window.__isComposingIme = true;
    });

    inputEl.addEventListener('compositionend', (e) => {
        window.__isComposingIme = false;
        // 조합이 끝난 후 최종 값으로 1회만 자동완성 실행
        if (typeof onCommit === 'function') {
            onCommit(e);
        }
    });
}

// datalist는 "옵션을 클릭해 선택"해도 브라우저/상황에 따라 change가 안 뜨는 케이스가 있어,
// input/keydown(Enter/Tab)/blur 등에서 "정확 일치" 시 resolve를 재시도해준다.
function bindDatalistResolveOnExactMatch(inputEl, { resolve, onResolved, onUnresolved } = {}) {
    if (!inputEl || inputEl.__datalistResolveBound) return;
    inputEl.__datalistResolveBound = true;

    const run = async () => {
        if (window.__isComposingIme) return;

        const name = (inputEl.value || '').trim();
        if (!name) {
            if (typeof onUnresolved === 'function') onUnresolved(name);
            return;
        }

        try {
            const resolved = await resolve(name);
            if (typeof onResolved === 'function') onResolved(resolved);
        } catch (err) {
            if (typeof onUnresolved === 'function') onUnresolved(name, err);
        }
    };

    inputEl.addEventListener('input', () => {
        // datalist option 클릭도 보통 input은 발생하므로 여기서도 resolve 시도
        run();
    });

    inputEl.addEventListener('change', () => {
        run();
    });

    inputEl.addEventListener('blur', () => {
        run();
    });

    inputEl.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === 'Tab') {
            // 탭/엔터로 확정할 때도 resolve
            setTimeout(() => run(), 0);
        }
    });
}

async function handleItemAutocomplete(event) {
    // 조합 중에는 자동완성 금지 (중복 입력/값 꼬임 방지)
    if (window.__isComposingIme) return;

    const input = event.target.value;
    const dataList = document.getElementById(event.target.getAttribute('list'));
    if (!input || input.length < 1 || !dataList) {
        dataList.innerHTML = '';
        return;
    }

    try {
        const items = await fetchItemAutocomplete(input);
        dataList.innerHTML = '';
        items.forEach((item) => dataList.insertAdjacentHTML('beforeend', `<option value="${item}"></option>`));
    } catch (e) {
        console.error('Autocomplete fetch failed:', e);
    }
}

const debouncedAutocomplete = debounce(handleItemAutocomplete, 300);
const debouncedSearch = debounce(async (keyword) => {
    await performSearch(keyword);
}, 250);

// --- Form & Report Handling ---
function showItemMasterForm(prefilledName = '', resumeData = null) {
    const formHtml = `
        <div style="padding:5px;min-width:260px;">
            <h4>아이템 등록</h4>
            <p style="font-size:13px;color:#666;margin-bottom:15px;">아이템 이름과 이미지를 등록합니다.</p>

            <div style="margin-bottom:10px;">
                <label>아이템 이름*:</label><br>
                <input type="text" id="master-item-name" value="${prefilledName}" style="width:95%;padding:6px;margin-top:4px;">
            </div>

            <div style="margin-bottom:15px;">
                <label>이미지 (선택):</label><br>
                <input type="file" id="master-item-image" accept="image/*" style="width:95%;padding:6px;margin-top:4px;">
            </div>

            <button type="button" id="send-master-btn" style="width:100%;padding:10px;background:#4CAF50;color:white;border:none;border-radius:4px;">신규 등록</button>
        </div>
    `;
    L.popup().setLatLng(window.map.getCenter()).setContent(formHtml).openOn(window.map);

    const sendBtn = document.getElementById('send-master-btn');
    if (sendBtn) {
        sendBtn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            sendItemMaster(resumeData);
        };
    }
}

function showUpdateItemImageForm() {
    const formHtml = `
        <div style="padding:5px;min-width:260px;">
            <h4>아이템 이미지 수정</h4>
            <p style="font-size:12px;color:#666;margin:0 0 10px;">
                아이템 <b>이름</b>을 검색/자동완성으로 선택하면 ID가 자동으로 바인딩됩니다.
            </p>

            <div style="margin-bottom:10px;">
                <label>아이템 이름*:</label><br>
                <input type="text" id="update-item-name" placeholder="예: 감자" list="update-item-name-suggestions" oninput="debouncedAutocomplete(event)" autocomplete="off" style="width:95%;padding:6px;margin-top:4px;">
                <datalist id="update-item-name-suggestions"></datalist>
            </div>

            <div id="update-item-bind-status" style="font-size:12px;color:#777;margin:-4px 0 10px;">
                선택된 아이템: (없음)
            </div>

            <div style="margin-bottom:12px;">
                <label>새 이미지*:</label><br>
                <input type="file" id="update-item-image" accept="image/*" style="width:95%;padding:6px;margin-top:4px;">
            </div>

            <button type="button" id="update-item-image-btn" style="width:100%;padding:10px;background:#5a87c5;color:white;border:none;border-radius:4px;">이미지 업데이트</button>
        </div>
    `;

    L.popup().setLatLng(window.map.getCenter()).setContent(formHtml).openOn(window.map);

    // 이름 -> id 자동 바인딩 상태
    window.__updateItemBound = window.__updateItemBound || { id: null, name: null };

    const nameInput = document.getElementById('update-item-name');
    const statusEl = document.getElementById('update-item-bind-status');

    // IME 조합 가드
    bindImeCompositionGuard(nameInput, { onCommit: (e) => debouncedAutocomplete(e) });

    const setBindStatus = (text) => {
        if (statusEl) statusEl.textContent = text;
    };

    const tryResolveByName = async () => {
        const name = (nameInput?.value || '').trim();
        window.__updateItemBound = { id: null, name: name || null };
        setBindStatus('선택된 아이템: (없음)');

        if (!name) return;

        try {
            const resolved = await resolveItemByName(name);
            window.__updateItemBound = { id: resolved.id, name: resolved.item_name };
            setBindStatus(`선택된 아이템: ${resolved.item_name} (ID: ${resolved.id})`);
        } catch (err) {
            window.__updateItemBound = { id: null, name };
            setBindStatus(`선택된 아이템: (미확인) — 자동완성에서 정확한 이름을 선택하세요`);
        }
    };

    if (nameInput) {
        nameInput.addEventListener('change', () => {
            tryResolveByName();
        });
        nameInput.addEventListener('blur', () => {
            tryResolveByName();
        });

        // datalist 선택 방식(부분 입력 후 클릭 / 전체 입력 후 클릭) 모두에서 안정적으로 바인딩
        bindDatalistResolveOnExactMatch(nameInput, {
            resolve: resolveItemByName,
            onResolved: (resolved) => {
                window.__updateItemBound = { id: resolved.id, name: resolved.item_name };
                setBindStatus(`선택된 아이템: ${resolved.item_name} (ID: ${resolved.id})`);
            },
            onUnresolved: () => {
                // 기존 tryResolveByName가 처리하므로 여기서는 조용히 둔다.
            },
        });
    }

    const updateBtn = document.getElementById('update-item-image-btn');
    if (updateBtn) {
        updateBtn.onclick = async (e) => {
            e.stopPropagation();
            e.preventDefault();

            await tryResolveByName();

            const id = window.__updateItemBound?.id;
            const fileInput = document.getElementById('update-item-image');
            const file = fileInput?.files?.[0];

            if (!id) {
                alert('아이템 이름을 자동완성에서 정확히 선택해주세요. (ID 바인딩 실패)');
                return;
            }
            if (!file) {
                alert('업로드할 이미지를 선택해주세요.');
                return;
            }

            try {
                const result = await updateItemImage(id, file);
                alert(result.message || '업데이트 완료');
            } catch (err) {
                console.error('updateItemImage failed:', err);
                alert(`업데이트 실패: ${err.message}`);
            }
        };
    }
}

function showUpdateItemNameForm() {
    const formHtml = `
        <div style="padding:5px;min-width:260px;">
            <h4>아이템 이름 변경</h4>
            <p style="font-size:12px;color:#666;margin:0 0 10px;">
                기존 이름을 자동완성에서 선택하면 ID가 바인딩됩니다.<br>
                그 다음 새 이름을 입력하면 items.item_name 이 변경됩니다.
            </p>

            <div style="margin-bottom:10px;">
                <label>기존 아이템 이름*:</label><br>
                <input type="text" id="rename-item-old-name" placeholder="예: 감자" list="rename-item-old-name-suggestions" oninput="debouncedAutocomplete(event)" autocomplete="off" style="width:95%;padding:6px;margin-top:4px;">
                <datalist id="rename-item-old-name-suggestions"></datalist>
            </div>

            <div id="rename-item-bind-status" style="font-size:12px;color:#777;margin:-4px 0 10px;">
                선택된 아이템: (없음)
            </div>

            <div style="margin-bottom:12px;">
                <label>새 아이템 이름*:</label><br>
                <input type="text" id="rename-item-new-name" placeholder="새 이름" autocomplete="off" style="width:95%;padding:6px;margin-top:4px;">
            </div>

            <button type="button" id="rename-item-btn" style="width:100%;padding:10px;background:#5a87c5;color:white;border:none;border-radius:4px;">이름 변경</button>
        </div>
    `;

    L.popup().setLatLng(window.map.getCenter()).setContent(formHtml).openOn(window.map);

    window.__renameItemBound = window.__renameItemBound || { id: null, name: null };

    const oldNameInput = document.getElementById('rename-item-old-name');
    const newNameInput = document.getElementById('rename-item-new-name');
    const statusEl = document.getElementById('rename-item-bind-status');

    // IME 조합 가드
    bindImeCompositionGuard(oldNameInput, { onCommit: (e) => debouncedAutocomplete(e) });

    const setBindStatus = (text) => {
        if (statusEl) statusEl.textContent = text;
    };

    const tryResolveByName = async () => {
        const name = (oldNameInput?.value || '').trim();
        window.__renameItemBound = { id: null, name: name || null };
        setBindStatus('선택된 아이템: (없음)');

        if (!name) return;

        try {
            const resolved = await resolveItemByName(name);
            window.__renameItemBound = { id: resolved.id, name: resolved.item_name };
            setBindStatus(`선택된 아이템: ${resolved.item_name} (ID: ${resolved.id})`);
        } catch (err) {
            window.__renameItemBound = { id: null, name };
            setBindStatus(`선택된 아이템: (미확인) — 자동완성에서 정확한 이름을 선택하세요`);
        }
    };

    if (oldNameInput) {
        oldNameInput.addEventListener('change', () => {
            tryResolveByName();
        });
        oldNameInput.addEventListener('blur', () => {
            tryResolveByName();
        });

        // datalist 선택 방식(부분 입력 후 클릭 / 전체 입력 후 클릭) 모두에서 안정적으로 바인딩
        bindDatalistResolveOnExactMatch(oldNameInput, {
            resolve: resolveItemByName,
            onResolved: (resolved) => {
                window.__renameItemBound = { id: resolved.id, name: resolved.item_name };
                setBindStatus(`선택된 아이템: ${resolved.item_name} (ID: ${resolved.id})`);
            },
            onUnresolved: () => {
                // 기존 tryResolveByName가 처리하므로 여기서는 조용히 둔다.
            },
        });
    }

    const btn = document.getElementById('rename-item-btn');
    if (btn) {
        btn.onclick = async (e) => {
            e.stopPropagation();
            e.preventDefault();

            await tryResolveByName();

            const id = window.__renameItemBound?.id;
            const newName = (newNameInput?.value || '').trim();

            if (!id) {
                alert('기존 아이템 이름을 자동완성에서 정확히 선택해주세요. (ID 바인딩 실패)');
                return;
            }
            if (!newName) {
                alert('새 아이템 이름을 입력해주세요.');
                return;
            }

            const ok = confirm(`아이템 이름을 변경할까요?\n- ID: ${id}\n- 새 이름: ${newName}`);
            if (!ok) return;

            try {
                const result = await updateItemName(id, newName);
                alert(result.message || '변경 완료');
                showToast('아이템 이름이 변경되었습니다.');
                try {
                    window.map.closePopup();
                } catch {}
            } catch (err) {
                console.error('updateItemName failed:', err);
                alert(`변경 실패: ${err.message}`);
            }
        };
    }
}

function showUpdateMapImageForm() {
    const currentMapId = window.currentMapId;
    if (!currentMapId) {
        alert('현재 맵 ID를 찾을 수 없습니다.');
        return;
    }

    const formHtml = `
        <div style="padding:5px;min-width:260px;">
            <h4>현재 맵 이미지 교체</h4>
            <p style="font-size:12px;color:#666;margin:0 0 10px;">
                현재 맵 ID: <b>${currentMapId}</b><br>
                이미지를 업로드하면 maps.img_path가 갱신되고, 즉시 화면에 반영됩니다.
            </p>

            <div style="margin-bottom:12px;">
                <label>새 이미지*:</label><br>
                <input type="file" id="update-map-image-file" accept="image/*" style="width:95%;padding:6px;margin-top:4px;">
            </div>

            <button type="button" id="update-map-image-btn" style="width:100%;padding:10px;background:#5a87c5;color:white;border:none;border-radius:4px;">맵 이미지 업데이트</button>
        </div>
    `;

    L.popup().setLatLng(window.map.getCenter()).setContent(formHtml).openOn(window.map);

    const btn = document.getElementById('update-map-image-btn');
    if (btn) {
        btn.onclick = async (e) => {
            e.stopPropagation();
            e.preventDefault();

            const fileInput = document.getElementById('update-map-image-file');
            const file = fileInput?.files?.[0];
            if (!file) {
                alert('업로드할 이미지를 선택해주세요.');
                return;
            }

            try {
                const result = await updateMapImage(currentMapId, file);
                alert(result.message || '업데이트 완료');

                // config 다시 받기 + 현재 맵 즉시 리로드
                window.MAP_CONFIG = await fetchMapConfig();
                await loadMap(currentMapId, { syncUrl: false, historyMode: 'replace' });

                showToast('맵 이미지가 업데이트되었습니다.');
            } catch (err) {
                console.error('updateMapImage failed:', err);
                alert(`업데이트 실패: ${err.message}`);
            } finally {
                try {
                    fileInput.value = '';
                } catch {}
            }
        };
    }
}

async function sendItemMaster(resumeData = null) {
    const itemName = document.getElementById('master-item-name').value;
    const imageInput = document.getElementById('master-item-image');
    const imageFile = imageInput.files[0];

    if (!itemName) {
        alert('아이템 이름을 입력해주세요.');
        return;
    }

    const formData = new FormData();
    formData.append('itemName', itemName);
    if (imageFile) {
        formData.append('image', imageFile);
    }

    try {
        const result = await postItemMaster(formData);
        alert(result.message);

        if (result.status === 'success') {
            window.map.closePopup();
            if (resumeData) {
                showReportFormForMarker(resumeData.markerId, resumeData.markerName, itemName);
            }
        }
    } catch (e) {
        console.error('Failed to send item master:', e);
        alert(`등록 중 오류가 발생했습니다: ${e.message}`);
    }
}

function showReportFormForMarker(markerId, markerName, prefilledItemName = '') {
    const dataListId = `item-suggestions-${markerId}`;
    const formHtml = `
        <div style="padding:5px;min-width:220px;">
            <h4>'${markerName}' 아이템 제보</h4>
            <div style="margin-bottom:10px;">
                <label>아이템 이름*:</label><br>
                <input type="text" id="report-item-name-${markerId}" value="${prefilledItemName}" list="${dataListId}" oninput="debouncedAutocomplete(event)" autocomplete="off" style="width:95%;padding:4px;">
                <datalist id="${dataListId}"></datalist>
            </div>
            <div style="margin-bottom:10px;">
                <label>획득 방식:</label><br>
                <select id="report-acquire-method-${markerId}" style="width:100%;padding:4px;">
                    <option value="상점">상점</option>
                    <option value="채집">채집</option>
                    <option value="드랍">드랍</option>
                    <option value="기타">기타</option>
                </select>
            </div>
            <div style="margin-bottom:10px;">
                <label>가격:</label>
                <div style="display:flex;gap:5px;">
                    <input type="number" id="report-price-value-${markerId}" placeholder="가격" style="flex:2;padding:4px;min-width:0;">
                    <input type="text" id="report-price-type-${markerId}" placeholder="골드/두카트 등" style="flex:1;padding:4px;min-width:0;">
                </div>
            </div>
            <div style="margin-bottom:10px;">
                <label>추가 설명:</label><br>
                <input type="text" id="report-acq-cond-${markerId}" placeholder="예: 1랭크 이상" style="width:95%;padding:4px;">
            </div>
            <div style="margin-bottom:15px;">
                <label>이미지 (선택):</label><br>
                <input type="file" id="report-item-image-${markerId}" accept="image/*" style="width:95%;padding:4px;">
            </div>
            <button type="button" id="send-report-btn-${markerId}" style="width:100%;padding:8px;background:#4CAF50;color:white;border:none;border-radius:4px;">제보하기</button>
        </div>
    `;

    L.popup().setLatLng(window.map.getCenter()).setContent(formHtml).openOn(window.map);

    // IME 조합 가드 (아이템 제보 입력)
    const reportNameInput = document.getElementById(`report-item-name-${markerId}`);
    bindImeCompositionGuard(reportNameInput, { onCommit: (e) => debouncedAutocomplete(e) });

    const sendBtn = document.getElementById(`send-report-btn-${markerId}`);
    if (sendBtn) {
        sendBtn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();
            sendItemReport(markerId, markerName);
        };
    }
}

async function sendItemReport(markerId) {
    const itemName = document.getElementById(`report-item-name-${markerId}`).value;
    if (!itemName) {
        alert('아이템 이름을 입력해주세요.');
        return;
    }

    const acquireMethod = document.getElementById(`report-acquire-method-${markerId}`).value;
    const acquisition_condition = document.getElementById(`report-acq-cond-${markerId}`).value;
    const price_value = document.getElementById(`report-price-value-${markerId}`).value;
    const price_type = document.getElementById(`report-price-type-${markerId}`).value;
    const imageInput = document.getElementById(`report-item-image-${markerId}`);
    const imageFile = imageInput.files[0];

    const formData = new FormData();
    formData.append('itemName', itemName);
    formData.append('acquireMethod', acquireMethod);
    formData.append('acquisition_condition', acquisition_condition);
    formData.append('price_value', price_value);
    formData.append('price_type', price_type);
    formData.append('markerId', markerId);
    if (imageFile) {
        formData.append('image', imageFile);
    }

    try {
        const result = await postReport(formData);
        alert(result.message);
        window.map.closePopup();
    } catch (e) {
        console.error('Item report failed:', e);
        alert(`제보 제출 중 오류가 발생했습니다: ${e.message}`);
    }
}

function bindNewMarkerPopupEvents(lat, lng) {
    const sendBtn = document.getElementById('send-new-marker-btn');
    if (sendBtn) {
        sendBtn.onclick = (event) => {
            event.stopPropagation();
            event.preventDefault();
            sendNewMarkerReport(lat, lng);
        };
    }

    const imageInput = document.getElementById('marker-image');
    const imagePreview = document.getElementById('marker-image-preview');
    if (imageInput && imagePreview) {
        imageInput.onchange = (event) => {
            event.stopPropagation();
            if (event.target.files && event.target.files[0]) {
                const reader = new FileReader();
                reader.onload = (loadEvent) => {
                    imagePreview.src = loadEvent.target.result;
                    imagePreview.style.display = 'block';
                };
                reader.readAsDataURL(event.target.files[0]);
            }
        };
    }
}

function initUiEvents() {
    if (!window.map) {
        console.error('지도가 아직 준비되지 않았습니다. 0.1초 후 재시도합니다.');
        setTimeout(initUiEvents, 100);
        return;
    }

    window.map.on('click', (e) => {
        const { lat, lng } = e.latlng;

        if (window.isEditMode || window.reportMode !== 'new-marker') return;

        const formHtml = `
            <div style="padding:5px;min-width:250px;" class="custom-popup-form">
                <h4>신규 마커 제보</h4>
                <p style="font-size:12px;color:#666;">좌표: [${lat.toFixed(4)}, ${lng.toFixed(4)}]</p>
                <div style="margin-bottom:10px;">
                    <label>이름*:</label><br>
                    <input type="text" id="marker-name" style="width:95%;padding:6px;margin-top:4px;">
                </div>
                <div style="margin-bottom:10px;">
                    <label>카테고리*:</label><br>
                    <select id="marker-category" style="width:98%; padding:6px; margin-top:4px;">
                        <option value="NPC">NPC</option>
                        <option value="몬스터">몬스터</option>
                        <option value="이벤트">이벤트</option>
                        <option value="오브젝트">오브젝트</option>
                        <option value="기타">기타</option>
                    </select>
                </div>
                <div style="margin-bottom:10px;">
                    <label>설명:</label><br>
                    <textarea id="marker-desc" rows="3" style="width:95%;padding:6px;margin-top:4px;"></textarea>
                </div>
                <div style="margin-bottom:15px;">
                    <label>이미지:</label><br>
                    <input type="file" id="marker-image" accept="image/*" style="width:95%;padding:6px;margin-top:4px;">
                    <img id="marker-image-preview" src="#" alt="Image preview" style="max-width: 100%; max-height: 150px; margin-top: 10px; display: none;">
                </div>
                <button type="button" id="send-new-marker-btn" style="width:100%;padding:10px;background:#4CAF50;color:white;border:none;border-radius:4px;cursor:pointer;">제보하기</button>
            </div>
        `;

        L.popup().setLatLng(e.latlng).setContent(formHtml).openOn(window.map);
        setTimeout(() => bindNewMarkerPopupEvents(lat, lng), 0);
    });
}

async function sendNewMarkerReport(lat, lng) {
    const name = document.getElementById('marker-name').value;
    const category = document.getElementById('marker-category').value;
    if (!name || !category) {
        alert('이름과 카테고리는 필수입니다.');
        return;
    }

    const description = document.getElementById('marker-desc').value;
    const imageInput = document.getElementById('marker-image');
    const imageFile = imageInput.files[0];

    const formData = new FormData();
    formData.append('name', name);
    formData.append('category', category);
    formData.append('description', description);
    formData.append('lat', lat);
    formData.append('lng', lng);

    // 신규 마커 제보 시 area_id는 "현재 맵의 areaForMarkers"로 자동 할당
    const areaForMarkers = window.MAP_CONFIG?.[window.currentMapId]?.areaForMarkers || '';
    formData.append('area_id', areaForMarkers);

    if (imageFile) {
        formData.append('image', imageFile);
    }

    try {
        const result = await postNewMarker(formData);
        alert(result.message);

        if (result.status === 'success') {
            window.map.closePopup();
            setReportMode(null);
            const area = window.MAP_CONFIG?.[window.currentMapId]?.areaForMarkers;
            if (area) {
                await loadNPCMarkers(area);
            }
        }
    } catch (e) {
        console.error('New marker report failed:', e);
        alert(`마커 등록 중 오류가 발생했습니다: ${e.message}`);
    }
}

// --- Search UI ---
function ensureSearchUi() {
    if (document.getElementById('search-ui-container')) return;

    const container = document.createElement('div');
    container.id = 'search-ui-container';
    container.innerHTML = `
        <div id="search-panel">
            <input id="map-search-input" type="text" placeholder="NPC / 아이템 검색">
            <div id="search-results"></div>
        </div>
    `;
    document.body.appendChild(container);

    container.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    const input = document.getElementById('map-search-input');
    input.addEventListener('input', (e) => {
        const keyword = e.target.value.trim();
        debouncedSearch(keyword);
    });
}

function renderSearchResults(results) {
    const container = document.getElementById('search-results');
    if (!container) return;

    if (!results.length) {
        container.innerHTML = '<div class="search-result-item"><div class="search-result-meta">검색 결과가 없습니다.</div></div>';
        return;
    }

    container.innerHTML = results.map((result) => `
        <div class="search-result-item" data-marker-id="${result.marker_id}">
            <div class="search-result-title">${result.name}</div>
            <div class="search-result-meta">${result.result_type} · ${result.area_id || '위치 미상'}${result.item_name ? ` · ${result.item_name}` : ''}</div>
        </div>
    `).join('');

    container.querySelectorAll('.search-result-item').forEach((node, index) => {
        node.addEventListener('click', async (e) => {
            e.stopPropagation();
            e.preventDefault();
            const result = results[index];
            await focusSearchResult(result);
        });
    });
}

async function performSearch(keyword) {
    const container = document.getElementById('search-results');
    if (!container) return;

    if (!keyword) {
        container.innerHTML = '';
        return;
    }

    try {
        const results = await searchMapEntities(keyword);
        renderSearchResults(results);
    } catch (error) {
        console.error('검색 실패:', error);
        container.innerHTML = '<div class="search-result-item"><div class="search-result-meta">검색 중 오류가 발생했습니다.</div></div>';
    }
}

function setupFilterControls() {
    const toggleBtn = document.getElementById('filter-toggle-btn');
    const panel = document.getElementById('filter-panel');
    const filterButtons = document.querySelectorAll('#filter-grid .filter-btn');

    if (!toggleBtn || !panel || !filterButtons.length) return;

    toggleBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        panel.classList.toggle('active');
    });

    window.map.on('click', () => {
        if (panel.classList.contains('active')) {
            panel.classList.remove('active');
        }
    });

    filterButtons.forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();

            filterButtons.forEach((button) => button.classList.remove('active'));
            btn.classList.add('active');

            const category = btn.dataset.category;

            // applyMarkerFilter는 map_logic.js에 정의됨. 로드/스코프 문제로 undefined가 되면 무반응처럼 보임.
            const fn = window.applyMarkerFilter || (typeof applyMarkerFilter === 'function' ? applyMarkerFilter : null);
            if (!fn) {
                console.error('applyMarkerFilter가 없습니다. map_logic.js 로드/에러를 확인하세요.');
                return;
            }

            fn(category);
            panel.classList.remove('active');
        });
    });

    panel.addEventListener('click', (e) => {
        e.stopPropagation();
    });
}

function openNewZoneReportPopup({ currentMapId, bounds }) {
    const formHtml = `
        <div style="padding:5px;min-width:260px;" class="custom-popup-form">
            <h4>맵 이동 영역 추가</h4>
            <p style="font-size:12px;color:#666;margin:0 0 10px;">
                부모 맵 ID(현재 맵): <b>${currentMapId}</b><br>
                bounds: ${JSON.stringify(bounds)}
            </p>

            <div style="margin-bottom:10px;">
                <label>이동할 맵 ID*:</label><br>
                <input type="text" id="zone-target-map-id" placeholder="예: dunbarton" style="width:95%;padding:6px;margin-top:4px;">
            </div>

            <div style="margin-bottom:12px;">
                <label>새로운 맵 이미지(선택):</label><br>
                <input type="file" id="zone-new-map-image" accept="image/*" style="width:95%;padding:6px;margin-top:4px;">
                <p style="font-size:12px;color:#666;margin:6px 0 0;">
                    이미지를 첨부하면 새 맵을 먼저 생성(/maps) 후 연결합니다.
                </p>
            </div>

            <button type="button" id="zone-save-btn" style="width:100%;padding:10px;background:#4CAF50;color:white;border:none;border-radius:4px;cursor:pointer;">저장</button>
            <button type="button" id="zone-cancel-btn" style="width:100%;padding:10px;margin-top:8px;background:#666;color:white;border:none;border-radius:4px;cursor:pointer;">취소</button>
        </div>
    `;

    // new-zone 팝업은 드래그 종료 직후 이벤트(클릭/줌/드래그)와 겹치면서
    // 열렸다가 즉시 닫히는(closeOnClick/autoClose) 케이스가 발생할 수 있어
    // 자동 닫힘을 비활성화한다.
    // 일부 케이스에서 openOn(map)이 호출은 되었는데 화면에 안 보이는 문제가 있어
    // map.openPopup(popup)으로 강제 오픈 + popupopen 로그로 확인한다.
    // 팝업 위치를 "현재 화면 중심"이 아니라, 드래그한 영역의 중심으로 잡아야
    // (특히 uladh 같이 bounds/view가 큰 맵에서) 화면 밖에 떠서 안 보이는 문제를 막을 수 있음.
    const b = L.latLngBounds(bounds);
    const popupLatLng = b.getCenter();

    const popup = L.popup({
        autoClose: false,
        closeOnClick: false,
        closeButton: true,
        // 화면 바깥으로 튀는 경우를 줄이기 위해 autoPan 허용
        autoPan: true,
        keepInView: true,
    })
        .setLatLng(popupLatLng)
        .setContent(formHtml);

    try {
        // 문제 재현상: 어떤 로직이 popup을 “잠깐 보였다가” 닫는 경우가 있음.
        // popupopen/popupclose 이벤트로 원인을 확정하고, new-zone 팝업은 최소 1초간 강제 유지한다.
        if (window.map && !window.map.__newZonePopupDebugBound) {
            window.map.__newZonePopupDebugBound = true;
            window.map.on('popupopen', (e) => {
                console.log('[new-zone-ui] leaflet popupopen', {
                    hasPopup: Boolean(e?.popup),
                    src: e?.popup?._source ? 'has_source' : 'no_source',
                });
            });
            window.map.on('popupclose', (e) => {
                console.log('[new-zone-ui] leaflet popupclose', {
                    hasPopup: Boolean(e?.popup),
                    src: e?.popup?._source ? 'has_source' : 'no_source',
                });

                try {
                    const lockUntil = window.__newZonePopupLockUntil || 0;
                    console.log('[new-zone-ui] popupclose extra', {
                        now: Date.now(),
                        lockUntil,
                        locked: Date.now() < lockUntil,
                        reportMode: window.reportMode,
                        activePopupSame: window.__newZoneActivePopup === e?.popup,
                        lastModeSet: window.__lastReportModeSetAt || null,
                    });
                } catch {}
                try {
                    console.trace('[new-zone-ui] popupclose stack');
                } catch {}
            });
        }
    } catch {}
    try {
        window.map.openPopup(popup);
        console.log('[new-zone-ui] popup opened', { currentMapId, bounds });
        window.__newZonePopupLockUntil = Date.now() + 1200; // 1.2초 동안은 closePopup 무시
        window.__newZoneActivePopup = popup;

        // 팝업이 “열렸는데 안 보이는” 원인 추적: DOM 존재/좌표/스타일 확인 + 강제 최상단 z-index 부여
        setTimeout(() => {
            try {
                const el = popup.getElement?.();
                if (!el) {
                    console.warn('[new-zone-ui] popup element is null (not in DOM?)');
                    return;
                }

                const rect = el.getBoundingClientRect();
                const cs = window.getComputedStyle(el);

                console.log('[new-zone-ui] popup element info', {
                    rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
                    display: cs.display,
                    visibility: cs.visibility,
                    opacity: cs.opacity,
                    zIndex: cs.zIndex,
                    position: cs.position,
                    transform: cs.transform,
                });

                // 원인 분리용: 가려짐(z-index)/opacity 문제면 이걸로 바로 보이게 됨
                el.style.zIndex = '100000';
                el.style.opacity = '1';
                el.style.visibility = 'visible';
                el.style.display = 'block';

                console.log('[new-zone-ui] popup element forced style applied', {
                    zIndex: el.style.zIndex,
                    opacity: el.style.opacity,
                    visibility: el.style.visibility,
                    display: el.style.display,
                });
            } catch (e) {
                console.error('[new-zone-ui] popup element debug failed', e);
            }
        }, 0);
    } catch (e) {
        console.error('[new-zone-ui] popup open failed', e);
        // fallback
        popup.openOn(window.map);
    }

    const saveBtn = document.getElementById('zone-save-btn');
    const cancelBtn = document.getElementById('zone-cancel-btn');

    if (cancelBtn) {
        cancelBtn.onclick = (e) => {
            e.stopPropagation();
            e.preventDefault();

            // 팝업 취소 = "모드 취소"와 동일하게 동작
            try {
                setReportMode(null);
            } catch {}

            try {
                window.map.closePopup();
            } catch {}

            if (typeof window.clearZoneDrawingState === 'function') {
                window.clearZoneDrawingState();
            }
        };
    }

    if (saveBtn) {
        saveBtn.onclick = async (e) => {
            e.stopPropagation();
            e.preventDefault();

            const targetId = (document.getElementById('zone-target-map-id').value || '').trim();
            if (!targetId) {
                alert('이동할 맵 ID를 입력해주세요.');
                return;
            }

            const imageInput = document.getElementById('zone-new-map-image');
            const imageFile = imageInput?.files?.[0];

            // 새 맵으로 연결하려는 케이스(= targetId가 아직 maps에 없을 가능성이 높음)는
            // 이미지 업로드를 필수로 강제해서 /maps 생성 플로우를 타게 한다.
            // (서버는 zones append 시 target map 존재를 검사함)
            if (!imageFile) {
                alert('새로운 이동할 맵을 추가하려면 "새로운 맵 이미지" 업로드가 필요합니다.\n(기존에 존재하는 맵으로 연결하려면 이미지 없이도 가능합니다)');
                return;
            }

            try {
                let finalTargetId = targetId;

                // 이미지가 있으면 새 맵 생성 먼저
                if (imageFile) {
                    // 새 맵 bounds는 일단 기본값(현재 맵 bounds)을 사용하도록 함 (추후 개선 가능)
                    const baseCfg = window.MAP_CONFIG?.[currentMapId];
                    const newMapBounds = baseCfg?.bounds || [[0, 0], [800, 800]];

                    const fd = new FormData();
                    fd.append('id', targetId);
                    fd.append('bounds', JSON.stringify(newMapBounds));
                    fd.append('parent_id', currentMapId);
                    fd.append('view_config', JSON.stringify(baseCfg?.view || null));

                    // 새 맵에서 생성되는 마커가 부모와 섞이지 않도록:
                    // 웹에서 새로 만드는 맵은 기본 area_for_markers를 "자기 map id"로 둔다.
                    // (즉, 임시구역2에서 만든 마커는 area_id=임시구역2 로만 보임)
                    const inheritedArea = targetId;
                    fd.append('area_for_markers', inheritedArea);

                    fd.append('image', imageFile);

                    const created = await createMap(fd);
                    finalTargetId = created?.map?.id || targetId;

                    // 즉시 MAP_CONFIG 갱신(리로드 없이 사용)
                    if (created?.map?.id && created?.map?.img_path) {
                        window.MAP_CONFIG[created.map.id] = {
                            img: created.map.img_path,
                            bounds: newMapBounds,
                            view: baseCfg?.view || null,
                            parent: currentMapId,
                            zones: null,
                            areaForMarkers: inheritedArea || null,
                        };
                    }
                }

                // 현재 맵 zones에 append
                await appendMapZone(currentMapId, bounds, finalTargetId);

                // config를 다시 받아와서 zones 즉시 반영(정확도 우선)
                window.MAP_CONFIG = await fetchMapConfig();

                // 현재 맵을 다시 로드해서 방금 추가한 존이 클릭 가능해지게
                await loadMap(currentMapId, { syncUrl: false, historyMode: 'replace' });

                showToast('이동 영역 저장 성공');

                // 저장 완료 = "모드 취소"와 동일하게 동작 (연속 추가를 원하면 사용자가 다시 켜면 됨)
                try {
                    setReportMode(null);
                } catch {}

                // 중요: loadMap() 내부에서 zonesLayer를 clear 후 다시 그리며,
                // 그 과정에서 Leaflet이 popup을 정리하면서 popupclose가 발생한다.
                // 따라서 여기서는 closePopup을 호출하지 않는다(팝업은 화면 전환/리로드 과정에서 자연스럽게 닫힘).
                // window.map.closePopup();

                if (typeof window.clearZoneDrawingState === 'function') {
                    window.clearZoneDrawingState();
                }
            } catch (err) {
                console.error('zone 저장 실패:', err);
                alert(`저장 실패: ${err.message}`);
            }
        };
    }
}
window.openNewZoneReportPopup = openNewZoneReportPopup;

function setupUi() {
    setupReportMenu();
    ensureSearchUi();
    initUiEvents();

    // 필터 UI는 map 초기화 이후(window.map 존재)에도 안전하게 바인딩되어야 함
    if (typeof setupFilterControls === 'function') {
        setupFilterControls();
    } else {
        console.warn('setupFilterControls가 정의되지 않았습니다. (map_logic.js 로드/에러 확인 필요)');
    }
}

// DOMContentLoaded가 이미 지난 경우에도 안전하게 실행
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupUi);
} else {
    setupUi();
}
