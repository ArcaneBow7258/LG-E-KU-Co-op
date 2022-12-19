//Tag Variables
var tagLabels = []; /* Keeps track of the tag names that are loaded */
var tagPlants = []; /* Keeps track of the plants of the respective tag names that are loaded */
var tagEng = [];
var tagDesc = [] /*man i have to keep tract of Description too */

var tagActive = []/* Keeps track of tags that hould be loaded | Also acts as yAxisTags*/
var xAxisTag = [] //For Regression
var regressionType = 'Lin'; //For Regression
var regressionResults = {points: {}, equation: {}, r2: {}, string: {}, predict: {}}; /*For export*/

/*var color;  Global variable so all of the functions can access it and keep the same color for different charts */
/*repurposed for consistent color when removing and adding tags*/
var color = ["#ff4040","#e19608","#96e108","#40ff40","#08e196","#0896e1","#4040ff","#9608e1","#e10896","#ff4040"].concat(d3.schemeSet1.concat(d3.schemeCategory10))
var tagColor = {}; /*Assign each tag to a color*/



//Variables for various chartJS
var globalData /*Pulled Data | Contains data that is unchanged */
var data /*data pertaining to the chart itself; active tags, scaling, time range, etc*/



//Set Initial Time
var globalMaximumTime = new Date().toISOString().split('.')[0];
var globalMinimumTime = new Date(new Date().getFullYear(),new Date().getMonth(),new Date().getDate()-7).toISOString().split('.')[0];
function raiseAlert({icon, msg, type = "success", timer = 200, from = "top", align = "center"} = {}){
     $.notify({
                icon: "tim-icons " + icon,
                message: msg

            },{
                type: type,
                timer: timer,
                placement: {
                    from: from,
                    align: align
                }
            });
    
}
function raiseError({code = 0, msg = ''}={}){
    let errorCard = document.createElement('div')
    errorCard.setAttribute("class", "card")
    errorCard.style = "margin-left:27vw; margin-top:26vh; width:46vw; height:23vh; position:absolute; z-index:100"
    
    let errorText = document.createElement('div')
    errorText.setAttribute("class","card-body text-danger")
    errorText.innerHTML = "Bing Bong the PDW has recieved the error of <br>\"" + msg + "\"<br>Please email a screenshot of this and details leading up this error.<br>You may refresh to website to retry."
    errorCard.append(errorText)
    document.getElementsByClassName('wrapper')[0].prepend(errorCard)
       //<div class="card" style="margin-left:27vw; width:46vw; height:46vh; position:absolute; "> </div>

}
function smallerDateCheck(tagArray){ //Checks if our new date range is already inside, if so we don;t ahve to requery data
    //console.log(new Date(globalMinimumTime))
    //console.log(new Date($("#global-min")[0].value))
    
    //Checking if we need to requery data
    try{
        if(globalData != undefined && globalData != []){
            //DataManager.updateDates()
            let timeDelta = new Date(globalData[1].time) - new Date(globalData[0].time)
            let timeDict = { 60000 : '1m',
                             3600000: '1h',
                             86400000: ' 1d',
                             604800000: '1w',
                             2592000000: '1mo'
                           }
            if(timeDict[timeDelta] != document.getElementById('timeInterval').value){
                return false
        }
            //let extent = d3.extent(globalData, r => new Date(r.time))
            if( globalMinimumTime <= new Date($("#global-min")[0].value)  && new Date($("#global-max")[0].value) <= globalMaximumTime ){
                for (t of tagArray){ //check if we have all the labels as well
                    if(!Object.keys(data[0]).includes(t)) { DataManager.updateDates(); return false }
                }
                //In the case we do have a smaller dataset, we don't need to change globalTime.
                //We change global time when we have to requery the data. 
                return true
            }
            DataManager.updateDates()
            return false
        }
        else{
            DataManager.updateDates()
            return false
        } 
    }catch (e)
    {
        raiseError({msg:'Error within date check! ' + e})
    }
}
function downloadCheck(tagArray){
    DataManager.updateDates()
    let rowCount = tagArray.length * (new Date(globalMaximumTime) - new Date(globalMinimumTime)) 
    if(globalData != undefined && globalData != []){
        let timeDelta = new Date(globalData[1].time) - new Date(globalData[0].time)
        //Our rout count already devides out by 60000 
        rowCount = rowCount/timeDelta
    }
    else {
        rowCount = rowCount / 60000
    }
    console.log("Row Count Stacked: " + rowCount)
    let tooBig = (rowCount > 300000)
        
    if (tooBig){
        $.notify({
        	icon: "tim-icons icon-cloud-download-93",
        	message: "The amount of data you want to download exceeds 300000 points. We will split your data into individual csv's."

        },{
            type: 'danger',
            timer: 300,
            placement: {
                from: "top",
                align: "center"
            }
        });
    }
    
    return tooBig
}
// (year, months from January, day, time)
class DataManager {
    //All below functions that Load have asynci off to ensure we do not move ahead before loading.
    
