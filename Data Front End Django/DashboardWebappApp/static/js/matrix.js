
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
        console.log("Expanding Time Range");
        globalMinimumTime = new Date($("#global-min")[0].value).toISOString().split('.')[0];
        globalMaximumTime = new Date($("#global-max")[0].value).toISOString().split('.')[0];
        createMatrix();
        
        
    });
	$('#download').click(function(){ //Look into maybe just running getRawData() instead? Pretty slow though. Would just be simplier to do a filter or subset but var data sucks and is complicated.
        let curTags = DataManager.getActive()
        if (globalData != undefined && curTags.every(t => Object.keys(globalData[0]).includes(t))){
            DataManager.dataToCSV(curTags)
        }else{
            DataManager.downloadCSV(curTags)   
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
//Depreciated?
function cardDrop(e) {
    e.preventDefault();
    this.classList.remove('over');
    let tagName = e.dataTransfer.getData('transferredData');
    let plantName = window.location.pathname.substr(1);

    if (DataManager.checkIfTagExists(tagName)) {
        $.notify({
        	icon: "tim-icons icon-alert-circle-exc",
        	message: "This tag has already been added."

        },{
            type: 'danger',
            timer: 500,
            placement: {
                from: "top",
                align: "center"
            }
        });
        return;
    }
	debugger;
	//set plantName based on tag name
    if(tagName.toLowerCase().includes("brown"))
        plantName = "brown";
    else if(tagName.toLowerCase().includes("cane"))
        plantName = "canerun";
    else if(tagName.toLowerCase().includes("ghent"))
        plantName = "ghent";
    else if(tagName.toLowerCase().includes("mill"))
        plantName = "millcreek";
    else if(tagName.toLowerCase().includes("trimble"))
        plantName = "trimble";
    else 
        plantName = "";
    //TODO: handle the fleet plant tag (the new tag that hasnt been added yet)
    DataManager.addTag(plantName, tagName);
	$.ajax({
        url:"tagGetCol",
        type: "POST",
        data: { "csrfmiddlewaretoken": csrftoken, "column": 'engunits', "plant": plantName, "tag": tagName},
        success:function(data){
            var data = JSON.parse(data);
			engunits = data['engunits'];
            console.log(data);

            let c;
            if(tagColor[yAxisTag] == undefined){
                tagColor[tagName] = color.pop();
                c = tagColor[tagName];
                 
            }else{
                c = d3.color(tagColor[tagName])
                }
            
            let div = document.createElement("div");
			div.setAttribute("class", "hierarchy items-body-content tagFilters")
			div.setAttribute("id", tagName)
			div.setAttribute("onclick", "removeTag(this);")
            div.setAttribute('style','opacity:.3')
			var nextIndex = tagLabels.length;
			div.innerHTML = `<span class="colorLabel" style="background:${c};"></span>`;
			div.innerHTML += `<p>${tagName} - ${engunits}</p>`;
			document.getElementById("tagNav").appendChild(div);
            //

                
            }
	});
 
    
	
	/*
	if you want a legend somewhere else: although css is bad and you need to create a div in .html
	let leg = document.createElement("div");
    leg.setAttribute("class", "hierarchy items-body-content tagFilters")
    leg.setAttribute("id", key + "EU")
    leg.setAttribute("onclick", "removeTag(this);")
    leg.innerHTML = `<span class="colorLabel" style="background:${d3.schemeSet2[index]};"></span>`;
    leg.innerHTML += `<i class="far fa-times"></i> ${key} - ${data['engUnits']}`;
    document.getElementById("legend").appendChild(leg);
				*/
	
	
    
}

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
                    div.setAttribute("onclick", "DataManager.toggleTag(obj);")
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


function toggleNav(obj) {

    el1 = document.getElementById("nav1")
    el1.style.display = "none"
    el2 = document.getElementById("nav2")
    el2.style.display = "none"
    el3 = document.getElementById("nav3")
    el3.style.display = "none"
    $("#navigation").removeClass("btn-info")
    $("#filter").removeClass("btn-info")
    $("#future").removeClass("btn-info")
    
    if (obj.id == "navigation"){
      document.getElementById("nav1").style.display = "block"
      $("#navigation").addClass("btn-info")
    }
    else if (obj.id =="filter"){
      document.getElementById("nav2").style.display = "block"
      $("#filter").addClass("btn-info")
      
    }
    else if (obj.id =="future"){
      document.getElementById("nav3").style.display = "block"
      $("#future").addClass("btn-info")
    }
}
