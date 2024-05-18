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

    setupThemeToggle();
    setupFormSubmissions();
});

function setupThemeToggle() {
    const toggleSwitch = document.getElementById('theme-toggle');
    const themeRed = document.getElementById('theme-red');
    const themeBlue = document.getElementById('theme-blue');
    const themeGreen = document.getElementById('theme-green');

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

    themeRed.addEventListener('click', function() {
        setColorScheme('red-theme');
    });

    themeBlue.addEventListener('click', function() {
        setColorScheme('blue-theme');
    });

    themeGreen.addEventListener('click', function() {
        setColorScheme('green-theme');
    });

    function setColorScheme(color) {
        document.body.classList.remove('red-theme', 'blue-theme', 'green-theme');
        document.body.classList.add(color);
        localStorage.setItem('color-scheme', color);
    }
}

function setupFormSubmissions() {
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
}
