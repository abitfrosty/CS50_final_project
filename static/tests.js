function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
    
    console.log("HELLO?");
    
    function startExample(exampleTime=0, exampleCount=0, index=1) {
        while (true) {
            $('span#exampleTime'+index)[0].textContent = exampleTime;
            delay(1000);
            exampleTime -= 1;
            
        }
    }

    function startTotal(totalTime=0) {
        while (true) {
            $('span#totalTime')[0].textContent = totalTime;
            delay(1000);
            totalTime += 1;
        }
    }

    function startTimers(totalTime=0, exampleTime=0, exampleCount=0, index=1) {
        //startTotal(totalTime);
        //startExample(exampleTime, exampleCount, index);
    }

    function rebindSubmit(index, exampleCount) {
        for (i=index, i-index<exampleCount, i++) {
            $('#example'+index).on('submit', function(evt) {
                evt.preventDefault();
                this.$('input[name="timespent"]').attr("value", this.$('span#exampleTime'+index)[0].textContent);
                $.ajax({
                    async: true,
                    url: this.action,
                    type: this.method,
                    data: this.serialize(),
                    success: function(response) {
                        this.$('input[name="eval"]').attr("value", response.eval)
                        this.prop("disabled", true);
                        // TODO Stop timer
                    },
                    error: function(e) {
                      console.log("ERROR", e);
                      // Handle error
                    }
                });
            });
        }
    }

    function hideExamples(index, exampleCount) {
        for (i=index, i<exampleCount, i++) {
            $('#example'+index).attr("hidden", true)
        }
    }
    function generateTest(form) {
        let totalTime = 0;
        let exampleTime = 0;
        let index = 1;
        exampleCount = 0;
        /*const level = $('input[name="level"]').val();
        const questions = $('input[name="questions"]').val();
        const time = $('input[name="time"]').val();
        const form = $('#generateTest');*/
        console.log("BEFORE AJAX");
        //console.log($('#generateTest').serialize());
        $.ajax({
          async: true,
          url: form.attr('action'),
          type: form.attr('method'),
          data: form.serialize(),
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
                hideExamples(index, exampleCount);
                rebindSubmit(index, exampleCount);
                startTimers(totalTime, exampleTime, exampleCount, index);
                console.log("AFTER TIMERS");
            }
            // else
            },
          error: function(e) {
            console.log("ERROR", e);
            // Handle error
          }
        });
        console.log("FUNCTION END");
    }

    $('#generateTest').on('submit', function (evt) {
        console.log("CLICKED");
        console.log("BEFORE PREVENT DEFAULT");
        evt.preventDefault();
        console.log("AFTER PREVENT DEFAULT");
        generateTest(this);
        });

}

document.addEventListener('DOMContentLoaded', listener);
