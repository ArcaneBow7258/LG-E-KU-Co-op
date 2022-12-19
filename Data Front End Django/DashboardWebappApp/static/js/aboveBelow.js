
var setOption= (obj) => {
    obj.parentElement.parentElement.children[0].innerHTML= obj.innerHTML

    }
var setTag = (obj) => { // maybe can move it into above?
     obj.parentElement.parentElement.children[0].innerHTML= obj.getAttribute('id').substring(6)


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
    
 
    $("#render").click(function() {
       
        let filters = []
        let tableBody = document.getElementById('filtersTable').children[0]
        for(let row of [].slice.call(tableBody.children)){
            if(row.children.length < 3){ //checking for the last row to skip data collection
                break;
            }
            else{ //else go through each column and extract its information. but need to go through td first
                let potentialData = {} //we will add to this but need to veriy if our filter is set up properly.
                for (let td of  [].slice.call(row.children)){ //we at the td level
                    let c = td.children[0]
                    if(c.className.includes('group')) // moveo ff group if at group
                       c = c.children[0]
                    if(c.innerHTML != 'Filter By' && c.innerHTML != 'Using' && c.className.includes('btn')){ //extracting data if it is a button
                       potentialData[c.id] = c.innerHTML
                    }
                    else if(c.nodeName == 'INPUT' && c.value != ''){   
                       potentialData[c.id] = c.value
                    }else{ //we have an empty input
                        break;
                    }
                    
                }
                filters.push(potentialData)
            }
            
        }
        
        createChart(['time'], DataManager.getActive(), {filters:filters, stats:'coggers'}).then(function(stats){
            console.log(stats)
            console.log('where am i')
            let body = document.getElementById('statsBody')
            //removing past stats
            while(body.childElementCount != 0)
                body.children[0].remove()
            for(let t of Object.keys(stats)){
                let max = stats[t].max + ' @ ' +stats[t].maxDate
                let min = stats[t].min  + ' @ ' +stats[t].minDate
                let mean = stats[t].mean
                let tr =  document.createElement('tr')
                let td = document.createElement('td').appendChild(document.createElement('p'))
                td.id = t + 'Tag'
                td.innerHTML = t
                tr.append(td.parentElement)
                td = document.createElement('td').appendChild(document.createElement('p'))
                td.id = t + 'Max'
                td.innerHTML = max
                tr.append(td.parentElement)
                td = document.createElement('td').appendChild(document.createElement('p'))
                td.id = t + 'Min'
                td.innerHTML = min
                tr.append(td.parentElement)
                td = document.createElement('td').appendChild(document.createElement('p'))
                td.id = t + 'Mean'
                td.innerHTML = mean
                tr.append(td.parentElement)
                body.append(tr)
                
            }
        })
    });
	$('#download').click(function(){ //Look into maybe just running getRawData() instead? Pretty slow though. Would just be simplier to do a filter or subset but var data sucks and is complicated.
        let l = []
        l = l.concat(DataManager.getActive())
        let filters = []
        let tableBody = document.getElementById('filtersTable').children[0]
        for(let row of [].slice.call(tableBody.children)){
            if(row.children.length < 3){ //checking for the last row to skip data collection
                break;
            }
            else{ //else go through each column and extract its information. but need to go through td first
                let potentialData = {} //we will add to this but need to veriy if our filter is set up properly.
                for (let td of  [].slice.call(row.children)){ //we at the td level
                    let c = td.children[0]
                    if(c.className.includes('group')) // moveo ff group if at group
                       c = c.children[0]
                    if(c.innerHTML != 'Filter By' && c.innerHTML != 'Using' && c.className.includes('btn')){ //extracting data if it is a button
                       potentialData[c.id] = c.innerHTML
                    }
                    else if(c.nodeName == 'INPUT' && c.value != ''){   
                       potentialData[c.id] = c.value
                    }else{ //we have an empty input
                        break;
                    }
                    
                }
                filters.push(potentialData)
            }
            
        }
        if (filters != undefined){
            for (let f of filters){
                if(l.indexOf(f.tag) == -1){
                    l.push(f.tag)
                }
            }


        }
        let info = ''
        for (let t of DataManager.getActive()){
            info += "TAG: " + t + ','
            info += "MAX: " + document.getElementById(t + 'Max').innerHTML + ','
            info += "MIN: " + document.getElementById(t + 'Min').innerHTML + ','
            info += "MEAN: " + document.getElementById(t + 'Mean').innerHTML  + ','
        }
        //console.log(info)
        if (globalData != undefined && l.every(t => Object.keys(globalData[0]).includes(t))){
            DataManager.dataToCSV(l, info)
        }else{
            DataManager.downloadCSV(l, info)   
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
                    div.setAttribute('style','opacity:1')
                    div.setAttribute("onclick", "DataManager.toggleTag(this)")
                    div.innerHTML = `<span class="colorLabel" style="background:${c};"></span>`;
                    div.innerHTML += `<p>${key} - ${data[key][2]}<br>  ${data[key][3]} </p>`;
                    document.getElementById("tagNav").appendChild(div);

            

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
    
function createFilter(add){
    try{
        let tableBody = document.getElementById("filtersTable").children[0]
        let filterRow = document.createElement('tr')
        filterRow.id = 'filterRow' + [].slice.call(tableBody.children).filter(r => r.id.includes('filterRow')).length
        //i have duplicate id's but only used so i can label things later :]
        //
        let gFilterSelect = document.createElement('td').appendChild(document.createElement('div'))
        gFilterSelect.setAttribute('class', 'btn-group dropdown')
        let filterSelect = document.createElement('td').appendChild(document.createElement('button'))
        filterSelect.id = 'tag'
        filterSelect.setAttribute('class',"btn btn-info dropdown-toggle btn-sm")
        filterSelect.setAttribute('data-toggle',"dropdown")
        filterSelect.innerHTML = 'Filter By'
        let dropSelect = document.createElement('div')
        dropSelect.setAttribute('class','dropdown-menu')
        
        for (let l of DataManager.getLabels()){
            let x = document.createElement("a");
            x.setAttribute("class", "dropdown-item")
            x.setAttribute("onclick", "this.parentElement.parentElement.children[0].innerHTML = this.innerHTML")
            x.innerHTML = l;
            dropSelect.appendChild(x);

        }
        let gFilterType = document.createElement('td').appendChild(gFilterSelect.cloneNode())
        gFilterSelect.append(filterSelect, dropSelect)
        //
        let filterType = (document.createElement('button'))
        filterType.id = 'type'
        filterType.setAttribute('class',"btn btn-info dropdown-toggle btn-sm")
        filterType.setAttribute('data-toggle',"dropdown")
        filterType.innerHTML = 'Using'
        let filterOptions = ['Above','Below','Status']
        let optSelect =  document.createElement('div')
        optSelect.setAttribute('class','dropdown-menu')
        for (let l of filterOptions){
            let item = document.createElement('a')
            item.setAttribute("class", "dropdown-item")
            item.setAttribute("onclick", "this.parentElement.parentElement.children[0].innerHTML = this.innerHTML")
            item.innerHTML = l;
            optSelect.appendChild(item);
            
        }
        
        gFilterType.append(filterType, optSelect)
        //
        let filterValue = document.createElement('td').appendChild(document.createElement('input'))
        filterValue.setAttribute('class',"form-control")
        filterValue.id = 'value'
        //
        let filterRemove = document.createElement('td').appendChild(document.createElement('button'))
        let icon = document.createElement('i')
        filterRemove.className = "btn btn-danger btn-sm btn-icon"
        filterRemove.setAttribute("onclick", "removeFilter(this);") 
        icon.className = "tim-icons icon-simple-remove"
        filterRemove.appendChild(icon)
        //


        filterRow.appendChild(gFilterSelect.parentElement)
        filterRow.appendChild(gFilterType.parentElement)
        filterRow.appendChild(filterValue.parentElement)
        filterRow.appendChild(filterRemove.parentElement)


        let addRow = add.cloneNode(true)
        //Adding a row and a copy of add to the bottom
        //replacing the original add row with a filterRow 
        tableBody.appendChild(addRow)
        //add.remove()
        add.replaceWith(filterRow)
    }
    catch (e)
    {
        raiseError({msg : 'Something went wrong creating a filter row! ' + e})
    }
    
}
function removeFilter(removeButton){
    //we want to remove that row and then shift the id's of every row back up to compensate.
    removeButton.parentElement.parentElement.remove()
    let tableBody = document.getElementById("filtersTable").children[0]
    let filters = [].slice.call(tableBody.children).filter(r => r.id.includes('filterRow'))
    for (let l in filters){
        filters[l].id = 'filterRow' + (l)
    }

    
    
    
}

                                         
