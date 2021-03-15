function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
        
    $(() => {$('a.alert-link').bind('click', () => {$('a.alert-link')[0].style='display: none';$('#qname')[0].style='display: inline';$('input[name="name"]').focus();})});
    
    function updateName() {
        const inputName = $('input[name="name"]');
        const name = inputName.val();
        $.ajax({
            method: "POST",
            url: "/update_name",
            data: {name: name}
        })
        .done(function(data) {
            if (data) {
                $('span#userName')[0].textContent = data.name;
                $(".alert").alert('close');
            }
        })
        .fail(() => {
            $('#formUpdateName')[0].reset();
            inputName.focus();
        });
    }
    
    $('#formUpdateName').on('submit', function (e) {
     updateName();
     e.preventDefault();
     });
    
}

document.addEventListener('DOMContentLoaded', listener);
