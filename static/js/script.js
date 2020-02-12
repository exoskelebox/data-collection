/*!
  * General application functions
  */

 function blockui(message) {
    $('.overlay > .overlay-content > .message').text(message);
    $('.overlay').addClass('d-flex').removeClass('d-none');
}

function toast(message, style = 'primary', delay = 1500) {
    $('.toast').addClass('bg-' + style);
    $('.toast').toast({
        delay: delay,
        autohide: true,
        animation: true
    });
    $('.toast > .toast-body').text(message);
    $('.toast').toast('show');
}

function unblockui() {
    $('.overlay').removeClass('d-flex').addClass('d-none');
}