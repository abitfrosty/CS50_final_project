
function listener() {

    const notifications = document.getElementById('notifications');
    rebindSubmit(document.getElementById('formUpdateName'));
    rebindSubmit(document.getElementById('formUpdatePassword'));
    rebindSubmit(document.getElementById('formUpdateProfile'));
    
    function update(myForm, lastInput) {
        const xhr = new XMLHttpRequest();

        xhr.onload = function() {
          if (xhr.readyState === xhr.DONE && xhr.status === 200) {
            notifications.insertAdjacentHTML('afterbegin', xhr.response);
            alertTimer();
            // Bootstrap's button focus fix
            lastInput.focus(); lastInput.blur();
              }
          }

        xhr.onerror = function() {
          dump("Error while getting xhr.");
        }
    
        xhr.open(myForm.method, myForm.action, true);
        xhr.responseType = "json";
        xhr.send(new FormData(myForm));
    }

    function rebindSubmit(submitForm){
        submitForm.addEventListener('submit', function(evt) {
            evt.preventDefault();
            update(submitForm, submitForm.elements[submitForm.length-2]);
        });
    }
        
    function alertTimer() {
        //.fadeTo(3000, 0)
        $(".alert").first().hide().slideDown(500).delay(4000).slideUp(200, function(){
            $(this).remove(); 
        });
    }
    
    $('#formUpdatePassword').on('submit', function() {
        $(this).each(function() {
             this.reset();
        });
    });
}


document.addEventListener('DOMContentLoaded', listener);

