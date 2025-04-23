
// Shows selected image file preview
function showSelectedProfilePic(event) {
    var file = event.target.files[0];
    var reader = new FileReader();

    reader.onload = function(e) {
        // The result attribute contains a data URL representing the file's data.
        const profilePictureDiv = document.getElementById("profile-picture-div")
        const selectedProfilePictureDiv = document.getElementById("selected-profile-picture-div")
        const actionButtonsDiv = document.getElementById("profile-update-action-buttons")
        profilePictureDiv.classList.add("hidden")
        selectedProfilePictureDiv.classList.remove("hidden")
        actionButtonsDiv.classList.remove("hidden")
        var imgPreview = document.getElementById('selected-profile-picture');
        imgPreview.src = e.target.result;
    };

    reader.readAsDataURL(file);
}

function clearPicturePreview(){
    const profilePictureDiv = document.getElementById("profile-picture-div")
    const selectedProfilePictureDiv = document.getElementById("selected-profile-picture-div")
    profilePictureDiv.classList.remove("hidden")
    selectedProfilePictureDiv.classList.add("hidden")
}

function displayNameEdit(){
    const displayName = document.getElementById("display-name")
    const displayNameEdit = document.getElementById("edit-display-name")
    const actionButtonsDiv = document.getElementById("profile-update-action-buttons")
    displayName.classList.add("hidden")
    displayNameEdit.classList.remove("hidden")
    actionButtonsDiv.classList.remove("hidden")
}

function closeEdit(){
    const displayName = document.getElementById("display-name")
    const displayNameEdit = document.getElementById("edit-display-name")
    const actionButtonsDiv = document.getElementById("profile-update-action-buttons")
    displayName.classList.remove("hidden")
    displayNameEdit.classList.add("hidden")
    actionButtonsDiv.classList.add("hidden")
    clearPicturePreview()
}

function profileUpdateFormActions(){
    const clearButton = document.getElementById("profile-update-form-clear")
    const displayName = document.getElementById("display-name")
    displayName.addEventListener("click", displayNameEdit)
    clearButton.addEventListener("click", closeEdit)
}

profileUpdateFormActions()

function profileUpdateSubmit(){
    const profileUpdateForm = document.getElementById("user-profile-update-form")
    profileUpdateForm.addEventListener("submit", (event)=>{
        const clearButton = document.getElementById("profile-update-form-clear")
        clearButton.addEventListener("click", closeEdit)
        htmx.trigger(htmx.find('body'),'profileUpdateEvent')
    })
}
profileUpdateSubmit()