    //Saves tag to session
    static persistTags(async = true){
        var min, max
        try{//Checking if we can get a time from our input box
            let dates= DataManager.updateDates(true) 
            min = dates[0]
            max = dates[1]
        }catch(err){/* //Normally we would output but
             $.notify({
                icon: "tim-icons icon-calendar-60",
                message: "Please set a date range."

            },{
                type: 'danger',
                timer: 1000,
                placement: {
                    from: "top",
                    align: "center"
                }
            });*/
        }finally{
            $.ajax({
                url:"persistTags",
                type: "POST",
                asyc: async,
                data: { "csrfmiddlewaretoken": csrftoken, "tags": tagLabels.join(";;"), "plants": tagPlants.join(";;"), "minTime": min, "maxTime": max},
                success:function(data){

                    console.log("Saved <3")
                },
                error: function(err) {
                }
            });
   
        }  
    }
    //Gets session tags
    static sessionTags(){
        function ajaxCall() {
            return new Promise(function(resolve, reject) {
                $.ajax({
                    url:"sessionTags",
                    type: "POST",
                    async: false,
                    data: { "csrfmiddlewaretoken": csrftoken },
                    success:function(data){
                        console.log(data)
                        data = JSON.parse(data)
                        resolve(data);
                    },
                    error: function(err) {
                        reject(err);
                    }
                });
            });
        }

        ajaxCall().then(function(data) {
            
            tagLabels = data['tags']
            tagActive = tagLabels;
            tagPlants = data['plants']
            
            globalMinimumTime = new Date(data['minTime'].replace(' ', 'T').split('+')[0]);
            globalMaximumTime = new Date(data['maxTime'].replace(' ', 'T').split('+')[0]);
            $('#global-min').val(data['minTime'].replace(' ', 'T').split('+')[0])
            $('#global-max').val(data['maxTime'].replace(' ', 'T').split('+')[0])
            return data;
        }
    )}
    //
    static updateDates(python = false){
            if(python){
                globalMinimumTime = new Date($("#global-min")[0].value)
                globalMaximumTime = new Date($("#global-max")[0].value)
                let min = new Date(globalMinimumTime.valueOf())
                let max = new Date(globalMaximumTime.valueOf())
                //Convert time to ISO to catch for both EDT and EST, and then convert to EST for PDW extraction
                //Check charts function and its parsing to see that we push forward an hour in DST
                min = new Date(min.setHours(min.getHours() - 5)).toISOString().split('.')[0].replace('T', ' ')
                max = new Date(max.setHours(max.getHours() - 5)).toISOString().split('.')[0].replace('T', ' ')
                
                return [min, max]
            }
            else{
                globalMinimumTime = new Date($("#global-min")[0].value)
                globalMaximumTime = new Date($("#global-max")[0].value)
            }
        

    }

