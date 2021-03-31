function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function listener() {
    
    let globalTimer;

    let exampleTime = 0;
    let timeGiven = 0;
    
    function updateExampleTime(index) {
        et = Date.now()-exampleTime;
        $('#exampleTime'+index)[0].textContent = et/1000+' ms';
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
        startGlobalTime();
        startExampleTime();
    }

    function disableForm(form, elements=[], disable=true) {
        if (!elements instanceof Array) {
            return;
        }
        if (!elements.length) {
            elements = ['input','label','select','textarea','button','fieldset','legend','datalist','output','option','optgroup'];
        }
        elements.forEach(function(element, index) {
            [...form.getElementsByTagName(element)].forEach(function(item, idx) {
                if (disable) {
                    item.setAttribute("disabled","");
                } else {
                    item.removeAttribute("disabled");
                }
            });
        });
    }


    function rebindSubmit(index, exampleCount) {
    
        var myForms = [];
        for (i=index; i<=exampleCount; i++) {
            myForms.push($('#example'+i));
        }
        const len = myForms.length;
        myForms.forEach(function(item, index, array) {
                item.on('submit', function(evt) {
                evt.preventDefault();
                $('#example'+(index+1)+' input[name="timespent"]').attr("value", $('#exampleTime'+(index+1))[0].textContent);
                updateExampleTime(index+1);
                $.ajax({
                    async: true,
                    url: item[0].action,
                    type: item[0].method,
                    data: item.serialize(),
                    success: function(response) {
                        $('#example'+(index+1)+' input[name="eval"]').attr("value", response['eval'])
                        disableForm($('#example'+(index+1))[0]);
                        if (index+1 >= array.length) {
                            clearInterval(globalTimer);
                            testFinished();
                        } else {
                            startExampleTime();
                            hideExample(index+2, false);
                            focusExample(index+2);
                        }
                        
                    },
                    error: function(e) {
                      console.log("ERROR", e);
                    }
                });
            });
        });
    }
        

    function focusExample(index) {
        $('#example'+index+' input[name="answer"]')[0].focus();
    }

    function hideExample(index, hide=true) {
        $('#example'+index).attr("hidden", hide);
    }
    
    function hideExamples(index, exampleCount) {
        for (i=index; i<=exampleCount; i++) {
            hideExample(i, true);
            if (i == exampleCount) {
                const button = $('#example'+i+' :submit');
                button[0].innerText = button[0].innerText.replace('Next', 'Last');
            }
        }
    }
    
    function testStart(form) {
        $.ajax({
          url: form.action,
          type: form.method,
          data: $(form).serialize(),
          success: function(response) {
            if (response.length) {
                $("#test").append(response);
                //timeGiven = parseInt($("#exampleTimeGiven")[0].value, 10)/1000;
                //let index = parseInt($("#exampleStartIndex")[0].value, 10);
                let exampleCount = parseInt($("#exampleCount")[0].value, 10);
                let index = 1;
                disableForm(form);
                $("#testQuery")[0].setAttribute("hidden","");
                focusExample(index);
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

    function testFinished() {
    
        $('h4[hidden]')[0].removeAttribute('hidden');
        
        //const index = parseInt($("#exampleStartIndex")[0].value, 10);
        const exampleCount = parseInt($("#exampleCount")[0].value, 10);
        const index = 1;
        for (i=index;i<=exampleCount;i++){
            $('#exampleTime'+i)[0].removeAttribute('hidden');
        }
        [...$('input[name="eval"]')].forEach(function(item,idx){
            var answer = item.parentElement.querySelector('input[name="answer"]');
            if (parseInt(item.value,10)-parseInt(answer.value,10)) {
                answer.style.backgroundColor="#faa";
            } else {
                answer.style.backgroundColor="#afa";
            }
        });
        /*
        <h4 hidden>Test is finished</h4>
        <input class="form-control text-center" value="" name="eval" type="number" hidden>
        <p class="pb-2 pt-2 m-0"><span id="exampleTime{{ example.number }}" hidden></span></p>
        timeGiven-<input value="0" name="timespent" type="hidden">
        */
    }

    $('#testStart').on('submit', function (evt) {
        evt.preventDefault();
        testStart(this);
        });
    
    $('#testContinue').on('submit', function (evt) {
        evt.preventDefault();
        testStart(this);
        });

}

document.addEventListener('DOMContentLoaded', listener);
