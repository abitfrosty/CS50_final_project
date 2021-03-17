function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
    
    console.log("HELLO?");
    
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
        //startTotal(totalTime);
        //startExample(exampleTime, exampleCount, index);
    }

    function bindTimers(index, exampleCount) {
        
    }

    function generateTest() {
        let totalTime = 0;
        let exampleTime = 0;
        let index = 1;
        exampleCount = 0;
        /*const level = $('input[name="level"]').val();
        const questions = $('input[name="questions"]').val();
        const time = $('input[name="time"]').val();*/
        const form = $('#generateTest');
        console.log("BEFORE AJAX");
        console.log($('#generateTest').serialize());
        $.ajax({
          async: true,
          url: form.attr('action'),
          type: form.attr('method'),
          data : form.serialize(),
          //data: {level: level, questions: questions, time: time},
          success: function(response) {
          console.log("SUCCESS AJAX");
            if (response.length) {
            console.log("BEFORE .html(response)");
            console.log(String(response));
                $("#test").append(response);
                console.log("AFTER .html(response)");
                exampleTime = response.timegiven;
                exampleCount = response.length;
                index = response[0].number;
                console.log("BEFORE TIMERS");
                bindTimers(index, exampleCount);
                startTimers(totalTime, exampleTime, exampleCount, index);
                console.log("AFTER TIMERS");
            }
            // else
            },
          error: function(xhr) {
          console.log("ERROR");
            //Do Something to handle error
          }
        });
        console.log("FUNCTION END");
    }

    $('#generateTest button[type="submit"]').on('click', function (e) {
        console.log("CLICKED");
        console.log("BEFORE PREVENT DEFAULT");
        e.preventDefault();
        console.log("AFTER PREVENT DEFAULT");
        generateTest();
        });

}

document.addEventListener('DOMContentLoaded', listener);