    static checkIfTagExists(tag) {
        return tagLabels.indexOf(tag) >= 0 ? true : false;
    }



    static addTag(plant_name, tag_name) {

        console.log(tag_name);

        // Tag already exists in the data
        if (tagLabels.indexOf(tag_name) >= 0) {
            console.log("already exists"); 
            return; 
        }

        function ajaxCall() {
            return new Promise(function(resolve, reject) { //Grabbing eng units.. Before the enw ave of ExtractPiData it was a data check
                $.ajax({
                    url:"tagGetCol",
                    type: "POST",
                    asyc: false,
                    data: { "csrfmiddlewaretoken": csrftoken, "plant": plant_name, "tag": tag_name},
                    success:function(data){
                        //debugger;
                        resolve(data);
                    },
                    error: function(err) {
                        reject(err);
                    }
                });
            });
        }

        ajaxCall().then(function(data) {
            var data = JSON.parse(data);
			var engUnits = data["engUnits"]
            var desc = data["descriptor"]
            tagLabels.push(tag_name);
            tagActive.push(tag_name);
            tagPlants.push(plant_name);
			tagEng.push(engUnits);
            tagDesc.push(desc)
           
            console.log(tagLabels);
            DataManager.persistTags();
        }).catch(function(err) {
            console.log(err);
            raiseError({msg : 'Error while adding tag: ' + err})
        });
    }
    
    /* Removes a tag from the loaded data */
    static removeTag(tag_name) {
        if (tagLabels.indexOf(tag_name) == -1) { return; } // Tag is not in the data
        
        tagPlants.splice(tagLabels.indexOf(tag_name), 1);
		tagEng.splice(tagLabels.indexOf(tag_name), 1);
        tagDesc.splice(tagLabels.indexOf(tag_name), 1);
        tagLabels.splice(tagLabels.indexOf(tag_name), 1);
        DataManager.persistTags()
     //   createLineChart();
    }
    static toggleTag(tagE){
        if (tagE.style.opacity == '0.3') {
            tagE.setAttribute('style', 'opacity: 1')
            tagE.style.opacity = '1'
            //idk why setting the styl doesn't work consistently
            tagActive.push(tagE.id)
            console.log(tagE.id + 'on')
            
            
        }
        else{
            tagE.setAttribute('style', 'opacity: 0.3')
            tagE.style.opacity = '0.3'
            tagActive.splice(tagActive.indexOf(tagE.id), 1)
            console.log(tagE.id + 'off')
            
        }
        
    }

