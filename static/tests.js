function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {

/*
function addExample(ex) {
    const divExample =  $('div#example');
    
    divExample.innerHTML = '<form action="/example_answer" method="post" class="row g-1"><div class="col-md-4"><input autocomplete="off" class="form-control" name="example" type="text" value=/"' + ex.example + '/"><input value=/"' + ex.number +'/" name="number" type="hidden"><input value=/"' + ex.tests_id + '/" name="tests_id" type="hidden"></div><div class="col-md-4"><input class="form-control" autofocus name="answer" placeholder="?" type="number"></div><div class="col-md-4"><button class="btn-primary form-control" type="submit">Next</button></div></form>;
}


() => {
totalTime = 0;
for example in tests:
    addExample(example){}.done().fail();
}

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
            if (data) {
                $('span#userName').text(data.name);
                $(".alert").alert('close');
            } else {
                formUpdate[0].reset();
                //errorMessage('', "Name update failed");
                inputName.focus();
            }
        })
        .fail(() => {
            console.log("Name update failed");
            formUpdate[0].reset();
            //errorMessage('', "Name update failed");
            inputName.focus();
        });
    }
    
    $('#formUpdateName').on('submit', function (e) {
     updateName();
     e.preventDefault();
     });
    */
}

document.addEventListener('DOMContentLoaded', listener);
