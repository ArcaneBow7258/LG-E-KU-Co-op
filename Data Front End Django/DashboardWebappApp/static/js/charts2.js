/*
Why charts 2 you may ask?
Other one is getting too big so I decided to split.
Also congregates certain types of functions, ie this is anything past 3/15 or advanced variations of items.
Moreover I feel like bigger files get laggy so I decided to split.
Also also I don't want to scroll for 3 minutes / use CTRL+F to search 1000 rows of code.
- Alvin Tran Spring 2022 Co-Op
*/
//Copied variables
var yScale; //Do these need to be const ? - avlin
var originalYScales = []; 
var xScale /*Global variable "scales" to revert normalized data back in other js files */
//xScale.invert(x0).toLocaleDateString('en-US', {year: 'numeric', month:"numeric", day:"numeric"})
/*
function controls(e){
    let key = e.code.substring(3)
    let mouseArea = document.getElementById('mouseArea')
    var x0 = (d3.pointer(event, mouseArea)[0]);
    console.log(key)
    if(key == "Q"){
        console.log(xScale.invert(x0).toLocaleDateString('en-US', {year: 'numeric', month:"numeric", day:"numeric"}))
        globalMinimumTime = new Date(xScale.invert(x0).toLocaleDateString('en-US', {year: 'numeric', month:"numeric", day:"numeric"})).toISOString().split('.')[0];
        $('#global-min').val(globalMinimumTime)
                
    }
    if(key == "E"){
        globalMaximumTime = new Date(xScale.invert(x0).toLocaleDateString('en-US', {year: 'numeric', month:"numeric", day:"numeric"})).toISOString().split('.')[0];
        $('#global-max').val(globalMaximumTime)
    }
}*/
    
/* Creates main line chart using D3FC. WebGL for the lines, Canvas for the gridlines. 
    Nested Promises are used to ensure relevant asynchronous data is loaded before moving on to the next step. */
