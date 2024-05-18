document.addEventListener('DOMContentLoaded', function() {
    const selectedChannelId = document.getElementById('channel_id').value;
    const sidebar = document.querySelector('.sidebar');
    const savedScrollPosition = localStorage.getItem('scrollPosition');
    if (savedScrollPosition) {
        sidebar.scrollTop = savedScrollPosition;
    }

    if (selectedChannelId) {
        const selectedChannelElement = document.querySelector(`li[data-id="${selectedChannelId}"]`);
        if (selectedChannelElement) {
            selectChannel(selectedChannelId, selectedChannelElement.innerText);
        }
    } else {
        document.getElementById('home-info').style.display = 'block';
    }

    const searchInput = document.getElementById('search');
    const savedSearchTerm = localStorage.getItem('searchTerm');
    if (savedSearchTerm) {
        searchInput.value = savedSearchTerm;
        filterChannels(savedSearchTerm);
    }

    sidebar.addEventListener('scroll', function() {
        localStorage.setItem('scrollPosition', sidebar.scrollTop);
    });

    searchInput.addEventListener('input', function() {
        const searchValue = this.value.toLowerCase();
        localStorage.setItem('searchTerm', searchValue);
        filterChannels(searchValue);
    });

    const socket = io();
    socket.on('new_message', function(data) {
        if (data.channel_id == document.getElementById('channel_id').value) {
            const messageList = document.getElementById('message-list');
            const messageElement = document.createElement('div');
            messageElement.classList.add('message');
            messageElement.innerHTML = `
                <div class="author" style="color:${data.color}">${data.author}</div>
                <div class="content">${data.content}</div>
                <div class="timestamp">${data.timestamp}</div>`;
            messageList.appendChild(messageElement);
            messageList.scrollTop = messageList.scrollHeight; // Scroll to the bottom
        }
    });

    // Dark mode toggle
    const toggleSwitch = document.getElementById('theme-toggle');
    const themeRed = document.getElementById('theme-red');
    const themeBlue = document.getElementById('theme-blue');
    const themeGreen = document.getElementById('theme-green');

    // Load saved theme and color scheme from localStorage
    const currentTheme = localStorage.getItem('theme');
    const currentColorScheme = localStorage.getItem('color-scheme');

    if (currentTheme) {
        document.body.classList.add(currentTheme);
        if (currentTheme === 'dark-mode') {
            toggleSwitch.checked = true;
        }
    }

    if (currentColorScheme) {
        document.body.classList.add(currentColorScheme);
    }

    toggleSwitch.addEventListener('change', function() {
        if (toggleSwitch.checked) {
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
            localStorage.setItem('theme', 'light-mode');
        }
    });

    function setColorScheme(color) {
        document.body.classList.remove('red-theme', 'blue-theme', 'green-theme');
        document.body.classList.add(color);
        localStorage.setItem('color-scheme', color);
    }

    themeRed.addEventListener('click', function() {
        setColorScheme('red-theme');
    });

    themeBlue.addEventListener('click', function() {
        setColorScheme('blue-theme');
    });

    themeGreen.addEventListener('click', function() {
        setColorScheme('green-theme');
    });

    // Handle form submission
    const form = document.querySelector('#message-form form');
    form.addEventListener('submit', function(event) {
        event.preventDefault(); // Prevent the form from submitting the traditional way

        const formData = new FormData(form);
        const channelId = formData.get('channel_id');
        const message = formData.get('message');

        if (!message.trim()) {
            showErrorMessage('Message cannot be empty');
            return;
        }

        // Send the message using fetch
        fetch('/send_message', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
          .then(data => {
              if (data.success) {
                  const messageList = document.getElementById('message-list');
                  const messageElement = document.createElement('div');
                  messageElement.classList.add('message');
                  messageElement.innerHTML = `
                      <div class="author" style="color:${data.color}">${data.author}</div>
                      <div class="content">${message}</div>
                      <div class="timestamp">${data.timestamp}</div>`;
                  messageList.appendChild(messageElement);
                  messageList.scrollTop = messageList.scrollHeight; // Scroll to the bottom

                  // Clear the message input
                  document.getElementById('message').value = '';
              } else {
                  showErrorMessage('Failed to send message');
              }
          }).catch(error => {
              showErrorMessage('Failed to send message: ' + error.message);
          });
    });

    document.getElementById('emoji-upload-form').addEventListener('submit', function(event) {
        event.preventDefault();

        const formData = new FormData();
        const emojiFile = document.getElementById('emoji-file').files[0];
        const emojiName = document.getElementById('emoji-name').value;

        if (!emojiFile || !emojiName) {
            showErrorMessage('Both file and name are required');
            return;
        }

        formData.append('emoji-file', emojiFile);
        formData.append('emoji-name', emojiName);

        fetch('/upload_emoji', {
            method: 'POST',
            body: formData
        }).then(response => response.json())
          .then(data => {
              if (data.success) {
                  showSuccessMessage('Emoji uploaded successfully');
                  document.getElementById('emoji-file').value = '';
                  document.getElementById('emoji-name').value = '';
                  showEmojiManagement(); // Refresh the emoji list
              } else {
                  showErrorMessage(data.error || 'Failed to upload emoji');
              }
          }).catch(error => {
              showErrorMessage('Failed to upload emoji: ' + error.message);
          });
    });
});

function selectChannel(id, name) {
    document.getElementById('channel_id').value = id;
    document.getElementById('selected_channel').innerText = name;
    document.getElementById('home-info').style.display = 'none'; // Hide home info
    document.getElementById('message-list').style.display = 'block'; // Show message list
    document.getElementById('message-form').style.display = 'block'; // Show message form
    document.getElementById('emoji-management').style.display = 'none'; // Hide emoji management
    document.getElementById('message-list').innerHTML = ''; // Clear previous messages

    // Fetch the last 10 messages
    fetch(`/get_last_messages/${id}`)
        .then(response => response.json())
        .then(messages => {
            const messageList = document.getElementById('message-list');
            messages.reverse().forEach(message => {
                const messageElement = document.createElement('div');
                messageElement.classList.add('message');
                messageElement.innerHTML = `
                    <div class="author" style="color:${message.color}">${message.author}</div>
                    <div class="content">${message.content}</div>
                    <div class="timestamp">${message.timestamp}</div>`;
                messageList.appendChild(messageElement);
            });
            messageList.scrollTop = messageList.scrollHeight; // Scroll to the bottom
        });
}

function deselectChannel() {
    document.getElementById('channel_id').value = '';
    document.getElementById('selected_channel').innerText = 'None';
    document.getElementById('home-info').style.display = 'block'; // Show home info
    document.getElementById('message-list').style.display = 'none'; // Hide message list
    document.getElementById('message-form').style.display = 'none'; // Hide message form
    document.getElementById('message-list').innerHTML = ''; // Clear messages
    document.getElementById('emoji-management').style.display = 'none'; // Hide emoji management
    document.querySelector('.sidebar').style.display = 'block'; // Show channels panel

    // Clear the search bar
    const searchInput = document.getElementById('search');
    searchInput.value = '';

    // Reset the filtered channels
    filterChannels('');
}

function showEmojiManagement() {
    document.getElementById('home-info').style.display = 'none'; // Hide home info
    document.getElementById('message-list').style.display = 'none'; // Hide message list
    document.getElementById('message-form').style.display = 'none'; // Hide message form
    document.getElementById('emoji-management').style.display = 'block'; // Show emoji management
    document.querySelector('.sidebar').style.display = 'block'; // Show channels panel

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
    const confirmation = confirm(`Are you sure you want to delete this emoji?\n\n${emojiName}`);
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
                showEmojiManagement(); // Refresh the emoji list
            } else {
                showErrorMessage('Failed to delete emoji');
            }
        });
}

function filterChannels(searchValue) {
    document.querySelectorAll('.category').forEach(function(category) {
        let categoryHasVisibleChannels = false;
        category.querySelectorAll('ul li').forEach(function(channel) {
            if (channel.innerText.toLowerCase().includes(searchValue)) {
                channel.style.display = '';
                categoryHasVisibleChannels = true;
            } else {
                channel.style.display = 'none';
            }
        });
        if (categoryHasVisibleChannels) {
            category.style.display = '';
        } else {
            category.style.display = 'none';
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

function showErrorMessage(message) {
    const errorMessageElement = document.createElement('div');
    errorMessageElement.classList.add('error-message');
    errorMessageElement.innerText = message;

    const formGroup = document.querySelector('.form-group');
    formGroup.parentNode.insertBefore(errorMessageElement, formGroup);

    setTimeout(() => {
        errorMessageElement.remove();
    }, 5000);
}

function showSuccessMessage(message) {
    const successMessageElement = document.createElement('div');
    successMessageElement.classList.add('success-message');
    successMessageElement.innerText = message;

    const formGroup = document.querySelector('.form-group');
    formGroup.parentNode.insertBefore(successMessageElement, formGroup);

    setTimeout(() => {
        successMessageElement.remove();
    }, 5000);
}
