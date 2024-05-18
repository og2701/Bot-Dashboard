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
