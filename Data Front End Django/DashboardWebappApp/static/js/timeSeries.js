var PDWSelect = []

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const csrftoken = getCookie('csrftoken');

$(function() {    
    /* Called when the Update button is clicked. Only updates the min and max time and then calls createLineChart(), which gets the new data  */
    $("#render").click(function() {
        //contingency if we want to add pre proccesing before geneating
        createChart(['time'],DataManager.getActive());   
    });
	$('#download').click(function(){ //Look into maybe just running getRawData() instead? Pretty slow though. Would just be simplier to do a filter or subset but var data sucks and is complicated.
        //I love copying code its so nice
        let curTags = DataManager.getActive()
        if (globalData != undefined && curTags.every(t => Object.keys(globalData[0]).includes(t))){
            DataManager.dataToCSV(curTags)
        }else{
            DataManager.downloadCSV(curTags)   
        }

        
	})
});

/* Initially called upon page load. Where the magic begins. */
function preloadTags() {
    $.ajax({
        url:"getloads",
        type: "POST",
        async: true,
        data: { "csrfmiddlewaretoken": csrftoken, },
        success:function(data){
            var data = JSON.parse(data);
            
            let keys = Object.keys(data);
            let times = data['times'];
            keys.splice(keys.indexOf('times'),1)
            //I do not wish to do this here but it must be done.
            //Converting times
            //Also catching since times is not in the forEach key, and we are doing an index access on one that mightn to exists
            try{
                if(times[0] != null && times[1] != null ){
                    console.log('valid times')
                    let minTime = times[0].replace(' ', 'T').split('+')[0];
                    let maxTime = times[1].replace(' ', 'T').split('+')[0];
                    console.log($('#global-min').val())
                    $('#global-min').val(minTime)
                    $('#global-max').val(maxTime)
                    globalMinimumTime = new Date($('#global-min').val())
                    globalMaximumTime = new Date($('#global-max').val())
                }
                keys.forEach(function(key,index) {
                    tagLabels.push(key);
                    tagActive.push(key)
                    tagPlants.push(data[key][1]);
                    tagEng.push(data[key][2]);
                    tagDesc.push(data[key[3]]);
                    let c;
                    if(tagColor[key] == undefined){
                        tagColor[key] = color.pop();
                        c = tagColor[key];

                    }else{
                        c = d3.color(tagColor[key])
                        }


                    let div = document.createElement("div");
                    div.setAttribute("class", "hierarchy items-body-content tagFilters")
                    div.setAttribute("id", key)
                    div.setAttribute("onclick", "removeTag(this);")
                    div.innerHTML = `<span class="colorLabel" style="background:${c};"></span>`;
                    div.innerHTML += `<p>${key} - ${data[key][2]}<br>  ${data[key][3]} </p>`;
                    document.getElementById("tagNav").appendChild(div);


                });
            }
            catch(err){
                console.log(err);
            }
            finally{
                document.getElementById("stopRightThere").remove()
            }
          
			
        }
    });
	

	
	
	
}
