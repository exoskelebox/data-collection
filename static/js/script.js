/*!
  * General application functions
  */

function blockui(message) {
    $('.overlay > .overlay-content > .message').text(message);
    $('.overlay').addClass('d-flex').removeClass('d-none');
}

function flash(message, category) {
    $('#flash').append(
        `<div class="alert alert-${category} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
        </div>`);
}

function clearFlash() {
    $('#flash').empty();
}

function unblockui() {
    $('.overlay').removeClass('d-flex').addClass('d-none');
}