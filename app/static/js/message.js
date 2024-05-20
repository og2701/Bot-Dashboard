function selectChannel(id, name) {
    document.getElementById('channel_id').value = id;
    document.getElementById('selected_channel').innerText = name;
    document.getElementById('home-info').style.display = 'none'; 
    document.getElementById('message-list').style.display = 'block';
    document.getElementById('message-form').style.display = 'block';
    document.getElementById('emoji-management').style.display = 'none';
    document.getElementById('message-list').innerHTML = '';

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
            messageList.scrollTop = messageList.scrollHeight;
        });
}

function deselectChannel() {
    document.getElementById('channel_id').value = '';
    document.getElementById('selected_channel').innerText = 'None';
    document.getElementById('home-info').style.display = 'block';
    document.getElementById('message-list').style.display = 'none';
    document.getElementById('message-form').style.display = 'none';
    document.getElementById('message-list').innerHTML = '';
    document.getElementById('emoji-management').style.display = 'none';
    document.querySelector('.sidebar').style.display = 'block';

    const searchInput = document.getElementById('search');
    searchInput.value = '';

    filterChannels('');
}
