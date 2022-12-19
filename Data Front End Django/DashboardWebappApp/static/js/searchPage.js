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
//Init
window.onbeforeunload = function() {DataManager.persistTags(false)}
$(function() {    
    $("#searchButton").click(function(){
      search();
    })
    
    
    $("#updateGlobalTime").click(function() {
        console.log("Expanding Time Range");
        DataManager.updateDates()
        $.notify({
        	icon: "tim-icons icon-calendar-60",
        	message: "Time Frame set to " + globalMinimumTime + " - " + globalMaximumTime

        },{
            type: 'success',
            timer: 1000,
            placement: {
                from: "top",
                align: "center"
            }
        });
    });
    
    $('#download').click(function(){
        let s = performance.now();


        let labels = tagLabels;
        
        let stop = document.createElement("div");
        stop.setAttribute("style", "background-color: rgba(200,200,200,0.3); width: 100%; height: 150%; position: absolute; z-index: 10")
        stop.setAttribute("id", "stopRightThere")
        document.getElementById('page-top').prepend(stop)
        console.log("CSV FOR " + labels)
        console.log(globalMinimumTime.toISOString() + " - " + globalMaximumTime.toISOString())

        //idk what d3.merge is doin but it doin it worng - ALvin. It appending the data to each other but not combining by date which is ... less than ideal...
        //data = d3.merge(combinedData);
        $.notify({
        	icon: "tim-icons icon-cloud-download-93",
        	message: "Downloading data..."

        },{
            type: 'warning',
            timer: 300,
            placement: {
                from: "top",
                align: "center"
            }
        });
        if(downloadCheck(labels)){
            console.log('big')
            labels.forEach(function (label) { //labels are the tags
            DataManager.downloadCSV(label).then((t) => {
                document.getElementById("stopRightThere").remove()
                $.notify({
                    icon: "tim-icons icon-check-2",
                    message: "Check your downloads folder for your csv's"

                },{
                    type: 'success',
                    timer: 500,
                    placement: {
                        from: "top",
                        align: "center"
                    }
                });
                let e = performance.now();
                console.log("CSV Generation:" + (e - s));
                });
            });
        }
        else{
            labels = labels.join(';;')
            DataManager.downloadCSV(labels).then((t) => {
                console.log('done small')
                document.getElementById("stopRightThere").remove()
                $.notify({
                    icon: "tim-icons icon-check-2",
                    message: "Check your downloads folder for your csv's"

                },{
                    type: 'success',
                    timer: 500,
                    placement: {
                        from: "top",
                        align: "center"
                    }
                });
                let e = performance.now();
                console.log("CSV Generation:" + (e - s));
            })

        }
        
        
    })//Download
})//Funtion
    
