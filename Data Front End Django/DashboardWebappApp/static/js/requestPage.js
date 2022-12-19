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
function preloadTags() {
    $.ajax({
        url:"requestRequests",
        type: "POST",
        async: true,
        data: { "csrfmiddlewaretoken": csrftoken, },
        success:function(data){
            var data = JSON.parse(data);
            console.log('Request Requests:' + data);
            if(data != undefined){
                let keys = Object.keys(data[0]);
                keys.shift() //theres some weird _state thing that we can jsut ignore 
                keys.pop() //we don't need to display pripirty
                console.log(keys)
                let table = document.getElementById('requestTable')
                //Make row for each request
                for (let req of data){
                    let row = document.createElement('tr')
                    row.id = req.tagName
                    //Adding each cell to row
                    for( let k of keys){
                        let cell = document.createElement('td')
                        cell.className = "text-center"
                        cell.innerHTML = req[k]
                        row.append(cell)
                    }
                    table.append(row)

                }
            }
            
            document.getElementById("stopRightThere").remove()
          
          
			
        }
    });
	

	
	
	
}
function makeRequest(){
    var requestTag = document.getElementById('tagInput').value
    console.log('Request for ' + requestTag)
    if(requestTag != ''){
        $.ajax({
        url:"newRequest",
        type: "POST",
        async: true,
        data: { "csrfmiddlewaretoken": csrftoken, 'tagName': requestTag, 'time': new Date().toISOString().substring(0,10)},
        success:function(msg){
            
            
          
            
            if(msg == 'Update Request'){
                $.notify({
                    icon: "tim-icons icon-alert-circle-exc",
                    message: "Tag has already been requested. We will update its priority"

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

            
            let row = document.createElement('tr')
            //tag name
            row.id = requestTag
            let cell = document.createElement('td')
            cell.className = "text-center"
            cell.innerHTML = requestTag
            row.append(cell)
            //last request and request creation date
            cell = document.createElement('td')
            cell.innerHTML = new Date().toISOString().substring(0,10)
            cell.className = "text-center"
            row.append(cell)
            cell = document.createElement('td')
            cell.innerHTML = new Date().toISOString().substring(0,10)
            cell.className = "text-center"
            row.append(cell)
            // null
            cell = document.createElement('td')
            cell.className = "text-center"
            cell.innerHTML = ''
            row.append(cell)
            document.getElementById('requestTable').prepend(row)
            }
            });
        
        
        
        
        
    }
    else{
        $.notify({
        	icon: "tim-icons icon-alert-circle-exc",
        	message: "Input a valid tag name"

        },{
            type: 'warning',
            timer: 300,
            placement: {
                from: "top",
                align: "center"
            }
        });
        
    }
    
    
}
