function listener() {

    //$('[data-bs-toggle="popover"]').popover();
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl)
    })
}


document.addEventListener('DOMContentLoaded', listener);