function saveSet(){
    let filePath = $("#setPath").val()
    let name = $("#setName").val()
    if (filePath == undefined || name == undefined){
        $.notify({
            icon: "tim-icons icon-single-02",
            message: "Please fill both fields"

        },{
            type: 'warning',
            timer: 200,
            placement: {
                from: "top",
                align: "center"
            }
        });
        return
        
        }
    var min, max
     try{//Checking if we can get a time from our input box
        let dates= DataManager.updateDates(true) 
        min = dates[0]
        max = dates[1]
    }catch(err){ //Normally we would output but
         $.notify({
            icon: "tim-icons icon-calendar-60",
            message: "Please set a date range."

        },{
            type: 'danger',
            timer: 200,
            placement: {
                from: "top",
                align: "center"
            }
        });
    }finally{
        let now = new Date()
        now = new Date(now.setHours(now.getHours() - 4)).toISOString().split('.')[0].replace('T', ' ')
        $.ajax({
                url:"saveTagSet",
                type: "POST",
                data: { "csrfmiddlewaretoken": csrftoken, "filePath": filePath, "name": name, "tags": tagLabels.join(";;"), "plants": tagPlants.join(";;"), "minTime": min, "maxTime": max ,"lastUpdated": now},
                success:function(data){
                    $.notify({
                        icon: "tim-icons icon-single-02",
                        message: "Tags saved to account " + filePath + "/" + name

                    },{
                        type: 'success',
                        timer: 300,
                        placement: {
                            from: "top",
                            align: "center"
                        }
                    });
                    console.log("Saved <3 to "+ filePath + '/' + name)
                    DataManager.persistTags()
                },
        })
    }

}
function loadSet(element){

    let hold = element.title.split(' | ')
    console.log(hold)
    globalMinimumTime = new Date (hold[0]);
    globalMaximumTime = new Date(hold[1]);

    $('#global-min').val(globalMinimumTime.toISOString().split('.')[0])
    $('#global-max').val(globalMaximumTime.toISOString().split('.')[0])
    
    while(document.getElementById('tagNav').children.length > 0){
        removeTag(document.getElementById('tagNav').children[0])
    }
    for (l of hold[2].split(', ')){
        let fake = document.createElement('div')
        fake.id = "search" + l
        cardDrop(fake)
        
    }
    DataManager.persistTags()
    let now = new Date()
    now = new Date(now.setHours(now.getHours() - 4)).toISOString().split('.')[0].replace('T', ' ')

    $.ajax({
            url:"useTagSet",
            type: "POST",
            data: { "csrfmiddlewaretoken": csrftoken, "tags": hold[2].replaceAll(", ", ";;"), "lastUsed": now},
            success:function(data){
            
            },
    })
}    
    


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
//repurposed for function as a click add
function cardDrop(e) {

    let tagName = e.id.substring(6); //remove the 'search' fomr searchTag
    
    let plantName = window.location.pathname.substr(1);
    

    if (DataManager.checkIfTagExists(tagName)) {
        $.notify({
        	icon: "tim-icons icon-alert-circle-exc",
        	message: "This tag has already been added."

        },{
            type: 'danger',
            timer: 300,
            placement: {
                from: "top",
                align: "center"
            }
        });
        return;
    }
	
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
        async: true,
        data: { "csrfmiddlewaretoken": csrftoken, "plant": plantName, "tag": tagName},
        success:function(data){
            var data = JSON.parse(data);
			engUnits = data['engUnits'];
            descriptor = data['descriptor'];
            let c;
            if(tagColor[tagName] == undefined){
                tagColor[tagName] = color.pop();
                c = tagColor[tagName];
                 
            }else{
                c = d3.color(tagColor[tagName])
                }
            
            let div = document.createElement("div");
			div.setAttribute("class", "hierarchy items-body-content tagFilters")
			div.setAttribute("id", tagName)
			div.setAttribute("onclick", "removeTag(this);")
			var nextIndex = tagLabels.length;
			div.innerHTML = `<span class="colorLabel" style="background:${c};"></span>`;
			div.innerHTML += `<p>${tagName} - ${engUnits} <br> ${descriptor}</p>`;
			document.getElementById("tagNav").appendChild(div);
            //
            
            }
	});/*
    $.notify({
        icon: "tim-icons icon-cloud-upload-94",
        message: "Tag added!."

    },{
        type: 'success',
        timer: 500,
        placement: {
            from: "top",
            align: "center"
        }
    });
	
	
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
                raiseAlert({icon:"icon-simple-remove", msg: err, type:"danger"})
                console.log(err)
            }
            finally{
                $.ajax({
                url:"getTagSet",
                type: "POST",
                async: true,
                data: { "csrfmiddlewaretoken": csrftoken, },
                success:function(tagSets){
                    tagSets = JSON.parse(tagSets);
                    console.log(tagSets)
                    //Creating this horrendous tree thing
                    //We sort to make sure we fill out the top level first
                    //Maybe add the filepath name to end of length to also srot by filepath secondary lol
                    tagSets.sort(s => s.filePath.split('/').length)
                    for(set of tagSets){
                        //Procedurally go through our path, creating a new div if it doesn't exist.
                        let paths = (set.filePath).split('/')
                        //console.log(paths)
                        //Some info about collapsable:
                        //requeires a button div, and a "card/holder" div.
                        //We are using the collapsable div to run through other collapsable
                        
                        let tab = document.getElementById('accordionBody')  //should be same as currentTop until currentTOp finds a deeper level to go down.
                        let currentTab = tab //our pointer to point where we "should go"
                        let bowl
                        //creating/looking gor filepath goiong down
                        let fullPath = ''
                        let index = 0 //depreciated
                        while(paths[0] != '' && paths.length > 0){
                            let searchFile = paths.shift()
                            fullPath += searchFile
                            //console.log(fullPath)
                            //searching through body
                            for (div of tab.children){
                                if(div.id == fullPath + 'Body'){
                                    currentTab = div
                                    break;
                                }  
                            }
                            if (currentTab == tab){ //Case when we did not find any mathcing children to path   
                                //we creatue our drop down and then body
                                
                                //might nest this within another div as well.
                                //Name plate button thing
                                let wow = document.createElement('a')
                                wow.setAttribute('data-toggle',  'collapse')
                                wow.setAttribute('href', "#" + fullPath + 'Body')
                                wow.setAttribute('aria-expanded',"false")
                                wow.setAttribute('aria-controls',fullPath)
                                wow.setAttribute('class','card collapsed')
                                wow.setAttribute('style', 'z-index:'+index+'px')
                                wow.role = 'tab'
                                wow.id = fullPath
                                wow.innerHTML = searchFile //+ `<i class="tim-icons icon-minimal-down"></i>`
                                tab.append(wow)
                                index++
                                //let no = document.createElement('br')
                                //bod.append(no)
                                
                                //actualy holder that collapses
                                bowl = document.createElement('div')
                                bowl.id = fullPath + 'Body'
                                bowl.role = 'tabpanel'
                                bowl.setAttribute('class','card-body collapse')
                                bowl.setAttribute('style', 'z-index:'+index)
                                index++
                                tab.append(bowl)
                                currentTab = bowl
                                tab = bowl
                            }
                            else{//We found a child, go down and reset
                                tab = currentTab
                            }
                            
                        }
                        //add a lonk
                        let rice = document.createElement('button')
                        rice.role = 'lonk'
                        rice.setAttribute('class','btn btn-small')
                        rice.setAttribute('onClick','loadSet(this)')
                        rice.id = fullPath + set.name
                        rice.innerHTML = set.name 
                        rice.title=set.minTime + " | "+  set.maxTime + " | " + set.tags.replaceAll(';;', ', ')
                        index++
                        tab.append(rice)
                        
                        
                        
                        
                        
                    }
                    
                    }
                })
                document.getElementById("stopRightThere").remove()
            }
          
			
        }
    });
	

	
	
	
}

function removeTag(obj) {
    console.log('Clicked: Deleted');
    obj.remove();
	//console.log(obj.getAttribute("id") + "EU")
	//document.getElementById(obj.getAttribute("id") + "EU").remove()
	//above is for if the legend was not included in the tag
    DataManager.removeTag(obj.id);

}

function search(){
    $.notify({
        	icon: "tim-icons icon-paper",
        	message: "Searching the database..."

        },{
            type: 'warning',
            timer: 300,
            placement: {
                from: "top",
                align: "center"
            }
        });
    var searchValue = ''
    //Again I'm really annoyed. You could definelty do a for loop to go through all <input> with class of check but you know here I am har coding it
    var reqValue = $('#requireCheck').is(":checked")
    let join = (reqValue) ? "" : "----" //When we do &, we want the empty character, but if we do |, we don't want duplicates with how we are doing it. 
    for (let s of document.getElementsByClassName('form-control mr-sm-12')){
        //Right now I am just making empty space so I specificly search by what is inputted.
        //If any of the paremeters are hit, we return that row (WHERE on parameter, JOIN each result)
       let add = (($('#' + s.id)).val() != '') ? ($('#' + s.id)).val() : join
        add =  ";;" + add
        searchValue = searchValue.concat(add); 

    }
    searchValue.replace("Input", "")//Taking out the "input". personal preference
    searchValue = searchValue.substring(2) // removing leading comma
    //Drop Box Code
    if(!(searchValue.toLowerCase().includes('brown') ||searchValue.toLowerCase().includes('canerun') || searchValue.toLowerCase().includes('ghent') || searchValue.toLowerCase().includes('trimble') || searchValue.toLowerCase().includes('millcreek')) ){
        searchValue = document.getElementById("plantSelect").value + '.' + document.getElementById("unitSelect").value + '.' + searchValue}
    console.log(searchValue);
    //Life sucks, fsrftoken messing me up - Alvin
    //I am going to have to pass an ugly string.
    $.ajax({
        url:"advancedSearch",
        type: "POST",
        data: { "csrfmiddlewaretoken": csrftoken, "searchParameters": searchValue, "require": reqValue},
        success:function(data){
            //Get Data
            var data = JSON.parse(data);
            console.log(data);
            //Removin gexisting table values
            //Charts were buggy so i'm just doing the while just in case
            let table = document.getElementById('tableBody')
            while(table.children.length > 0){
                for (let c of table.children){
                    c.remove();
                }
            }
           
            let keys = Object.keys(data);
            
            keys.forEach(function(key){
                let row = document.createElement("tr")
                row.id = "search" + key
                //row.className = (keys.indexOf(key) % 2 == 1) ? 'table-info' : ''
                for( let c in data[key]){
                    if(c != 1){ //We don't want to get TAG_ID outputting, just able to be serached for us
                        
                        let col = document.createElement("td")
                        col.className = "text-center"
                        col.innerHTML = data[key][c]
                        row.append(col)
                    }
                }
                //let att = document.createElement('td')
                //att.innerHTML = "Placeholder"
                //row.append(att)
                let action = document.createElement("td")
                let addButton = document.createElement("button")
                let icon = document.createElement('i')
                addButton.className = "btn btn-success btn-sm btn-icon"
                addButton.setAttribute("onclick", "cardDrop(this.parentElement.parentElement);") 
                
                icon.className = "tim-icons icon-simple-add"
                
                //parent is td, parent of that is row
                addButton.append(icon)
                action.append(addButton)
                row.append(action)
                table.append(row)
           
            
                
            })//for each
            $.notify({
                icon: "tim-icons icon-paper",
                message: "Table assembled!"

            },{
                type: 'success',
                timer: 300,
                placement: {
                    from: "top",
                    align: "center"
                }
            });
            
        }//succ
    });//ajax
    
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
