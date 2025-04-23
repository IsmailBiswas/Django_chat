const newConnectionEvent = new Event('newConnectionEvent');
const profileUpdateEvent = new Event('profileUpdateEvent');

function toggleLogoutModal() {
    var logoutModal = document.getElementById("logout-modal");
    var logoutModalBG = document.getElementById("logout-modal-bg");
    var siteContainer = document.getElementById("site-container");

    logoutModal.classList.toggle("hidden");
    logoutModalBG.classList.toggle("hidden");
    siteContainer.classList.toggle("brightness-50");
    siteContainer.classList.toggle("blur-sm");
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function toggleSocketDisconnectModal() {
    var disconnectModal = document.getElementById("websocket-disconnect-modal");
    var disconnectModalBG = document.getElementById("socket-disconnect-modal-bg");
    var siteContainer = document.getElementById("site-container");

    disconnectModal.classList.toggle("hidden");
    disconnectModalBG.classList.toggle("hidden");
    siteContainer.classList.toggle("brightness-50");
    siteContainer.classList.toggle("blur-sm");
}

function isFocusedOnSender(sender) {
    const focusedSender = document.getElementById("connection-id");
    const messageTextInput = document.getElementById("message-text-input")
    if (focusedSender && messageTextInput) {
        return focusedSender.dataset.username === sender ? true : false;
    } else {
        return false;
    }
}

function updateUnreadMessageCounter(sender_username, reset) {
    const senderDiv = document.getElementById(sender_username + "-notification");
    const notificationCount = senderDiv.querySelector("span");
    if (reset) {
        notificationCount.innerText = 0;
        senderDiv.classList.add("hidden");
    } else {
        senderDiv.classList.remove("hidden");
        notificationCount.innerText = Number(notificationCount.innerText) + 1;
    }
}

function handleIncomingSocketData(data) {
    if (data.message_type == "chat_message") {
        if (data.sender === data.recipient) {
            appendMessage(data);
        } else if (data.sender != data.recipient) {
            if (isFocusedOnSender(data.sender)) {
                // appendMessage is defined in `user_connection.js`
                appendMessage(data);
                sendMessageReadACK(data.sender)
            } else {
                updateUnreadMessageCounter(data.sender, false)
            }
        }
    }

    if (data.message_type == "new_connection") {
        document.dispatchEvent(newConnectionEvent)
    }

    if (data.message_type == "connection_accepted") {
        document.dispatchEvent(newConnectionEvent)
    }
}


const reconnectInterval = 1000
const maxReconnectAttempts = 2;
var reconnectAttempts = 0;

function connectWebSocket() {

    const userWebSocket = new WebSocket(
        "ws://" + window.location.host + "/ws/connection/"
    );

    userWebSocket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        handleIncomingSocketData(data);
    };

    userWebSocket.onclose = function(event) {
        console.log("WebSocket closed:", event);
        if (!event.wasClean && reconnectAttempts < maxReconnectAttempts) {
            console.log("Attempting to reconnect...");
            setTimeout(function() {
                reconnectAttempts++;
                connectWebSocket();
            }, reconnectInterval);
        } else {
            if (reconnectAttempts >= maxReconnectAttempts)
                toggleSocketDisconnectModal();
        }
    };
}

connectWebSocket()


// Sends a request indicating message has been read by user.
function sendMessageReadACK(sender) {
    const csrftoken = getCookie('csrftoken');
    const formData = new FormData();
    formData.set("sender", sender)
    formData.set("csrfmiddlewaretoken", csrftoken)

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/messages/messagereadack/")
    xhr.send(formData)
}

function clearUserSearch() {
    const searchResultDiv = document.getElementById("search-result");
    const searchClearButton = document.getElementById("clear-user-search");
    const userSearchInput = document.getElementById("user-search-input")
    searchResultDiv.classList.remove("h-64")
    searchResultDiv.classList.remove("border-b")
    userSearchInput.value = "";
    searchClearButton.classList.add("hidden");
    searchResultDiv.innerHTML = "";
}

const userSearchForm = document.getElementById('user-search-form')
userSearchForm.addEventListener("submit", () => {
    const searchClearButton = document.getElementById("clear-user-search");
    const searchResultDiv = document.getElementById("search-result");
    searchResultDiv.classList.add("border-b")
    searchResultDiv.classList.add("h-64")
    searchClearButton.classList.remove("hidden");
})