    /* Returns the labels for the loaded tags, including time as the first element */
    static getLabels() {
        return tagLabels;
    }
    static getActive(){
        return tagActive;
    }
    static makeStop(){
        let stop = document.createElement("div");
        stop.setAttribute("style", "background-color: rgba(200,200,200,0.3); width: 100%; height: 150%; position: absolute; z-index: 10")
        stop.setAttribute("id", "stopRightThere")
        document.getElementById('page-top').prepend(stop)
    }
    static removeStop(){
        document.getElementById("stopRightThere").remove()
    }
    /* Any arguments supplied should be tag names */
    static getRawData(tag_name) {
        var plant_name = tagPlants[tagLabels.indexOf(tag_name)];
        
        //Converting to ISO makes us to gain 4 hours when setting it before; now we just keep our timezone in the FRONT END
        //Passing to python, it is timestamp naive so we do the time conversion to EST for ourselves.
        let dates = DataManager.updateDates(true)
        let min = dates[0]
        let max = dates[1]
        //console.log(`Current plant_name: ${plant_name}`);
        //tagLabels.join(';;')
        return new Promise(function(resolve, reject) {
            $.ajax({
                url:"filteredTagDataNew",
                type: "POST",
                data: { "csrfmiddlewaretoken": csrftoken, "plant": plant_name, "tag": tag_name, "minTime": min, "maxTime": max, "timeInterval": document.getElementById('timeInterval').value},
                success:function(data){
                    console.log('Raw Data')
                    //console.log(data)
                
                    resolve(data);
                    
                },
                error: function(err) {
                    console.log(err)
                    reject(err);
                    raiseError({code : 0, msg:'Extraction Failed! Our data extraction did not go smoothly'}) 
                }
            });
        });
    }
    //Predominatenly used for the search page... hopefully nothing else...
    static downloadCSV(tag_name, info = '') {
        try{
            let s = performance.now();
            let dates = DataManager.updateDates(true)
            let min = dates[0]
            let max = dates[1]
            console.log('CSV DOWNLOAD');
            let interval = document.getElementById('timeInterval').value
            if(typeof(tag_name) != 'string'){
                tag_name = tag_name.join(';;')
            }
            //tagLabels.join(';;')
            return new Promise(function(resolve, reject) {
                $.ajax({
                    url:"downloadCSV",
                    type: "POST",
                    data: { "csrfmiddlewaretoken": csrftoken, "tag": tag_name, "minTime": min, "maxTime": max, "timeInterval": interval},
                    success:function(data){
                        try{
                            console.log("did we do it?")
                            //console.log(data)
                            let infoIndex = data.indexOf('\n')  
                            //Adding additiona info depdning on where we are downloading from
                            data = data.slice(0,infoIndex) +"," + info  + data.slice(infoIndex)
                            let csvContent = "data:text/csv;charset=utf-8,"  + data;
                            var encodedUri = encodeURI(csvContent);
                            let link = document.createElement("a");
                            link.setAttribute("href", encodedUri);
                            //Creating File Name: MinDate-MaxDate+Tag1_Tag2_...
                            //mabye change to ..._Tag1_Tag2...
                            let fileName = globalMinimumTime.toISOString().substring(0, 10) + "-" + globalMaximumTime.toISOString().substring(0, 10) + '-' + interval + "+" 
                            fileName += tag_name + "_"

                            link.setAttribute("download", fileName + ".csv");
                            document.body.appendChild(link); // Required for FF

                            link.click(); // This will download the data file named "my_data.csv".
                            link.remove()
                            resolve('works')
                        }catch(err){
                            raiseError({msg: "Error occured while attempting to convertintg .csv: " + err})
                        }
                    },
                    error: function(err) {
                        reject(err);
                        
                    }
                });
            });
        }catch (e){
            raiseError({msg:"Error occured while attempting to pulling .csv: " + e})
        }
        
    }
    static dataToCSV(tagArray, info = '') {
        try{
            //Info comes in columns right after headers, must be formated |cell, cell, cell|
            console.log('CSV DOWNLOAD');
            DataManager.makeStop()
            let s = performance.now();
            //let big = downloadCheck(tagArray)
            let big = false
            //Need to find way to either A. Split downloads and B. filter globalData.
            //Or just say no go to serach page !
            raiseAlert({icon: 'icon-notes', type: 'warning', timer:'200', msg:'Generating csv...'})
            ///https://stackoverflow.com/questions/54907549/keep-only-selected-keys-in-every-object-from-array
            let wantedKeys = []
            const redux = array => array.map(o => wantedKeys.reduce((acc, curr) => {
              acc[curr] = o[curr];
              return acc;
            }, {}));
            if(big){
                for (t of tagArray){
                    keys = [t]
                    let csvContent = "data:text/csv;charset=utf-8,"  + d3.csvFormat(redux(globalData).filter(x=> new Date(x.time) > globalMinimumTime &&  globalMaximumTime > new Date(x.time) ))
                    let infoIndex = csvContent.indexOf('\n')  
                    //Adding additiona info depdning on where we are downloading from
                    csvContent = csvContent.slice(0,infoIndex) +"," + info  + csvContent.slice(infoIndex)
                    var encodedUri = encodeURI(csvContent);
                    let link = document.createElement("a");
                    link.setAttribute("href", encodedUri);
                    //Creating File Name: MinDate-MaxDate+Tag1_Tag2_...
                    //mabye change to ..._Tag1_Tag2...
                    let fileName = globalMinimumTime.toISOString().substring(0, 10) + "-" + globalMaximumTime.toISOString().substring(0, 10) + "+"
                    fileName += t

                    link.setAttribute("download", fileName + ".csv");
                    document.body.appendChild(link); // Required for FF

                    link.click(); // This will download the data file named "my_data.csv".
                    link.remove();

                }
                raiseAlert({icon :'icon-check-2', msg: "Check your downloads folder for csv's.", timer:200})
            }
            else{
                let csvContent = "data:text/csv;charset=utf-8,"  + d3.csvFormat(globalData.filter(x=> new Date(x.time) > globalMinimumTime &&  globalMaximumTime > new Date(x.time)))
                let infoIndex = csvContent.indexOf('\n')  
                //Adding additiona info depdning on where we are downloading from
                csvContent = csvContent.slice(0,infoIndex) +"," + info  + csvContent.slice(infoIndex)
                var encodedUri = encodeURI(csvContent);

                let link = document.createElement("a");
                link.setAttribute("href", encodedUri);
                //Creating File Name: MinDate-MaxDate+Tag1_Tag2_...
                //mabye change to ..._Tag1_Tag2...
                let fileName = globalMinimumTime.toISOString().substring(0, 10) + "-" + globalMaximumTime.toISOString().substring(0, 10) + "+"
                for (let l of tagArray){
                    fileName += l + "_"
                }
                link.setAttribute("download", fileName + ".csv");
                document.body.appendChild(link); // Required for FF

                link.click(); // This will download the data file named "my_data.csv".
                link.remove();
                raiseAlert({msg:"Data downloaded as:" + fileName + ".csv", timer:200, type:'success', icon:'icon-check-2'})
            }

            let e = performance.now();
            DataManager.removeStop()
            console.log("CSV Generation:" + (e - s));


        }catch(e){
        raiserError({msg:"Error occured while converting data to .csv: " + e})
    }
}
}

