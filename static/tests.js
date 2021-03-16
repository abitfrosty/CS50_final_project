function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
    
    console.log("HELLO?")
    
    async function startExample(exampleTime=0, exampleCount=0, index=1) {
        while (true) {
            $('span#exampleTime'+idx)[0].textContent = exampleTime;
            sleep(1000);
            exampleTime -= 1;
        }
    }

    async function startTotal(totalTime=0) {
        while (true) {
            $('span#totalTime')[0].textContent = totalTime;
            sleep(1000);
            totalTime += 1;
        }
    }

    function startTimers(totalTime=0, exampleTime=0, exampleCount=0, index=1) {
        startTotal(totalTime);
        startExample(exampleTime, exampleCount, index);
    }

    function bindTimers(index, exampleCount) {
        
    }

    function generateTest() {
        let totalTime = 0;
        let exampleTime = 0;
        let index = 1;
        exampleCount = 0;
        const level = $('input[name="level"]').val();
        const questions = $('input[name="questions"]').val();
        const time = $('input[name="time"]').val();
        console.log("BEFORE AJAX")
        $.ajax({
          url: "/generate_test",
          type: "get",
          data: {level: level, questions: questions, time: time},
          success: function(response) {
          console.log("SUCCESS AJAX")
            if (response.length) {
            console.log("BEFORE .html(response)")
                $("#test").html(response);
                console.log("AFTER .html(response)")
                exampleTime = response.timegiven;
                exampleCount = response.length;
                index = response[0].number;
                console.log("BEFORE TIMERS")
                bindTimers(index, exampleCount);
                startTimers(totalTime, exampleTime, exampleCount, index);
                console.log("AFTER TIMERS")
            }
            // Added return to / if query is empty
            // if (text === "") {$.ajax({url: "/",type: "get", success: (args) => {console.log("success: empty string");}, error: (arge) => {console.log("error: empty string");}});}
            },
          error: function(xhr) {
          console.log("ERROR")
            //Do Something to handle error
          }
        });
        console.log("FUNCTION END")
    }

    $('#generateTest').on('click', function (e) {
        console.log("CLICKED")
        generateTest();
        console.log("BEFORE PREVENT DEFAULT")
        e.preventDefault();
        console.log("AFTER PREVENT DEFAULT")
});


/*
function addExample(ex) {
    const divExample =  $('div#example');
    
    divExample.innerHTML = '<form action="/example_answer" method="post" class="row g-1"><div class="col-md-4"><input autocomplete="off" class="form-control" name="example" type="text" value=/"' + ex.example + '/"><input value=/"' + ex.number +'/" name="number" type="hidden"><input value=/"' + ex.tests_id + '/" name="tests_id" type="hidden"></div><div class="col-md-4"><input class="form-control" autofocus name="answer" placeholder="?" type="number"></div><div class="col-md-4"><button class="btn-primary form-control" type="submit">Next</button></div></form>;
}*/

}

document.addEventListener('DOMContentLoaded', listener);
