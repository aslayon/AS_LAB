// api.js 첫 줄
// 기본값: 현재 접속한 origin(도메인/IP + 포트)을 API 주소로 사용
// (필요하면 index.html 등에서 window.API_BASE_URL을 먼저 지정해 override 가능)
if (typeof window.API_BASE_URL === 'undefined') {
    window.API_BASE_URL = window.location.origin;
}

// 템플릿 문자열에서 쓰기 쉽게 별칭 제공
const API_BASE_URL = window.API_BASE_URL;



async function fetchMapConfig() {
    const response = await fetch(`${API_BASE_URL}/maps/config`);
    if (!response.ok) throw new Error('Failed to fetch map config');
    return await response.json();
}

async function fetchMarkers(areaName) {
    const response = await fetch(`${API_BASE_URL}/markers?area=${areaName}`);
    if (!response.ok) throw new Error(`Failed to load markers for ${areaName}`);
    return await response.json();
}

async function fetchMarkerItems(markerId, signal) {
    const response = await fetch(`${API_BASE_URL}/markers/${markerId}/items`, { signal });
    if (!response.ok) throw new Error(`Failed to fetch items for marker ${markerId}`);
    return await response.json();
}

async function postDislike(source_id) {
    const response = await fetch(`${API_BASE_URL}/item-sources/${source_id}/dislike`, {
        method: 'POST'
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to dislike item source');
    }
    return await response.json();
}

async function fetchItemAutocomplete(name) {
    const response = await fetch(`${API_BASE_URL}/items/search?name=${encodeURIComponent(name)}`);
    if (!response.ok) throw new Error('Autocomplete fetch failed');
    return await response.json();
}

async function postItemMaster(formData) {
    const response = await fetch(`${API_BASE_URL}/items/master`, {
        method: 'POST',
        body: formData
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to send item master');
    }
    return await response.json();
}

async function postReport(formData) {
    const response = await fetch(`${API_BASE_URL}/report`, {
        method: 'POST',
        body: formData
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to send report');
    }
    return await response.json();
}

async function postNewMarker(formData) {
    const response = await fetch(`${API_BASE_URL}/report-marker`, {
        method: 'POST',
        body: formData
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to send new marker report');
    }
    return await response.json();
}

async function updateMarkerLocation(markerId, lat, lng) {
    const response = await fetch(`${API_BASE_URL}/markers/${markerId}/location`, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ lat, lng }),
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to update marker location');
    }
    return await response.json();
}

async function searchMapEntities(keyword) {
    const response = await fetch(`${API_BASE_URL}/search?keyword=${encodeURIComponent(keyword)}`);
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to search entities');
    }
    return await response.json();
}

async function createMap(formData) {
    const response = await fetch(`${API_BASE_URL}/maps`, {
        method: 'POST',
        body: formData
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to create map');
    }
    return await response.json();
}

async function updateMapImage(mapId, file) {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${API_BASE_URL}/maps/${encodeURIComponent(mapId)}/image`, {
        method: 'PATCH',
        body: formData,
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to update map image');
    }
    return await response.json();
}

async function appendMapZone(mapId, bounds, target) {
    const formData = new FormData();
    formData.append('bounds', JSON.stringify(bounds));
    formData.append('target', target);

    const response = await fetch(`${API_BASE_URL}/maps/${encodeURIComponent(mapId)}/zones`, {
        method: 'PATCH',
        body: formData,
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to append map zone');
    }
    return await response.json();
}

async function updateItemImage(itemId, file) {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${API_BASE_URL}/items/${encodeURIComponent(itemId)}/image`, {
        method: 'POST',
        body: formData,
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to update item image');
    }
    return await response.json();
}

async function updateItemName(itemId, newName) {
    const formData = new FormData();
    formData.append('new_name', newName);

    const response = await fetch(`${API_BASE_URL}/items/${encodeURIComponent(itemId)}/name`, {
        method: 'PATCH',
        body: formData,
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to update item name');
    }
    return await response.json();
}

async function updateMarkerImage(markerId, file) {
    const formData = new FormData();
    formData.append('image', file);

    const response = await fetch(`${API_BASE_URL}/markers/${encodeURIComponent(markerId)}/image`, {
        method: 'POST',
        body: formData,
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to update marker image');
    }
    return await response.json();
}

async function resolveItemByName(name) {
    const response = await fetch(`${API_BASE_URL}/items/resolve?name=${encodeURIComponent(name)}`);
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to resolve item by name');
    }
    return await response.json();
}

async function reportMarker(markerId) {
    const response = await fetch(`${API_BASE_URL}/markers/${encodeURIComponent(markerId)}/report`, {
        method: 'POST',
    });
    if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Failed to report marker');
    }
    return await response.json();
}
