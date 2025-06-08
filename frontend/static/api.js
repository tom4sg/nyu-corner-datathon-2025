const BACKEND_URL = process.env.VITE_API_URL || "http://127.0.0.1:8000";

export async function searchPlaces(query) {
    const response = await fetch(`${BACKEND_URL}/search?q=${encodeURIComponent(query)}`);
    const data = await response.json();
    return data.results;
}

export async function getPlaceDetails(placeId) {
    const response = await fetch(`${BACKEND_URL}/place/${placeId}`);
    const data = await response.json();
    return data;
}

export async function getPlaceReviews(placeId) {
    const response = await fetch(`${BACKEND_URL}/place/${placeId}/reviews`);
    const data = await response.json();
    return data;
}

export async function getPlacePhotos(placeId) {
    const response = await fetch(`${BACKEND_URL}/place/${placeId}/photos`);
    const data = await response.json();
    return data;
}
