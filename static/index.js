function listener() {
        
    $(() => {$('a.alert-link').bind('click', () => {$('a.alert-link')[0].style='display: none';$('#qname')[0].style='display: inline';$('input[name="name"]').focus();})});
    
    function updateName() {
        const inputName = $('input[name="name"]');
        const name = inputName.val();
        $.ajax({
            method: "POST",
            url: "/name_update",
            data: {name: name}
        })
        .done(function(data) {
            if (data) {
                $('#userName')[0].textContent = name;
                $(".alert").alert('close');
            }
        })
        .fail(() => {
            $('#formNameUpdate')[0].reset();
            inputName.focus();
        });
    }
    
    $('#formNameUpdate').on('submit', function (e) {
     updateName();
     e.preventDefault();
     });
    
}

document.addEventListener('DOMContentLoaded', listener);
