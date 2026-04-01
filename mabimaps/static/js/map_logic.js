// --- Global Map Variables ---
window.map = L.map('map', { crs: L.CRS.Simple, minZoom: -1, maxZoom: 3 });
window.markerLayers = {
    npc: L.layerGroup(),
    monster: L.layerGroup(),
    event: L.layerGroup(),
    object: L.layerGroup(),
    other: L.layerGroup(),
};
window.currentLayer = null;
window.currentMapId = null;
window.MAP_CONFIG = null;
window.markerIndex = new Map();
window.activeCategoryFilter = 'all';
window.activeHighlightedMarker = null;

window.reportMode = null;
window.currentDrawingRect = null;
window.isDrawingZone = false;
window.zoneDragStartLatLng = null;

const zonesLayer = L.layerGroup().addTo(window.map);
// 다른 스크립트에서 필요 시 참조/디버깅할 수 있도록 노출
window.zonesLayer = zonesLayer;

// zones(이동영역)은 마커보다 아래로 깔아서(낮은 z-index) 마커 클릭을 방해하지 않게 함
let zonesPane = window.map.getPane('zonesPane');
if (!zonesPane) {
    zonesPane = window.map.createPane('zonesPane');
}

// NOTE: zones가 "0.1초 보였다가 사라짐" 증상은 overlayPane(imageOverlay)가 위에서 덮는 stacking 이슈였음.
// overlayPane(기본 400)보다 살짝 위, markerPane(기본 600)보단 아래로 고정.
try {
    const overlayPane = window.map.getPane('overlayPane');
    const overlayZ = overlayPane ? Number(getComputedStyle(overlayPane).zIndex || 400) : 400;
    zonesPane.style.zIndex = String(Math.min(overlayZ + 10, 550));
} catch {
    zonesPane.style.zIndex = '410';
}

const CATEGORY_LAYER_MAP = {
    NPC: 'npc',
    몬스터: 'monster',
    이벤트: 'event',
    오브젝트: 'object',
};

