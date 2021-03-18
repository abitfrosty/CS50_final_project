function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
    
    let globalTimer;

    let exampleTime = 0;
    let timeGiven = 0;
    
    function updateExampleTime(index) {
        et = Date.now()-exampleTime;
        console.log(index, typeof index, $('#exampleTime'+index));
        $('#exampleTime'+index)[0].textContent = et/1000;
        $('#example'+index+' input[name="timespent"]').attr("value", et);
    }
    
    function startExampleTime() {
        exampleTime = Date.now();
    }
    
    function startGlobalTime() {
        globalTime = Date.now();
        globalTimer = setInterval(()=>{
            $('#totalTime')[0].textContent = ((Date.now()-globalTime)/1000).toFixed(1);
            }, 100);
    }
    
    function startTimers(index) {
        console.log('startTimers');
        startGlobalTime();
        startExampleTime();
    }


    function rebindSubmit(index, exampleCount) {
    
        var myForms = [];
        for (i=index; i<exampleCount; i++) {
            myForms.push($('#example'+i));        
        }
        myForms.forEach(function(item, index) {
                let i = index+1;
                item.on('submit', function(evt) {
                evt.preventDefault();
                $('#example'+i+' input[name="timespent"]').attr("value", $('#exampleTime'+i)[0].textContent);
                //console.log(item, item[0].action, item[0].method, $(item).action, $(item).method, item.serialize());
                $.ajax({
                    async: true,
                    url: item[0].action,
                    type: item[0].method,
                    contentType: 'application/json;charset=UTF-8',
                    dataType: 'json',
                    //data: JSON.stringify(data, null, '\t'),
                    data: item.serialize(),
                    success: function(response) {
                        console.log(response);
                        $('#example'+i+' input[name="eval"]').attr("value", response['eval'])
                        $('#example'+i).prop("disabled", true);
                        
                        updateExampleTime(i);
                        if (i == exampleCount) {
                            clearInterval(globalTimer);
                        } else {
                            startExampleTime();
                            hideExample(i+1, false);
                        }
                        
                    },
                    error: function(e) {
                      console.log("ERROR", e);
                      // Handle error
                    }
                });
            });
        });
    }
        


    /*
    function rebindSubmit(index, exampleCount) {
        for (i=index; i<exampleCount; i++) {
            var anotherForm = $('#example'+i);
            anotherForm.on('submit', function(evt) {
                evt.preventDefault();
                $('#example'+i+' input[name="timespent"]').attr("value", $('#exampleTime'+i)[0].textContent);
                $.ajax({
                    async: true,
                    url: anotherForm.action,
                    type: anotherForm.method,
                    contentType: 'application/json;charset=UTF-8',
                    dataType: 'json',
                    //data: JSON.stringify(data, null, '\t'),
                    data: anotherForm.serialize(),
                    success: function(response) {
                        console.log(response);
                        $('#example'+i+' input[name="eval"]').attr("value", response['eval'])
                        anotherForm.prop("disabled", true);
                        
                        updateExampleTime(i);
                        if (i == exampleCount) {
                            clearInterval(globalTimer);
                        } else {
                            startExampleTime();
                            hideExample(i+1, false);
                        }
                        
                    },
                    error: function(e) {
                      console.log("ERROR", e);
                      // Handle error
                    }
                });
            });
        }
    }*/
    
    
    /*
    function rebindSubmit(index, exampleCount) {
            var anotherForm = $('#example1');
            anotherForm.on('submit', function(evt) {
                evt.preventDefault();
                $('#example1 input[name="timespent"]').attr("value", $('#exampleTime1')[0].textContent);
                $.ajax({
                    async: true,
                    url: anotherForm.action,
                    type: anotherForm.method,
                    contentType: 'application/json;charset=UTF-8',
                    dataType: 'json',
                    //data: JSON.stringify(data, null, '\t'),
                    data: anotherForm.serialize(),
                    success: function(response) {
                        console.log(response);
                        $('#example1 input[name="eval"]').attr("value", response['eval'])
                        anotherForm.prop("disabled", true);
                    },
                    error: function(e) {
                      console.log("ERROR", e);
                      // Handle error
                    }
                });
                updateExampleTime(1);
                if (2 == exampleCount) {
                    clearInterval(globalTimer);
                } else {
                    startExampleTime();
                    hideExample(2, false);
                }
            });
        }*/


    function hideExample(index, hide=true) {
        $('#example'+index).attr("hidden", hide);
    }
    
    function hideExamples(index, exampleCount) {
        for (i=index; i<=exampleCount; i++) {
            hideExample(i, true);
            if (i == exampleCount) {
                const button = $('#example'+i+' :submit');
                button[0].innerText = button[0].innerText.replace('Next', 'Finish');
            }
        }
    }
    
    function generateTest(form) {
        $.ajax({
          async: true,
          url: form.action,
          type: form.method,
          data: $(form).serialize(),
          success: function(response) {
            if (response.length) {
                $("#test").append(response);
                timeGiven = parseInt($("#exampleTimeGiven")[0].value, 10);
                let exampleCount = parseInt($("#exampleCount")[0].value, 10);
                let index = parseInt($("#exampleStartIndex")[0].value, 10);
                hideExamples(index+1, exampleCount);
                rebindSubmit(index, exampleCount);
                startTimers(index);
            }
                // else
            },
          error: function(e) {
            console.log("ERROR", e);
          }
        });
    }

    $('#generateTest').on('submit', function (evt) {
        evt.preventDefault();
        generateTest(this);
        });

}

document.addEventListener('DOMContentLoaded', listener);