function round(value, decimals) {
    return Number(Math.round(value+'e'+decimals)+'e-'+decimals);
}

/* Used for creating elements and if useful if you need to chain together calls, so that you don't have a lot of redundant code. */
this.createEl = (function () {
    function _el() {
        var self = this, newElement, rootObject;
        var newElements = [];

        this.create = function (tag) {
            newElement = document.createElement(tag);
            newElements.push(newElement);
            return this;
        }

        this.append = function (tag) {
            newElement = document.createElement(tag);
            newElements.push(newElement);
            return this;
        },

        this.select = function (tag) {
            rootObject = tag;
            newElements.length = 0;
            return this;
        }

        this.selectById = function (id) {
            rootObject = document.getElementById(id);
            newElements.length = 0;
            return this;
        },

        this.selectByClass = function (cl) {
            rootObject = document.getElementsByClassName(cl);
            newElements.length = 0;
            return this;
        },

        this.subelement = function (tag) {
            newElement = document.createElement(tag);
            newElements[0].appendChild(newElement);
            return this;
        },

        this.type = function (par) {
            newElement.type = par;
            return this;
        }

        this.id = function (name) {
            newElement.id = name;
            return this;
        },

        this.className = function (name) {
            newElement.className = name;
            return this;
        },

        this.style = function (attr, val) {
            newElement.style.setProperty(attr, val);
            return this;
        },

        this.innerHTML = function (str) {
            newElement.innerHTML = str;
            return this;
        },

        this.step = function (val) {
            newElement.step = val;
            return this;
        }

        this.end = function () {
            if (rootObject != undefined) {
                newElements.forEach((el) => rootObject.appendChild(el));
            }

            return arguments[0] == "root" ? rootObject : newElement;
        }

        return this;
    }
    return new _el();
}());

