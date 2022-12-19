
var setReg = (obj) => {
    regressionType = obj.id.substring(3);
    document.getElementById('regButton').innerHTML =obj.innerHTML

    }
var setXAxis = (obj) => { // maybe can move it into above?
    tag = obj.getAttribute('id');
    if(xAxisTag.includes(tag)){
        xAxisTag.splice(xAxisTag.indexOf(tag),1)
        obj.setAttribute('style', 'opacity: .3')
        obj.style.opacity = '.3'
    }else{
        xAxisTag.push(tag)
        obj.setAttribute('style', 'opacity: 1')
        obj.style.opacity = '1'
        
    }
   
}
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
    
    let regItems = document.getElementById("regMenu").children;
    
    for (let re = 0; re < regItems.length; re++){
        regItems[re].setAttribute("onclick", "setReg(this)")
        
    }
 
    $("#render").click(function() {
        if(xAxisTag.length != 0 && DataManager.getActive().length != 0){
            createChart(xAxisTag, DataManager.getActive(), {regression: true})
            
        }
        else{
            raiseAlert({msg: 'Please make sure you have a tag selected for both X and Y!', type:'warning', icon: "icon-simple-remove"})
        }
        
        
        
    });
	$('#download').click(function(){ //Look into maybe just running getRawData() instead? Pretty slow though. Would just be simplier to do a filter or subset but var data sucks and is complicated.
        let curTags = xAxisTag.concat(DataManager.getActive())
        let objToString  = (big) => {
            let aggregate = ''
            for(let key of Object.keys(big)){
                aggregate += key + " - " + big[key] + " | "
            }
            return aggregate
        }
        let str = objToString(regressionResults['string'])
        let r2 = objToString(regressionResults['r2'])
        if (globalData != undefined && curTags.every(t => Object.keys(globalData[0]).includes(t))){
            DataManager.dataToCSV(curTags, "" + str + ", R2: " + r2)
        }else{
            DataManager.downloadCSV(curTags, "" + str + ", R2: " + r2)   
        }
        
	})
    
});

/* Handles when a tag name starts being hovered over the chart area */
function cardDragOver(e) {
    e.preventDefault();
    this.classList.add('over');
}

/* Handles when a tag name is no longer being hovered over the chart area */
function cardDragLeave(e) {
    this.classList.remove('over');
}

/* Handles when the tag name is actually dropped (i.e. let go when hovering over the chart area) */


/* Initially called upon page load. Where the magic begins. */
function preloadTags() {
     $.ajax({
        url:"getloads",
        type: "POST",
        async: true,
        data: { "csrfmiddlewaretoken": csrftoken, },
        success:function(data){
            try{
                var data = JSON.parse(data);
                //console.log('getLoads:' + data);

                let keys = Object.keys(data);
                let times = data['times'];
                keys.splice(keys.indexOf('times'),1)                
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
                    xAxisTag.push(key)
                    tagLabels.push(key);
                    tagActive.push(key);
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
                    div.setAttribute("onclick", "DataManager.toggleTag(this);;")
                    div.setAttribute('style','opacity:1')
                    div.innerHTML = `<span class="colorLabel" style="background:${c};"></span>`;
                    div.innerHTML += `<p>${key} - ${data[key][2]}<br>  ${data[key][3]} </p>`;
                    
                    document.getElementById("tagNav").appendChild(div);
                    
                    
                    let x = document.createElement("div");
                    x.setAttribute("class", "hierarchy items-body-content tagFilters")
                    x.setAttribute("id", key)
                    x.setAttribute("onclick", "setXAxis(this);;")
                    x.setAttribute('style','opacity:1')
                    x.innerHTML = `<span class="colorLabel" style="background:${c};"></span>`;
                    x.innerHTML += `<p>${key} - ${data[key][2]}<br>  ${data[key][3]} </p>`;
                    
                    document.getElementById("xAxisBody").appendChild(x);
                    
                    /*
                    if using this remember ot substring7 to get rid of selectX from id
                    let x = document.createElement("a");
                    x.setAttribute("class", "dropdown-item")
                    x.setAttribute("id",  "selectX"+key )
                    x.setAttribute("onclick", "setXAxis(this)")
                    x.innerHTML = key;
                    document.getElementById("xAxisMenu").appendChild(x);
                    */
                });
            }catch(err){
                console.log(err);
            }
            finally{
                document.getElementById("stopRightThere").remove()
            }
          
			
        }


    });
        
}
    
