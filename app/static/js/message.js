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
