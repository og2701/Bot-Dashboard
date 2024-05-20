function showEmojiManagement() {
    document.getElementById('home-info').style.display = 'none';
    document.getElementById('message-list').style.display = 'none';
    document.getElementById('message-form').style.display = 'none';
    document.getElementById('emoji-management').style.display = 'block';
    document.querySelector('.sidebar').style.display = 'block';

    fetch('/get_emojis')
        .then(response => response.json())
        .then(emojis => {
            const emojiList = document.getElementById('emoji-list');
            emojiList.innerHTML = '';
            emojis.forEach(emoji => {
                const emojiElement = document.createElement('div');
                emojiElement.classList.add('emoji-item');
                emojiElement.innerHTML = `
                    <img src="${emoji.url}" alt="${emoji.name}" class="emoji-image">
                    <div class="emoji-name">${emoji.name}</div>
                    <button onclick="confirmDeleteEmoji('${emoji.id}', '${emoji.url}', '${emoji.name}')">Delete</button>
                `;
                emojiList.appendChild(emojiElement);
            });
        });
}

function confirmDeleteEmoji(emojiId, emojiUrl, emojiName) {
    const confirmation = confirm(`Are you sure you want to delete this emoji?

${emojiName}`);
    if (confirmation) {
        deleteEmoji(emojiId);
    }
}

function deleteEmoji(emojiId) {
    fetch(`/delete_emoji/${emojiId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showSuccessMessage('Emoji deleted successfully');
                showEmojiManagement();
            } else {
                showErrorMessage('Failed to delete emoji');
            }
        });
}

function filterEmojis() {
    const searchValue = document.getElementById('emoji-search').value.toLowerCase();
    document.querySelectorAll('.emoji-item').forEach(function(emojiItem) {
        const emojiName = emojiItem.querySelector('.emoji-name').innerText.toLowerCase();
        if (emojiName.includes(searchValue)) {
            emojiItem.style.display = 'flex';
        } else {
            emojiItem.style.display = 'none';
        }
    });
}