function createEmojiMarkerIcon(emoji, extraClass = '') {
    return L.divIcon({
        className: `emoji-marker ${extraClass}`.trim(),
        html: `<div class="emoji-marker__inner">${emoji}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
        popupAnchor: [0, -14],
    });
}

const markerIcons = {
    npc: createEmojiMarkerIcon('👤', 'emoji-marker--npc'),
    monster: createEmojiMarkerIcon('⚔️', 'emoji-marker--monster'),
    event: createEmojiMarkerIcon('✨', 'emoji-marker--event'),
    object: createEmojiMarkerIcon('📦', 'emoji-marker--object'),
    other: createEmojiMarkerIcon('🌟', 'emoji-marker--other'),
};

// --- App Initialization & Map Logic ---
function getMapIdFromUrl() {
    try {
        const params = new URLSearchParams(window.location.search);
        return params.get('map');
    } catch {
        return null;
    }
}

function setUrlMapParam(mapId, mode = 'push') {
    const url = new URL(window.location.href);
    if (mapId) {
        url.searchParams.set('map', mapId);
    } else {
        url.searchParams.delete('map');
    }

    const state = { map: mapId || null };
    if (mode === 'replace') {
        window.history.replaceState(state, '', url);
    } else {
        window.history.pushState(state, '', url);
    }
}

async function initApp() {
    try {
        window.MAP_CONFIG = await fetchMapConfig();
        ensureMarkerIconStyles();
        // ui_handlers.js에서도 setupFilterControls를 호출하므로 여기서는 중복 호출하지 않음


        const initialMapIdFromUrl = getMapIdFromUrl();
        const initialMapId = initialMapIdFromUrl && window.MAP_CONFIG?.[initialMapIdFromUrl] ? initialMapIdFromUrl : 'world';

        // 첫 로드는 replaceState로 현재 URL과 history state를 동기화
        setUrlMapParam(initialMapId, 'replace');

        // 뒤로가기/앞으로가기 처리: URL의 map 파라미터를 읽어서 해당 맵으로 로드
        window.addEventListener('popstate', (event) => {
            const mapId = event?.state?.map || getMapIdFromUrl() || 'world';
            // popstate는 이미 URL이 바뀐 상태이므로 pushState를 하지 않도록 옵션 전달
            loadMap(mapId, { syncUrl: false });
        });

        loadMap(initialMapId, { syncUrl: false });
    } catch (e) {
        console.error('맵 설정 데이터 로드 실패:', e);
        document.getElementById('map').innerHTML = '<p style="color:white; text-align:center;">맵 데이터를 불러올 수 없습니다.</p>';
    }
}

function ensureMarkerIconStyles() {
    const styleId = 'marker-icon-category-styles';
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
    style.textContent = `
        .marker-icon-monster {
            filter: hue-rotate(140deg) saturate(1.8);
        }
        .marker-icon-event {
            filter: hue-rotate(280deg) saturate(2);
        }
        .marker-icon-object {
            filter: grayscale(0.2) sepia(0.8) saturate(1.3);
        }
        .marker-icon-other {
            filter: grayscale(0.8);
        }
    `;
    document.head.appendChild(style);
}

function normalizeCategory(category) {
    return CATEGORY_LAYER_MAP[category] || 'other';
}

function getMarkerIcon(category) {
    const normalized = normalizeCategory(category);
    return markerIcons[normalized] || markerIcons.other;
}

function applyMarkerDraggableState(marker) {
    if (!marker?.dragging) return;

    if (window.isEditMode) {
        marker.dragging.enable();
    } else {
        marker.dragging.disable();
    }
}

function setActiveMarkerHighlight(marker) {
    if (window.activeHighlightedMarker && window.activeHighlightedMarker !== marker) {
        const prevEl = window.activeHighlightedMarker.getElement?.();
        if (prevEl) prevEl.classList.remove('emoji-marker--active');
    }

    window.activeHighlightedMarker = marker;

    const el = marker?.getElement?.();
    if (el) el.classList.add('emoji-marker--active');
}

function bindMarkerEvents(marker, markerData) {
    marker.off();

    marker.on('click', (event) => {
        if (!window.isEditMode) {
            setActiveMarkerHighlight(marker);
            openNpcPopup(marker, markerData, event);
        }
    });

    marker.on('dragend', async (event) => {
        if (!window.isEditMode) {
            applyMarkerDraggableState(marker);
            return;
        }

        const newPos = event.target.getLatLng();
        const previousLat = markerData.lat;
        const previousLng = markerData.lng;

        try {
            await updateMarkerLocation(markerData.id, newPos.lat, newPos.lng);
            markerData.lat = newPos.lat;
            markerData.lng = newPos.lng;
            showToast(`'${markerData.name}' 위치 저장 성공`);
        } catch (error) {
            console.error('마커 위치 저장 실패:', error);
            marker.setLatLng([previousLat, previousLng]);
            showToast(`저장 실패: ${error.message}`);
        }
    });
}

function clearMarkerLayers() {
    Object.values(window.markerLayers).forEach((layer) => layer.clearLayers());
    window.markerIndex.clear();
}

function applyMarkerFilter(category = window.activeCategoryFilter || 'all') {
    window.activeCategoryFilter = category;

    Object.values(window.markerLayers).forEach((layer) => {
        if (window.map.hasLayer(layer)) {
            window.map.removeLayer(layer);
        }
    });

    if (category === 'all') {
        Object.values(window.markerLayers).forEach((layer) => layer.addTo(window.map));
        return;
    }

    const targetLayer = window.markerLayers[category];
    if (targetLayer) {
        targetLayer.addTo(window.map);
    }
}

// UI(다른 스크립트)에서 안전하게 호출할 수 있도록 전역으로 노출
window.applyMarkerFilter = applyMarkerFilter;

function setReportMode(mode) {
    // ui_handlers.js 가 reportMode/커서/UI 갱신을 담당한다.
    // map_logic.js 쪽 setReportMode는 중복 정의로 인해 호출 경로가 꼬이거나,
    // 다른 파일에서 window.setReportMode를 호출할 때 의도치 않게 이 버전이 잡힐 수 있다.
    // 따라서 여기서는 reportMode만 세팅하되, window.setReportMode로 노출하지 않는다.
    window.reportMode = mode;
}
// window.setReportMode = setReportMode;

function clearZoneDrawingState() {
    if (window.currentDrawingRect) {
        try {
            window.map.removeLayer(window.currentDrawingRect);
        } catch {}
        window.currentDrawingRect = null;
    }
    window.isDrawingZone = false;
    window.zoneDragStartLatLng = null;
    try {
        window.map.dragging.enable();
    } catch {}

    // (UX) 드래그 영역 추가 도중 "모드 취소" 또는 "취소" 시, 커서/버튼 상태도 즉시 정리
    // ui_handlers.js 의 setReportMode(null)에서 편집모드/메뉴 상태도 함께 정리한다.
    try {
        if (typeof window.setReportMode === 'function') {
            window.setReportMode(null);
        }
    } catch {}
}

function latLngBoundsToZoneBounds(bounds) {
    // CRS.Simple 기준: Leaflet은 [lat, lng]를 사용 (여기서는 y,x 로 취급)
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();
    return [
        [sw.lat, sw.lng],
        [ne.lat, ne.lng],
    ];
}

function createMapMarker(markerData) {
    const marker = L.marker([markerData.lat, markerData.lng], {
        icon: getMarkerIcon(markerData.category),
        draggable: Boolean(window.isEditMode),
    });

    marker.mabiData = markerData;
    bindMarkerEvents(marker, markerData);
    applyMarkerDraggableState(marker);

    return marker;
}

function registerMarker(markerData) {
    const layerKey = normalizeCategory(markerData.category);
    const marker = createMapMarker(markerData);

    marker.addTo(window.markerLayers[layerKey]);
    window.markerIndex.set(markerData.id, {
        marker,
        data: markerData,
        layerKey,
    });

    return marker;
}

async function loadMap(mapId, options = {}) {
    const { syncUrl = true, historyMode = 'push' } = options;
    if (!window.MAP_CONFIG?.[mapId]) return;

    if (syncUrl) {
        setUrlMapParam(mapId, historyMode);
    }

    const config = window.MAP_CONFIG[mapId];
    window.currentMapId = mapId;

    if (window.currentLayer) {
        window.map.removeLayer(window.currentLayer);
    }

    clearMarkerLayers();
    zonesLayer.clearLayers();

    const imgUrl = `${config.img}${config.img.includes('?') ? '&' : '?'}v=${Date.now()}`;
    window.currentLayer = L.imageOverlay(imgUrl, config.bounds).addTo(window.map);
    if (config.view) {
        window.map.setView(config.view.center, config.view.zoom);
    } else {
        window.map.fitBounds(config.bounds);
    }

    const backBtn = document.getElementById('backBtn');
    backBtn.style.display = config.parent ? 'flex' : 'none';
    backBtn.onclick = config.parent ? () => loadMap(config.parent) : null;

    if (config.zones) {
        config.zones.forEach((zone) => {
            // zones는 항상 화면에서 보이도록 약한 투명도를 기본 적용
            // (클릭 가능한 영역을 사용자에게 명확히 보여주기 위함)
            const ZONE_STYLE_DEFAULT = {
                pane: 'zonesPane',
                interactive: true,
                bubblingMouseEvents: false, // 클릭이 지도/다른 레이어로 전파되는 것 최소화
                color: '#ff7800',
                weight: 2,
                opacity: 0.6,
                fillColor: '#ff7800',
                fillOpacity: 0.25, // 핵심: 평소에도 영역이 보이도록
            };

            const rect = L.rectangle(zone.bounds, ZONE_STYLE_DEFAULT).addTo(zonesLayer);

            // Leaflet은 실제 표시 엘리먼트를 pane에 올리므로, DOM 쪽에서 opacity/display가
            // 다른 CSS/로직에 의해 꺼지는지 확인하기 위해 클래스 부여
            try {
                rect.on('add', () => {
                    const el = rect.getElement?.();
                    if (el) el.classList.add('zone-rect');
                });
                const elNow = rect.getElement?.();
                if (elNow) elNow.classList.add('zone-rect');
            } catch {}

            // Hover 효과: 클릭 가능한 영역임을 명확히 표시
            rect.on('mouseover', () => rect.setStyle({ fillOpacity: 0.5 }));
            rect.on('mouseout', () => rect.setStyle({ fillOpacity: 0.25 }));

            rect.on('click', (e) => {
                // 마커 클릭 등과 충돌 최소화
                if (e?.originalEvent) {
                    try {
                        e.originalEvent.stopPropagation();
                    } catch {}
                }
                loadMap(zone.target);
            });
        });
    }

    if (config.areaForMarkers) {
        await loadNPCMarkers(config.areaForMarkers);
    } else {
        applyMarkerFilter(window.activeCategoryFilter);
    }
}

async function loadNPCMarkers(areaName) {
    try {
        clearMarkerLayers();

        const data = await fetchMarkers(areaName);
        data.forEach((markerData) => {
            registerMarker(markerData);
        });

        applyMarkerFilter(window.activeCategoryFilter);
    } catch (e) {
        console.error(`Failed to load markers for ${areaName}:`, e);
    }
}

function findMapIdByArea(areaId) {
    const entries = Object.entries(window.MAP_CONFIG || {});
    const found = entries.find(([, config]) => config.areaForMarkers === areaId);
    return found ? found[0] : null;
}

async function focusSearchResult(result) {
    if (!result) return;

    const targetMapId = findMapIdByArea(result.area_id) || window.currentMapId;
    if (targetMapId && targetMapId !== window.currentMapId) {
        await loadMap(targetMapId);
    }

    const targetZoom = Math.max(window.map.getZoom(), 1);
    window.map.flyTo([result.lat, result.lng], targetZoom, { duration: 0.8 });

    const markerEntry = window.markerIndex.get(result.marker_id);
    if (markerEntry) {
        setActiveMarkerHighlight(markerEntry.marker);
        // 검색 결과 클릭 시에도 “마커 클릭”과 동일하게 팝업을 즉시 띄움
        // (이동 애니메이션이 끝나기 전에 열리면 어색할 수 있어서 약간 지연)
        setTimeout(() => openNpcPopup(markerEntry.marker, markerEntry.data), 650);
    }
}

/**
 * 신규 영역 추가(new-zone): 드래그 로직 (사용자 제공 “튕김 완전 해결” 버전으로 덮어씀)
 *
 * 핵심:
 * - container 캡처 단계에서 이벤트를 가로채 Leaflet 내부 핸들러보다 먼저 처리
 * - 중복 등록 방지: 기존 리스너를 removeEventListener 후 재등록
 * - 드래그 시작/끝 좌표: map.mouseEventToLatLng(MouseEvent)
 * - mouseup 직후 즉시 팝업 호출
 */
const __zoneDrag = {
    startZoneDrawing: null,
    handleMouseMove: null,
    handleMouseUpGlobal: null,
    debug: true,
    seq: 0,
};

function zoneDbg(eventName, extra = {}) {
    if (!__zoneDrag.debug) return;
    const payload = {
        seq: ++__zoneDrag.seq,
        t: new Date().toISOString(),
        mode: window.reportMode,
        isDrawingZone: window.isDrawingZone,
        currentMapId: window.currentMapId,
        hasRect: Boolean(window.currentDrawingRect),
        ...extra,
    };
    try {
        console.log('[new-zone]', eventName, payload);
    } catch {}
}

function bindNewZoneDomDragHandlers() {
    if (!window.map) return;
    const container = window.map.getContainer?.();
    if (!container) return;

    // 1) 기존 리스너 제거(중복 방지)
    if (__zoneDrag.startZoneDrawing) container.removeEventListener('mousedown', __zoneDrag.startZoneDrawing, true);
    if (__zoneDrag.handleMouseMove) container.removeEventListener('mousemove', __zoneDrag.handleMouseMove, true);
    if (__zoneDrag.handleMouseUpGlobal) window.removeEventListener('mouseup', __zoneDrag.handleMouseUpGlobal, true);

    // 2) 새로운 캡처링 리스너 등록
    __zoneDrag.startZoneDrawing = (ev) => {
        if (window.reportMode !== 'new-zone') return;
        if (!window.currentMapId) return;
        if (typeof ev.button === 'number' && ev.button === 2) return;

        // 팝업 위(취소/저장/닫기 등) 클릭을 드래그 시작으로 오인하지 않도록 차단
        try {
            const target = ev.target;
            if (target && typeof target.closest === 'function') {
                if (target.closest('.leaflet-popup') || target.closest('.leaflet-control') || target.closest('#search-ui-container')) {
                    return;
                }
            }
        } catch {}

        // 팝업이 열려있으면(특히 closeOnClick:false로 유지 중) 팝업 닫기/입력에 집중해야 하므로
        // 그 동안은 new-zone 드래그 시작을 막는다.
        // 단, 팝업이 '열려있다'고 해서 항상 화면상 입력 중인 상태는 아니다.
        // loadMap() 등으로 overlay가 갈아엎어지면 내부적으로 window.map._popup 레퍼런스가 남아
        // 다음 드래그가 영구적으로 막히는 케이스가 생길 수 있다.
        // 따라서 실제로 열린 팝업인지(isOpen)까지 확인한다.
        if (window.map && window.map._popup) {
            const p = window.map._popup;
            const isOpen = typeof p.isOpen === 'function' ? p.isOpen() : Boolean(p._isOpen);
            if (isOpen) return;
        }

        zoneDbg('mousedown', {
            button: ev.button,
            clientX: ev.clientX,
            clientY: ev.clientY,
            buttons: ev.buttons,
        });

        // Leaflet의 드래그와 충돌 방지 핵심
        try {
            ev.stopPropagation();
            ev.stopImmediatePropagation?.();
            ev.preventDefault?.();
        } catch {}

        window.isDrawingZone = true;
        window.zoneDragStartLatLng = window.map.mouseEventToLatLng(ev);
        zoneDbg('start', { start: window.zoneDragStartLatLng });

        if (window.currentDrawingRect) {
            try {
                window.map.removeLayer(window.currentDrawingRect);
            } catch {}
            window.currentDrawingRect = null;
        }

        // 임시 사각형 생성 (zonesPane에 표시)
        window.currentDrawingRect = L.rectangle([window.zoneDragStartLatLng, window.zoneDragStartLatLng], {
            color: '#ff7800',
            weight: 2,
            fillOpacity: 0.2,
            dashArray: '5, 5',
            pane: 'zonesPane',
            interactive: false,
        }).addTo(window.map);

        try {
            window.map.dragging.disable();
        } catch {}
    };

    __zoneDrag.handleMouseMove = (ev) => {
        if (window.reportMode !== 'new-zone') return;
        if (!window.isDrawingZone || !window.zoneDragStartLatLng || !window.currentDrawingRect) return;

        try {
            ev.stopPropagation();
            ev.stopImmediatePropagation?.();
            ev.preventDefault?.();
        } catch {}

        const ll = window.map.mouseEventToLatLng(ev);
        const b = L.latLngBounds(window.zoneDragStartLatLng, ll);
        window.currentDrawingRect.setBounds(b);

        // move는 너무 많이 찍히니 10회 중 1회만 출력
        if (__zoneDrag.seq % 10 === 0) {
            zoneDbg('mousemove', { end: ll });
        }
    };

    __zoneDrag.handleMouseUpGlobal = (ev) => {
        if (window.reportMode !== 'new-zone') return;
        if (!window.isDrawingZone) return;

        zoneDbg('mouseup', {
            button: ev.button,
            clientX: ev.clientX,
            clientY: ev.clientY,
            buttons: ev.buttons,
        });

        try {
            ev.stopPropagation();
            ev.stopImmediatePropagation?.();
            ev.preventDefault?.();
        } catch {}

        // 드래그 종료 및 팝업 호출(즉시)
        const ok = finishZoneDrawing(ev);
        zoneDbg('finishZoneDrawing', { ok });

        // 드래그 상태 정리
        window.isDrawingZone = false;
        try {
            window.map.dragging.enable();
        } catch {}

        // 중요:
        // 여기서 reportMode를 null로 끄면, 다음에 버튼으로 다시 켰을 때
        // UI(ui_handlers.js)의 setReportMode가 map_logic.js 쪽 동기화를 못하고
        // window.setReportMode(map_logic.js 버전)가 재귀 호출로 빠지면서 모드가 꼬일 수 있다.
        // new-zone 무한 팝업 문제는 "팝업 영역 클릭을 드래그 시작으로 오인"하는 것이 핵심이므로
        // mousedown에서 .leaflet-popup 등을 차단하는 현재 로직으로 해결하고,
        // 모드는 자동 종료하지 않는다.
    };

    container.addEventListener('mousedown', __zoneDrag.startZoneDrawing, true);
    container.addEventListener('mousemove', __zoneDrag.handleMouseMove, true);
    window.addEventListener('mouseup', __zoneDrag.handleMouseUpGlobal, true);
}

// --- New Zone Drawing Mode (new-zone) ---
bindNewZoneDomDragHandlers();

function finishZoneDrawing(ev) {
    if (window.reportMode !== 'new-zone') return false;
    if (!window.isDrawingZone || !window.currentDrawingRect) return false;

    // mouseup 시점의 마우스 위치를 기준으로 bounds를 한 번 더 확정(요구사항: 좌표 타이밍 혼동 방지)
    if (ev) {
        try {
            const endLatLng = window.map.mouseEventToLatLng(ev);
            const finalBounds = L.latLngBounds(window.zoneDragStartLatLng, endLatLng);
            window.currentDrawingRect.setBounds(finalBounds);
            zoneDbg('finalizeBounds', { start: window.zoneDragStartLatLng, end: endLatLng });
        } catch (e) {
            zoneDbg('finalizeBounds_error', { err: String(e) });
        }
    }

    const bounds = window.currentDrawingRect.getBounds();
    zoneDbg('bounds_raw', { sw: bounds.getSouthWest(), ne: bounds.getNorthEast() });

    // 너무 작은/선 형태 bounds는 클릭 영역이 거의 없어져서 “추가했는데 클릭 안됨”이 발생함.
    // 최소 크기를 강제로 보정해서 항상 면적이 있는 사각형으로 저장되게 한다.
    const MIN_ZONE_SIZE = 8; // CRS.Simple 좌표 기준 최소 8px 정도
    const sw = bounds.getSouthWest();
    const ne = bounds.getNorthEast();

    let minLat = Math.min(sw.lat, ne.lat);
    let maxLat = Math.max(sw.lat, ne.lat);
    let minLng = Math.min(sw.lng, ne.lng);
    let maxLng = Math.max(sw.lng, ne.lng);

    if (Math.abs(maxLat - minLat) < MIN_ZONE_SIZE) {
        const mid = (maxLat + minLat) / 2;
        minLat = mid - MIN_ZONE_SIZE / 2;
        maxLat = mid + MIN_ZONE_SIZE / 2;
    }
    if (Math.abs(maxLng - minLng) < MIN_ZONE_SIZE) {
        const mid = (maxLng + minLng) / 2;
        minLng = mid - MIN_ZONE_SIZE / 2;
        maxLng = mid + MIN_ZONE_SIZE / 2;
    }

    const zoneBounds = [
        [minLat, minLng],
        [maxLat, maxLng],
    ];

    // 팝업이 안 뜨는 원인 추적용: 함수 존재 + 호출 직전/직후 로그
    zoneDbg('beforePopupCall', {
        hasOpenNewZoneReportPopup: typeof window.openNewZoneReportPopup === 'function',
        zoneBounds,
    });

    if (typeof window.openNewZoneReportPopup === 'function') {
        try {
            window.openNewZoneReportPopup({
                currentMapId: window.currentMapId,
                bounds: zoneBounds,
            });
            zoneDbg('afterPopupCall', { ok: true });
        } catch (e) {
            zoneDbg('afterPopupCall', { ok: false, err: String(e) });
        }
    } else {
        console.warn('openNewZoneReportPopup is not defined');
    }

    return true;
}

/**
 * (정리)
 * 기존 Leaflet 기반 mouseup/dragend + container mouseup/touchend 폴백은
 * DOM 기반 드래그 처리(bindNewZoneDomDragHandlers)로 대체되었으므로 제거.
 * 중복 핸들러는 팝업이 두 번 뜨거나 상태(isDrawingZone)가 꼬이는 원인이 될 수 있다.
 */
