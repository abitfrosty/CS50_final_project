function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
    
    function updateName() {
        const inputName = $('input[name="name"]');
        const name = inputName.val();
        $.ajax({
            method: "POST",
            url: "/update_name",
            data: {name: name}
        })
        .done(function(data) {
            // My hotfix to Bootstrap's button focus
            inputName.focus().blur();
        })
        .fail(() => {
            console.log("Name update failed");
        });
    }
    
    $('#formUpdateName').on('submit', function (e) {
     updateName();
     e.preventDefault();
     });
    
}

document.addEventListener('DOMContentLoaded', listener);
