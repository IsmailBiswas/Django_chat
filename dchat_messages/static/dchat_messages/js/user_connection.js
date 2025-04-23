// Clicks the submit button when the user presses the enter key.
document.querySelector("#message-text-input").onkeyup = function(e) {
    if (e.key === "Enter") {
        document.querySelector("#message-submit-btn").click();
    }
};

document.querySelector("#message-text-input").focus();


function generateRandomString() {
    return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

// Retrieves data from the message-input and file-input, also clears the inputs.
function sendData() {
    const messageInput = document.querySelector("#message-text-input");
    const fileInput = document.querySelector("#message-file-input");
    const message = messageInput.value;
    const connection = document.getElementById("connection-id");
    const recipientType = connection.getAttribute("data-connection-type");
    const recipient = connection.getAttribute("data-username");

    var messageUniqueID = "";
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isInsecure = window.location.protocol === "http:"
    // On mobile devices there is no `crypto.randomUUID` function available in
    // insecure connection.
    if (isMobile && isInsecure) {
        messageUniqueID = generateRandomString()
    } else {
        messageUniqueID = crypto.randomUUID();
    }

    var fileName = "";
    var isAttachment = false;
    var attachment = null;

    // const message_unique_id = "what-will-happen-if-value-is-not-unique";
    if (fileInput.files.length > 0) {
        isAttachment = true;
        fileName = fileInput.files[0].name;
        attachment = fileInput.files[0];
    }

    const csrftoken = getCookie('csrftoken');
    const formData = new FormData();
    formData.set("attachment", attachment);
    formData.set("csrfmiddlewaretoken", csrftoken);
    formData.set("message", message);
    formData.set("message_unique_id", messageUniqueID);
    formData.set("recipient", recipient);
    formData.set("recipient_type", recipientType);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/messages/message/")
    xhr.send(formData)

    // clears text input
    messageInput.value = "";
    // Clears the file input.
    removeSelectedFile()
}

function appendImage(data) {
    const imagePreviewSkeleton = document.getElementById(
        "image-preview-skeleton"
    );
    const messageContainer = document.getElementById("message-container");
    const clonedDiv = imagePreviewSkeleton.cloneNode(true);
    clonedDiv.classList.remove("hidden")
    var openInNewWindowLink = clonedDiv.querySelector(".open-in-new-window")
    const imageElement = clonedDiv.querySelector("img")
    var downloadLink = clonedDiv.querySelector(".download-link")
    const media_server_base_url = clonedDiv.getAttribute("data-media-server-base-url");

    openInNewWindowLink.href = media_server_base_url + data.file_path + "?token=" + data.access_token + "&exp_time=" + data.exp_time + "&hmac=" + data.hmac;
    imageElement.src = media_server_base_url + data.file_path + "?token=" + data.access_token + "&exp_time=" + data.exp_time + "&hmac=" + data.hmac;
    downloadLink.href = media_server_base_url + data.file_path + "?token=" + data.access_token + "&exp_time=" + data.exp_time + "&hmac=" + data.hmac + "&download_type=attachment";
    messageContainer.appendChild(clonedDiv)

}

function appendFile(data) {
    const imagePreviewSkeleton = document.getElementById(
        "attachment-preview-skeleton"
    );
    const messageContainer = document.getElementById("message-container");
    const clonedDiv = imagePreviewSkeleton.cloneNode(true);
    clonedDiv.classList.remove("hidden")
    var downloadLink = clonedDiv.querySelector(".download-link")
    var fileName = clonedDiv.querySelector(".attachment-filename")
    const media_server_base_url = clonedDiv.getAttribute("data-media-server-base-url");
    downloadLink.href = media_server_base_url + data.file_path + "?token=" + data.access_token + "&exp_time=" + data.exp_time + "&hmac=" + data.hmac + "&download_type=attachment";
    fileName.innerText = data.file_name
    messageContainer.appendChild(clonedDiv)

}

function appendMessage(data) {
    if (data.is_attachment) {
        if (data.mime_type.includes("image")) {
            appendImage(data)
        } else {
            appendFile(data)
        }
    } else {
        if (data.message.length > 0) {

            const messageContainerSkeleton = document.getElementById(
                "text-container-skeleton"
            );
            const messageContainer = document.getElementById("message-container");

            const clonedDiv = messageContainerSkeleton.cloneNode(true);
            clonedDiv.classList.remove("hidden");
            textParagraph = clonedDiv.querySelector("p");
            textParagraph.textContent = data.message;
            messageContainer.appendChild(clonedDiv);

            if (data.sender != data.recipient) {
                textParagraph.classList.add("border-green-300");
            }
        }
    }
}

document.querySelector("#message-submit-btn").onclick = function(e) {
    sendData()
};

function resetNotificationCounter() {
    const connection = document.getElementById("connection-id");
    const sender = connection.getAttribute("data-username");
    // const sender = connection.innerText;

    // This function takes the sender username and a boolean argument that
    // indicates should it reset the counter to zero and hide message counter
    // icon.
    updateUnreadMessageCounter(sender, true)
}

resetNotificationCounter()

function showSelectedFileName() {
    const fileInput = document.getElementById('message-file-input')
    const fileNameSpan = document.getElementById('selected-file-name')
    const fileInputCleanBtn = document.getElementById('file-input-clean-btn')
    if (fileInput.files.length > 0) {
        fileNameSpan.textContent = fileInput.files[0].name;
        fileInputCleanBtn.classList.remove("hidden")
    } else {
        fileInputCleanBtn.classList.add("hidden")
        fileNameSpan.textContent = '';
    }
}

function removeSelectedFile() {
    const fileInput = document.getElementById('message-file-input')
    fileInput.value = ''
    showSelectedFileName()
}
