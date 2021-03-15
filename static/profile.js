function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
    function updateName() {
        const formUpdate = $('#formUpdateName');
        const inputName = $('input[name="name"]');
        const name = inputName.val();
        $.ajax({
            method: "POST",
            url: "/update_name",
            data: {name: name}
        })
        .done(function(data) {            
        })
        .fail(() => {
            console.log("Name update failed");
            //errorMessage('', "Name update failed");
            inputName.focus();
        });
    }
    
    $('#formUpdateName').on('submit', function (e) {
     updateName();
     e.preventDefault();
     });
    
}

document.addEventListener('DOMContentLoaded', listener);
