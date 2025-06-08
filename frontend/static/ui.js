// frontend/src/ui.js

const tagEmojiMap = {
  shop: '🛍️',
  cafe: '☕️',
  park: '🌳',
  restaurant: '🍽️',
  museum: '🏛️',
  beach: '🏖️',
  bar: '🍻',
  hotel: '🏨',
  gallery: '🖼️',
  theater: '🎭',
  hiking: '🥾',
  bookstore: '📚',
  vintage: '🧥',
  dessert: '🍰',
  bakery: '🥐',
  nature: '🌲',
  night_club: '🌃',
  health: '🏥',
  culture: '🎨',
  book_store: '📖',
};

export function clearResults() {
  const resultsDiv = document.getElementById('results');
  resultsDiv.innerHTML = '';
}

export function displayResults(results) {
  const resultsDiv = document.getElementById('results');

  if (!results || results.length === 0) {
    resultsDiv.innerHTML = '<p>No results found.</p>';
    return;
  }

  results.forEach(item => {
    const div = document.createElement('div');
    div.className = 'result';

    let tagsHTML = '';
    if (item.tags) {
      const tags = item.tags
        .replace(/[{}]/g, '')
        .split(',')
        .map(tag => tag.trim())
        .filter(tag => tag.length > 0);

      tagsHTML = tags.map(tag => {
        const cleanTag = tag.replace(/_/g, ' ').toLowerCase();
        const emoji = tagEmojiMap[cleanTag] || '🏷️';
        const displayTag = cleanTag.split(' ').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
        return `<span class="tag">${emoji} ${displayTag}</span>`;
      }).join(' ');
    }

    // Format scores as percentages
    const hybridPercent = (item.hybrid_score * 100).toFixed(1);
    const densePercent = (item.dense_score * 100).toFixed(1);
    const sparsePercent = (item.sparse_score * 100).toFixed(1);
    const imagePercent = item.image_score ? (item.image_score * 100).toFixed(1) : null;

    div.innerHTML = `
      <h3>${item.name || 'Unnamed Place'} ${item.emojis || ''}</h3>
      <p>Neighborhood: ${item.neighborhood || 'Unknown'}</p>
      <div class="tags">${tagsHTML}</div>
      <p>Description: ${item.description || 'No description available.'}</p>
      <div class="scores">
        <div class="score-bar">
          <div class="score-fill" style="width: ${hybridPercent}%"></div>
          <span class="score-label">Match Score: ${hybridPercent}%</span>
        </div>
        <div class="score-details">
          <span>Dense: ${densePercent}%</span>
          <span>Sparse: ${sparsePercent}%</span>
          ${imagePercent ? `<span>Image: ${imagePercent}%</span>` : ''}
        </div>
      </div>
    `;
    resultsDiv.appendChild(div);
  });
}