/*Hi - Alvin */
function createAboveBelow(tagName, side, targetValue, throwCheck, filterName, filterSide, filterValue) {
    try{
        originalYScales = []; 
        console.log('Creating \'AboveBelow\' Chart');
        DataManager.makeStop()
        var startTime = performance.now();

        const labels = []
        labels.push(tagName)
        if(!(filterName == 'Filter Tag' || filterSide == 'Options' || isNaN(filterValue)) ){
            labels.push(filterName)
        }
        //Converting to T/F
        side = (side == "Above")
        $.notify({
                icon: "tim-icons icon-refresh-02",
                message: "Chart refreshing...."

            },{
                type: 'warning',
                timer: 300,
                placement: {
                    from: "top",
                    align: "center"
                }
            })
        //$('#global-min').val(globalMinimumTime)
        //$('#global-max').val(globalMaximumTime)
        const parse = (item) => {
            for (let m in item) {
                if (m == "time") item[m] = Date.parse(item[m]); else item[m] = +item[m];
            }
            return item;
        };
        var p;
        if(smallerDateCheck(labels)){
            p = new Promise(function(resolve, reject){
                console.log('Using older data')
                resolve(globalData)
            })
        }
        else{
            p = DataManager.getRawData(labels.join(';;'))
        }

        p.then(function (rawData) {
            //console.log(rawData)
            if(typeof rawData == 'string' ){
                data = d3.csvParse(rawData)
                globalData = JSON.parse(JSON.stringify(data))
                data.forEach(r => parse(r))
            }else{
                //When using older data, we want to have data within our time range.
                //If using new data,s ohuldn't affect anything
                data = JSON.parse(JSON.stringify(globalData))
                data.forEach(r => parse(r))
                data = data.filter(r => globalMinimumTime.valueOf() <= r.time && r.time <= globalMaximumTime.valueOf())
            }


            console.log('option checks')
            if(throwCheck){
                data = data.filter(row => (side ? row[tagName] > targetValue :  row[tagName] < targetValue ))
            }
            if(!(filterName == 'Filter Tag' || filterSide == 'Options' || isNaN(filterValue)) ){
                filterSide = (filterSide == "Above")
                data = data.filter(row => (filterSide ? row[filterName] > filterValue :  row[filterName] < filterValue ))
            }
            //sometimes redundant, as we already do same filter above if we throw. can be optimized with logic but i just want ti to work - alvin
            let targetCount = d3.count(data.filter(row => (side ? row[tagName] > targetValue :  row[tagName] < targetValue )), row => row.time)

            console.log(data);
            createEl.select(document.getElementById("linediv")).append("div").id("chart").end();
            $.notify({
                icon: "tim-icons icon-refresh-02",
                message: "Data loaded..."

            },{
                type: 'warning',
                timer: 200,
                placement: {
                    from: "top",
                    align: "center"
                }
            })
            var valueMax = d3.max(data, function (d) { return d[labels[0]]});
            var valueMin = d3.min(data, function (d) { return d[labels[0]]});

            //Scales are made to put Y values into 0-1 scale if we are given multuple tags. We keep the origanlYScales for each tag/label to cnvert back from 0-1 to actual values.
            //For download button purposes, i have made the scale variables global
            xScale = d3
                    .scaleTime()
                    .domain(fc.extentDate().accessors([d => d.time])(data));
            yScale = d3
                .scaleLinear()
                .domain([valueMin - (valueMax-valueMin)*.1, valueMax+ (valueMax-valueMin)*.1]);
            originalYScales.push(yScale);

            //lines are a lie this is a scatterplot >:(
            //Function to create lines; apply it to each tag
            const line =  fc.seriesWebglPoint()
                    .equals((previousData, currentData) => previousData === currentData)
                    .crossValue(d => d['time'])
                    .mainValue(d => d[labels[0]])
                    .decorate((program, data, selection) => {
                        fc.webglFillColor().value(d => {
                            let rgba;
                            if(tagColor[labels[0]] == undefined){
                                tagColor[labels[0]] = color.pop();
                                rgba = tagColor[labels[0]];

                            }else{
                                rgba = d3.color(tagColor[labels[0]])
                            }
                            return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                        }).data(data)(program);
                    });
            var lines = [line];
            //Adding Above/Below Bar
            const targetSeries = fc.seriesWebglPoint()
                .equals((previousData, currentData) => previousData === currentData)
                .crossValue(d => d['time'])
                .mainValue(d => targetValue)
                .decorate((program, data, selection) => {
                     fc.webglFillColor().value(d => {
                        const rgba = d3.color(d3.schemePaired[0]);
                        return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                        }).data(data)(program);
                    })
            lines.push(targetSeries); 

            const gridline = fc.annotationCanvasGridline();

            const series = fc
                .seriesWebglMulti()
                .xScale(xScale)
                .yScale(yScale)
                .series(lines);

            const container = document.getElementById("chart")

            const zoom = fc.zoom().on('zoom', event => {
                render(); 
            }); 


            var yLabel = (labels[0] + " - " + tagEng[tagLabels.indexOf(labels[0])])


            const chart = fc
                .chartCartesian(xScale, yScale)
                .webglPlotArea(series)
                .canvasPlotArea(gridline)
                .decorate(sel => {

                    sel.enter().call(zoom, xScale, yScale);

                }).xLabel("Date")
                .yLabel(yLabel)
                .useDevicePixelRatio(true)


            const render = () => { 
                d3.select(container)
                .datum(data)
                .call(chart);

            };

            render();

            container.setAttribute("style", "height:75vh; width:71vw;")
                const cChart = document.getElementsByClassName("cartesian-chart")[0];
                let mouseArea = document.createElement("div");
                mouseArea.setAttribute("pointer-events", "all")
                mouseArea.setAttribute("class", "plot-area");
                mouseArea.id = "mouseArea"
                mouseArea.setAttribute("style", "z-index:10");
            let focus = document.createElement("div");
                const tooltipAtt = "margin-left:1.75vw; padding: 10px; z-index: 9; position: absolute; width:12vw; margin-top: 3vh; word-wrap: break-word; white-space:normal; "
                focus.setAttribute("style", tooltipAtt+ "visibility: hidden; ");
                focus.setAttribute("class", "badge badge-default");
                focus.innerHTML = "Bread";
            cChart.append(mouseArea);
            mouseArea.append(focus);
            let bar = document.createElement("div");
            const barAtt = "margin-left:1.35vw; height: 91.5%; z-index: 8; position: absolute; width:.25vw; word-wrap: break-word; white-space:normal; background-color: rgba(225,50,50,0.5);"
            bar.id = "bar"
            bar.setAttribute("style", barAtt + "visibility: hidden; ")
            mouseArea.append(bar)
            //Maybe look at quadtree implementaiton?


            test = data;
            function mousemove(event)
            {
                var x0 = (d3.pointer(event, this)[0]);
                var y0 = (d3.pointer(event, this)[1]);
                var bisect = d3.bisector(function(d){return d.time});

                let index = bisect.center(data, xScale.invert(x0))
                let pointer = data[index] 
                x0  = (x0 < 650 ? xScale(pointer.time): xScale(pointer.time) - 240)

                var yTooltip = '';
                for (let l of labels){
                    var yAdjust = pointer[l];
                    yTooltip += l + ": " + yAdjust.toFixed(4) + "<br>";
                }
                yTooltip += (side)?"Above time: " + targetCount + " minutes": "Below time: " +targetCount + " minutes";
                focus.setAttribute("style", tooltipAtt+ "left:" + x0 +"; top: "+(y0 + 10)+ ";visibility: visible");
                focus.innerHTML = "<p class=\"card-title\" style=\"font-size:12px\">"+ new Date(pointer.time).toLocaleDateString('en-US', {year: 'numeric', month:"numeric", day:"numeric"}) + " " +  new Date(pointer.time).toLocaleTimeString('en-GB') + " </p> <p style=\"font-size:12px\">" + yTooltip + "</p>";
                bar.setAttribute("style", barAtt+ "left: "+xScale(pointer.time) +";visibility: visible;")
            }//Change to en-US for 12-hr, en-GB for 24-hr
                //Also i'm sure there a better way but i started with the DateString only and wanted to add the time so here I am- Alvin
            function mouseover() {
                    focus.setAttribute("style", "visibility: visible");
                    bar.setAttribute("style", barAtt + + "visibility: visible; ")	
            }
            function mouseout() {
                    focus.setAttribute("style", "visibility: hidden");
                    bar.setAttribute("style", barAtt + "visibility: hidden; ")
                }
            d3.select(mouseArea)
                .on('mousemove', mousemove)
                .on('mouseleave', mouseout)
                .on('mouseenter', mouseover);
            var endTime = performance.now()
            console.log(`Dot Chart Render, ${labels.length} tags: ${endTime - startTime}`);
            $.notify({
                icon: "tim-icons icon-check-2",
                message: "Chart made!"

            },{
                type: 'success',
                timer: 300,
                placement: {
                    from: "top",
                    align: "center"
                }
            });


            let bs = d3.bisector(function(d){return d[labels[0]]})
            //Idk how to return out of a promise
            let max = d3.max(data, function (d) { return d[labels[0]]})
            let min = d3.min(data, function (d) { return d[labels[0]]}) 
            let avg = d3.mean(data, d => d[labels[0]])
            document.getElementById('maxField').innerHTML = max + " at " + new Date(data[bs.center(data, max)].time)
            document.getElementById('minField').innerHTML = min + " at " + new Date(data[bs.center(data, min)].time)
            document.getElementById('avgField').innerHTML = avg
            document.getElementById('timeField').innerHTML = targetCount + " minutes"
            DataManager.removeStop()
        })
    }
    catch(err){
        raiesError(msg = 'Chart was unable to generate:<br>' + err)
    }
    
}


