var xScale /*Global variable "scales" to revert normalized data back in other js files */
var yScale; //Do these need to be const ? - avlin


/*ONE DAY I WILL CONDENSE ALL THIS CODE. one day... - ALVIN TRAN 5/2/2022 */
// Today is the day 6/2/2022
//We are going to move labels outside of charts, and have the render button check/add tags to our needed labels instead. Labels are the yAxi that we wil lgenerate.
//New xAxis parameter. Default is time (time series). And then regression usees 1 ag, scatter will use multiple.
//Options allows us to do extra functions like regression or filtering
//Current modes: Regression: type, Filter:xyz, 
//xAxis as time genertes 1 large plot
//Mutliple xAxis will generate a scatter and any amount of y's
//single xAXis and any amount of y will generate regression.
function createChart( xAxis = ['time'],labels = [], options = {}){
    return new Promise(function(resolve, reject) { 
        try{
            raiseAlert({icon:"icon-refresh-02", msg:'Chart refreshing...', type : 'warning'})
            DataManager.makeStop()
            while(document.getElementById('linediv').children.length > 0){
                for (let c of document.getElementById('linediv').children){
                    c.remove();
                }
            }

            let allTags = xAxis.concat(labels)
            if (options['filters'] != undefined){
                for (let f of options['filters']){
                    if(allTags.indexOf(f.tag) == -1){
                        allTags.push(f.tag)
                    }
                }


            }
            if(xAxis[0] == 'time')
                allTags.shift()
            const parse = (item) => {
                for (let m in item) {
                    //smoge used to be one liner but now we adjust for timezone in updateDates :<
                    if (m == "time"){
                        if( new Date().getTimezoneOffset() == 240){ //spring forward an hour sice our data is est
                            item[m] = Date.parse(item[m]) + 3600000;
                        }else{ //est so we don't do anything :)
                            item[m] = Date.parse(item[m]);
                        }
                        
                    }else item[m] = +item[m];
                }
                return item;

            };
            var p;
            let dataOut = {}
            if(smallerDateCheck(allTags) ){
                p = new Promise(function(resolve, reject){
                    console.log('Using older data')
                    resolve(globalData)
                })
            }
            else{

                p = DataManager.getRawData(allTags.join(';;'))

            }
            var originalYScales = []
            p.then(function (rawData){
                try{
                    if(typeof rawData == 'string' ){
                        data = d3.csvParse(rawData)
                        globalData = JSON.parse(JSON.stringify(data)) //global data is in EST
                        globalData.sort((a, b) => d3.ascending(new Date(a.time), new Date (b.time)))[globalData.length - 1]
                        data.forEach(r => parse(r))
                        
                        
                    }else{
                        //When using older data, we want to have data within our time range.
                        //If using new data,s ohuldn't affect anything
                        data = JSON.parse(JSON.stringify(globalData))
                        data.forEach(r => parse(r))
                        
                        data = data.filter(r => globalMinimumTime.valueOf() <= r.time && r.time <= globalMaximumTime.valueOf())
                    }


                    //If rescaling
                    let extentDict = {}
                    for (let l of allTags){
                        extentDict[l] = d3.extent(data, d => d[l])

                    }
                    //filtering data
                    if (options['filters'] != undefined){
                        console.log(options['filters'] )
                        for (let f of options['filters']){

                            if(f.type == 'Above' || f.type =='Below'){ //above below
                                data = data.filter(r => (f.type == 'Above') ? r[f.tag] > f.value : r[f.tag] < f.value)

                                }
                            else { //status?? words???


                            }
                        }
                    }
                    let ret = {}
                    if(options['stats'] != undefined){
                        for (let l of labels){
                            let stat = {}
                            let bs = d3.bisector(function(d){return d[l]})
                            stat['max'] = d3.max(data, d =>  d[l])
                            stat['min'] = d3.min(data, d => d[l])
                            stat['mean'] = d3.mean(data, d => d[l])
                            stat['maxDate'] = new Date(data[d3.maxIndex(data, d =>  d[l])].time)
                            stat['minDate'] = new Date(data[d3.maxIndex(data, d =>  d[l])].time)
                            ret[l] = stat

                        }
                    }

                    let chartArea = document.getElementById("linediv");
                    //Chart generation.
                    for(let x of xAxis){
                        //if we ever have time, we only create 1 chart as of 6/2/2022
                        if (x == 'time'){//creating xScale for chart.
                            xScale = d3
                            .scaleTime()
                            .domain([globalMinimumTime.valueOf(), globalMaximumTime.valueOf()]);
                        }else{
                            xScale = d3
                            .scaleLinear()
                            .domain(fc.extentLinear().accessors([d => d[x]])(data)); 
                        }

                        let yLines = [] // used to create multiple lines on same graph
                        let series = []
                        const line = (tag) => {
                        return fc
                            .seriesWebglPoint()
                            .equals((previousData, currentData) => previousData === currentData)
                            .crossValue(d => d[x])
                            .mainValue(d => d[tag])
                            .decorate((program, data, selection) => {
                                fc.webglFillColor().value(d => {
                                    let rgba;
                                    if(tagColor[tag] == undefined){
                                        tagColor[tag] = color.pop();
                                        rgba = tagColor[tag];

                                    }else{
                                        rgba = d3.color(tagColor[tag])
                                    }
                                    return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                                }).data(data)(program);
                            });
                        };
                        //for making a grid of graphs
                        var width = 60, //do math by width; 100vw = 1920; 800 original
                        height = 70, // 100vh = 1080
                        padding = 1, //20 padding
                        n = labels.length,
                        size = (width - 2* padding) 
                        heightSize = (height - 2* padding)  / labels.length,
                        widthSize = (width - 2* padding)  / xAxis.length
                        //labels.forEach(l => lines.push(line(l)));
                        yScale = d3
                            .scaleLinear()
                            .domain([-.1, 1.1]);
                        const gridline = fc.annotationCanvasGridline();
                        for(let y of labels){//maybe unecessary to foor here
                            if(x =='time'){//if we have time, we simple generate the chart all togther


                                yLines.push(line(y))
                                if( labels.length == 1){//regular y scale
                                    yScale = d3 
                                        .scaleLinear()
                                        .domain([extentDict[y][0] - (extentDict[y][1]-extentDict[y][0])*.1, extentDict[y][1]+ (extentDict[y][1]-extentDict[y][0])*.1]);
                                }else{//replace y scale
                                    //need to normalize values
                                    const normalScale = d3.scaleLinear()
                                    .domain(extentDict[y]) 
                                    .range([0,1])
                                    data.forEach((d) => {d[y] = normalScale(d[y])})
                                    originalYScales.push(normalScale);
           
                                }
                            }else{ //when using time, we instead generate each char indivdually. this is scatter or regression between x/y
                                let chartDiv = document.createElement("div");
                                let xShift =  xAxis.indexOf(x) * widthSize
                                let yShift = labels.indexOf(y) * heightSize
                                if (xAxis.length == 1 || labels.length == 1) { //given only 1xAxis, we would like ot geenrate a grid rather than column for that xAxis
                                    let gridSide = Math.ceil(Math.sqrt(d3.max([labels.length,xAxis.length])))
                                    heightSize = (height - 2* padding) /gridSide
                                    widthSize = (width - 2* padding) /gridSide

                                    let choose = (xAxis.length == 1) ? labels.indexOf(y) :  xAxis.indexOf(x)
                                    xShift = choose % gridSide * widthSize
                                    yShift = Math.floor(choose / gridSide)  * heightSize
                                }
                                chartDiv.id = x + y;
                                chartDiv.setAttribute("style", "position: absolute; height:" + heightSize + "vh; width:"+ widthSize + "vw;transform: translate(" + (xShift) + "vw, " + (yShift) + "vh);")
                                chartArea.append(chartDiv)
                                xScale = d3.scaleLinear()
                                .domain(extentDict[x])
                                yScale = d3.scaleLinear()
                                .domain(extentDict[y]) //same no matter wat

                                let histData = []
                                if(x == y){ //matrix x = y is  histogram
                                    let bin = d3.bin() //Binning function w/ accesor fxn
                                        .value(d=>d[x])
                                        .thresholds(10)
                                    let bucketedData = bin(data) //Just rearranges the data into an array(all buckets), holding array(1 bucket) of values
                                    let binEnds = []//create bin labels, to be stored as [ [], [], [] ]
                                    let freq = []

                                    let extent=fc.extentLinear().accessors([d => d[x]])(data)
                                    let end=extent[0] + (extent[1]-extent[0])/bucketedData.length *0.5;//starting with left most midpointvalue we equally incrment, probalby not how the program works but you know.
                                    //Have to do this since we are using a Linear Scale on a BAR graph to create a HISTOGRAM
                                    //Just positioning middle of bar to be in middle of data range instead of the left end.
                                    //ALso bukcets will get NaN values
                                   for (let b of bucketedData){//Creating arrays of info

                                        freq.push(b.length)
                                        binEnds.push(end)
                                       end = end + ( (extent[1] - extent[0])/bucketedData.length )

                                   }
                                    for (let b in freq) //doing it outside it was bugger before idk why
                                        histData.push({'freq': freq[b], 'ends': binEnds[b]})
                                    xScale = d3.scaleLinear()
                                        .domain(extent)
                                    yScale = d3.scaleLinear() //Y have values 0 to maximum bin size
                                        .domain([0, d3.max(freq, function(d) {return d;})])
                                    yLines.push(fc.autoBandwidth(fc.seriesWebglBar()).widthFraction(1)
                                            .xScale(xScale)
                                            .yScale(yScale)
                                            .crossValue(d => d['ends'])
                                            .mainValue(d => d['freq'])
                                            .decorate((program, data, selection) => {
                                                 fc.webglFillColor().value(d => {
                                                    let rgba;
                                                    if(tagColor[y] == undefined){
                                                        tagColor[y] = color.pop();
                                                        rgba = tagColor[y];

                                                    }else{
                                                        rgba = d3.color(tagColor[y])
                                                    }
                                                    return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                                                }).data(data)(program);
                                            }));
                                }//end x==y
                                else{//scatter ploting
                                    yLines = [] //Clearing yLines 
                                    yLines.push(line(y))
                                    if(options['regression'] != undefined){ //if we do regression
                                        let splitData = data.map(row => [row[x], row[y]]) // seperate our data into an array of [x,y] pairs
                                        let rr = {}
                                        switch (regressionType){
                                            case 'Lin':
                                                rr = linear(splitData);
                                                break;
                                            case '2nd':
                                                rr = polynomial(splitData, { order: 2 , precision: 6, period: null});
                                                break;
                                            case '3rd':
                                                rr = polynomial(splitData, { order: 3 , precision: 6, period: null});
                                                break;
                                            case 'Log':
                                                rr = logarithmic(splitData);
                                                break;
                                            case 'Pow':
                                                rr = power(splitData);
                                                break;
                                            case 'Exp':
                                                rr = exponential(splitData);
                                                break;
                                            default:
                                        }
                                        //regresison results from datautilities for exporting
                                        for(let key of Object.keys(regressionResults)){
                                            regressionResults[key][x + y] = rr[key]
                                        }
                                        //might use rr here since we don't need to hold the points
                                        splitData = regressionResults['points'][x+y].map(row => [row[0], row[1]]); //Getting the "predicted points" to plot. an array of arrays [x,y]; x is acutal data point we have, y = predict(x)

                                        if (isNaN(regressionResults['r2'][x + y])){ //Some regressions are imcompatiable ? we get NaN 
                                            $.notify({
                                            icon: "tim-icons icon-puzzle-10",
                                            message: "Your regression type does not yield results for " + x + " and " + y

                                        },{
                                            type: 'danger',
                                            timer: 10,
                                            placement: {
                                                from: "top",
                                                align: "center"
                                            }
                                        });
                                        }
                                        const regressionSeries = fc.seriesWebglPoint()
                                            .equals((previousData, currentData) => previousData === currentData)
                                            .crossValue(d => d['predict' + x])
                                            .mainValue(d => d['predict' + y])
                                            .decorate((program, data, selection) => {
                                                 fc.webglFillColor().value(d => {
                                                    const rgba = d3.color(d3.schemePaired[0]);
                                                    return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                                                    }).data(splitData)(program);
                                                })
                                        yLines.push(regressionSeries); 
                                        /*We essentially generate a line with the regression equation
                                        Normally ig only gives te predictY for every existing X in data
                                        */
                                        let predictXMax = -1*Number.MAX_SAFE_INTEGER;
                                        let predictXMin = Number.MAX_SAFE_INTEGER;
                                        for(let r = 0; r < splitData.length; r++){
                                            if (splitData[r][0] > predictXMax)
                                                predictXMax = splitData[r][0]
                                            if (splitData[r][0] < predictXMin)
                                                predictXMin = splitData[r][0]
                                        }
                                        let predictInc = (predictXMax - predictXMin)/ data.length
                                        let predictPointer = predictXMin
                                        for (let r = 0; r < data.length; r++){ 
                                            data[r]['predict' + x] = predictPointer;
                                            data[r]['predict' + y] = regressionResults['predict'][x+y](predictPointer)[1];
                                            predictPointer += predictInc;
                                        }
                                    }


                            }//end else
                            const ticks = 5;
                            const gridline = fc.annotationCanvasGridline().xTicks(ticks).yTicks(ticks);
                            const container = document.getElementById(x + y)
                            series = fc
                                .seriesWebglMulti()
                                .xScale(xScale)
                                .yScale(yScale)
                                .series(yLines);
                            const chart = fc
                                    .chartCartesian(xScale, yScale)
                                    .webglPlotArea(series)
                                    .canvasPlotArea(gridline)
                                    .useDevicePixelRatio(true)
                                    .xTicks(ticks)
                                    .xNice()
                                    .yTicks(ticks)
                                    .yNice()
                            if(options['regression'] != undefined) {
                                const zoom = fc.zoom().on('zoom', event => {
                                    render(); 
                                });
                                chart.decorate(sel => {

                                    sel.enter().call(zoom, xScale, yScale);

                                })
                            }
                            //Label maker, check if we are on bottom or top
                            if(labels.indexOf(y) == labels.length - 1)
                                chart.xLabel(x  + " - " + tagEng[tagLabels.indexOf(x)])
                            if(labels.indexOf(x) == labels.length - 1)
                                chart.yLabel(y + " - " + tagEng[tagLabels.indexOf(y)])
                            chart.xLabel(x  + " - " + tagEng[tagLabels.indexOf(x)])
                            chart.yLabel(y + " - " + tagEng[tagLabels.indexOf(y)])

                             const render = () => { 
                                 if(x == y)
                                     d3.select(container).datum(histData).call(chart)
                                 else
                                     d3.select(container).datum(data).call(chart)
                            };
                            render();
                        }//end of y
                        //geneating the large chart if time is our option
                        if (x=='time'){

                            const series = fc
                                .seriesWebglMulti()
                                .xScale(xScale)
                                .yScale(yScale)
                                .series(yLines);
                            createEl.select(document.getElementById("linediv")).append("div").id("chart").end();
                            const container = document.getElementById("chart")

                            const zoom = fc.zoom().on('zoom', event => {
                                render(); 
                            }); 
                            var yLabel = "Relative Magnitude";
                            if (labels.length == 1) 
                                {
                                    yLabel = (labels[0] + " - " + tagEng[tagLabels.indexOf(labels[0])])
                                };


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
                            function mousemove(event)
                            {
                                var x0 = (d3.pointer(event, this)[0]);
                                var y0 = (d3.pointer(event, this)[1]);
                                var bisect = d3.bisector(function(d){return d.time});
                                let index = bisect.center(data, xScale.invert(x0))
                                let pointer = data[index] 
                                x0 = (x0 < 650 ? xScale(pointer.time) : xScale(pointer.time) - 240)
                                var yTooltip = '';
                                for (let l of labels){
                                    var current = originalYScales[labels.indexOf(l)];
                                    var yAdjust = pointer[l];
                                    if (labels.length > 1) yAdjust = current.invert(pointer[l])
                                    yTooltip += l + ": " + yAdjust.toFixed(4) + "<br>";
                                }
                                focus.setAttribute("style", tooltipAtt+ "left:" +x0+"; top: "+(y0 + 10)+ ";visibility: visible");
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

                        }//end of time
                    }// end of something??
                }//end of x loop



                    raiseAlert({icon:"icon-check-2", msg:'Chart generated!.', type : 'success', timer:100})
                    DataManager.removeStop()
                    resolve(ret)
                }catch (e){//End of Inside Try| STart of inside Catch
                    console.log(e)
                    raiseError({msg : 'Error generating chart: ' + e})
                }
            })//End of promies
        }//End of try
        catch (e){
            console.log(e)
            raiseError({msg : e})
        }
    })
}
/* Creates main line chart using D3FC. WebGL for the lines, Canvas for the gridlines. 
    Nested Promises are used to ensure relevant asynchronous data is loaded before moving on to the next step. */
function createLineChart() {
    try{
        originalYScales = []; 
        console.log('Creating \'Line\' Chart');
        DataManager.makeStop()
        var startTime = performance.now();

        const labels = DataManager.getActive();
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
                globalData.sort((a, b) => d3.ascending(new Date(a.time), new Date (b.time)))[globalData.length - 1]
                data.forEach(r => parse(r))
            }else{
                //When using older data, we want to have data within our time range.
                //If using new data,s ohuldn't affect anything
                data = JSON.parse(JSON.stringify(globalData))
                data.forEach(r => parse(r))
                data = data.filter(r => globalMinimumTime.valueOf() <= r.time && r.time <= globalMaximumTime.valueOf())
            }



            if (document.getElementById("chart") != undefined) {
                document.getElementById("chart").remove();
            }

            createEl.select(document.getElementById("linediv")).append("div").id("chart").end();

            var valueMax = -1*Number.MAX_SAFE_INTEGER;
            var valueMin = Number.MAX_SAFE_INTEGER;
            var maxDict = {};
            var minDict = {};
            for (let i = 0; i < labels.length; i++) {
                let max = d3.max(data, function (d) { return d[labels[i]]});
                let min = d3.min(data, function (d) { return d[labels[i]]});

                valueMax = Math.max(valueMax, max);
                valueMin = Math.min(valueMin, min);
                if (labels.length > 1){ //grabing max/min for each if we have to scale (multiple tags)
                    maxDict[labels[i]] = max;
                    minDict[labels[i]] = min
                }
            }

            //Scales are made to put Y values into 0-1 scale if we are given multuple tags. We keep the origanlYScales for each tag/label to cnvert back from 0-1 to actual values.
            //For download button purposes, i have made the scale variables global
            xScale = d3
                    .scaleTime()
                    .domain([globalMinimumTime.valueOf(), globalMaximumTime.valueOf()]);
            if (labels.length == 1){ //Rescale Y if we have multiple labels
                yScale = d3
                    .scaleLinear()
                    .domain([valueMin - (valueMax-valueMin)*.1, valueMax+ (valueMax-valueMin)*.1]);
                originalYScales.push(yScale);
            }else{

                for (let i = 0; i < labels.length; i++){
                    const normalScale = d3
                                .scaleLinear()
                                .domain([minDict[labels[i]],maxDict[labels[i]]]) 
                                .range([0,1])
                    originalYScales.push(normalScale);
                    for (let j = 0; j < data.length; j++){
                        data[j][labels[i]]= normalScale(data[j][labels[i]]);
                    }
                }
                yScale = d3
                    .scaleLinear()
                    .domain([-.1, 1.1]);
            };
            var width = 42 //do math by width; 100vw = 1920; 800 default
                padding = 1, //20 padding
                n = labels.length,
                size = (width - 2* padding) / n //dividing remaining area by number of labels
            //lines are a lie this is a scatterplot >:(
            //Function to create lines; apply it to each tag
            const line = (tag) => {
                return fc
                    .seriesWebglPoint()
                    .equals((previousData, currentData) => previousData === currentData)
                    .crossValue(d => d.time)
                    .mainValue(d => d[tag])
                    .decorate((program, data, selection) => {
                        fc.webglFillColor().value(d => {
                            let rgba;
                            if(tagColor[tag] == undefined){
                                tagColor[tag] = color.pop();
                                rgba = tagColor[tag];

                            }else{
                                rgba = d3.color(tagColor[tag])
                            }
                            return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                        }).data(data)(program);
                    });
            };
            var lines = [];
            labels.forEach(l => lines.push(line(l)));

        
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


            var yLabel = "Relative Magnitude";
            if (labels.length == 1) 
                {
                    yLabel = (labels[0] + " - " + tagEng[tagLabels.indexOf(labels[0])])
                };


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
            function mousemove(event)
            {
                var x0 = (d3.pointer(event, this)[0]);
                var y0 = (d3.pointer(event, this)[1]);
                var bisect = d3.bisector(function(d){return d.time});
                let index = bisect.center(data, xScale.invert(x0))
                let pointer = data[index] 
                x0 = (x0 < 650 ? xScale(pointer.time) : xScale(pointer.time) - 240)
                var yTooltip = '';
                for (let l of labels){
                    var current = originalYScales[labels.indexOf(l)];
                    var yAdjust = pointer[l];
                    if (labels.length > 1) yAdjust = current.invert(pointer[l])
                    yTooltip += l + ": " + yAdjust.toFixed(4) + "<br>";
                }
                focus.setAttribute("style", tooltipAtt+ "left:" +x0+"; top: "+(y0 + 10)+ ";visibility: visible");
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
            document.getElementById('stopRightThere').remove()
        })
    }
    catch(err){
        raiseror(msg = 'Chart was unable to generate:<br>' + err)
    }
    
}


function createTrends(){
    try{
        //xAxisTag -> just remembering it exists out of scope.
        yAxisTags = DataManager.getActive()
        let labels = [xAxisTag].push(yAxisTags)
        if (xAxisTag == ''  || yAxisTags.length == 0){
                $.notify({
                icon: "tim-icons icon-simple-remove",
                message: "Please select a X and Y Axis first."

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
        DataManager.makeStop()
        console.log('Creating Regression Chart')
        originalYScales = []; 
        var startTime = performance.now();

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
            if (document.getElementById("chart") != undefined) {
                document.getElementById("chart").remove();
            }
             var width = 42 //do math by width; 100vw = 1920; 800 default
            padding = 1, //20 padding
            n = labels.length,
            size = (width - 2* padding) / n //dividing remaining area by number of labels

            createEl.select(document.getElementById("linediv")).append("div").id("chart").end();

            console.log("Post Processed:");
            console.log(data);


            var valueMax = -1*Number.MAX_SAFE_INTEGER;
            var valueMin = Number.MAX_SAFE_INTEGER;
            var maxDict = {};
            var minDict = {};
            for (let i = 0; i < labels.length; i++) {
                let max = d3.max(data, function (d) { return d[labels[i]]});
                let min = d3.min(data, function (d) { return d[labels[i]]});

                valueMax = Math.max(valueMax, max);
                valueMin = Math.min(valueMin, min);
                if (labels.length > 1){ //grabing max/min for each if we have to scale (multiple tags)
                    maxDict[labels[i]] = max;
                    minDict[labels[i]] = min
                }
            }
            //Scales are made to put Y values into 0-1 scale if we are given multuple tags. We keep the origanlYScales for each tag/label to cnvert back from 0-1 to actual values.
            //For download button purposes, i have made the scale variables global
            xScale = d3
                    .scaleLinear()
                    .domain(fc.extentLinear().accessors([d => d[xAxisTag]])(data)); 
            let yExtent = fc.extentLinear().accessors([d => d[yAxisTag]])(data);
            let yRange = yExtent[1] - yExtent[0];
            yScale = d3
                    .scaleLinear()
                    .domain([yExtent[0] - yRange*.1, yExtent[1] + yRange*.1]) //expanding for 10% margins
            /*
            color = d3.scaleOrdinal()
                .domain(labels)
                .range(d3.schemeSet2);
                */
            //lines are a lie this is a scatterplot >:(

            const line =  fc.seriesWebglPoint()
                    .equals((previousData, currentData) => previousData === currentData)
                    .crossValue(d => d[xAxisTag])
                    .mainValue(d => d[yAxisTag])
                    .decorate((program, data, selection) => {
                        fc.webglFillColor().value(d => {
                            let rgba;
                            if(tagColor[yAxisTag] == undefined){
                                tagColor[yAxisTag] = color.pop();
                                rgba = tagColor[yAxisTag];

                            }else{
                                rgba = d3.color(tagColor[yAxisTag])
                            }
                            return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                        }).data(data)(program);
                    });
            var lines = [line];

            //Oh boy is that regression !

            let splitData = data.map(row => [row[xAxisTag], row[yAxisTag]]) // seperate our data into an array of [x,y] pairs
            console.log("Regression Type: " + regressionType)
            switch (regressionType){
                case 'Lin':
                    regressionResults = linear(splitData);
                    break;
                case '2nd':
                    regressionResults = polynomial(splitData, { order: 2 , precision: 6, period: null});
                    break;
                case '3rd':
                    regressionResults = polynomial(splitData, { order: 3 , precision: 6, period: null});
                    break;
                case 'Log':
                    regressionResults = logarithmic(splitData);
                    break;
                case 'Pow':
                    regressionResults = power(splitData);
                    break;
                case 'Exp':
                    regressionResults = exponential(splitData);
                    break;
                default:
            }

            splitData = regressionResults['points'].map(row => [row[0], row[1]]); //Getting the "predicted points" to plot. an array of arrays [x,y]; x is acutal data point we have, y = predict(x)

            if (isNaN(regressionResults['r2'])){ //Some regressions are imcompatiable ? we get NaN 
                $.notify({
                icon: "tim-icons icon-puzzle-10",
                message: "Your regression type does not yield results."

            },{
                type: 'danger',
                timer: 300,
                placement: {
                    from: "top",
                    align: "center"
                }
            });
            }
            const regressionSeries = fc.seriesWebglPoint()
                .equals((previousData, currentData) => previousData === currentData)
                .crossValue(d => d['predictX'])
                .mainValue(d => d['predictY'])
                .decorate((program, data, selection) => {
                     fc.webglFillColor().value(d => {
                        const rgba = d3.color(d3.schemePaired[0]);
                        return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                        }).data(splitData)(program);
                    })
            lines.push(regressionSeries); 
            /*We essentially generate a line with the regression equation
            Normally ig only gives te predictY for every existing X in data
            */
            let predictXMax = -1*Number.MAX_SAFE_INTEGER;
            let predictXMin = Number.MAX_SAFE_INTEGER;
            for(let r = 0; r < splitData.length; r++){
                if (splitData[r][0] > predictXMax)
                    predictXMax = splitData[r][0]
                if (splitData[r][0] < predictXMin)
                    predictXMin = splitData[r][0]
            }
            let predictInc = (predictXMax - predictXMin)/ data.length
            let predictPointer = predictXMin
            for (let r = 0; r < data.length; r++){ 
                data[r]['predictX'] = predictPointer;
                data[r]['predictY'] = regressionResults['predict'](predictPointer)[1];
                predictPointer += predictInc;
            }

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

            const chart = fc
                .chartCartesian(xScale, yScale)
                .webglPlotArea(series)
                .canvasPlotArea(gridline)
                .decorate(sel => {

                    sel.enter().call(zoom, xScale, yScale);

                }).xLabel(xAxisTag + " - " + tagEng[tagLabels.indexOf(xAxisTag)])
                .yLabel(yAxisTag + " - " + tagEng[tagLabels.indexOf(yAxisTag)])
                .useDevicePixelRatio(true);

            const render = () => { 
                d3.select(container)
                .datum(data)
                .call(chart);

            };

            render();
            //
            container.setAttribute("style", "height:75vh; width:71vw;")
             if(DataManager.getActive().length == 1){
                const cChart = document.getElementsByClassName("cartesian-chart")[0];
                let mouseArea = document.createElement("div");
                mouseArea.setAttribute("pointer-events", "all")
                mouseArea.setAttribute("class", "plot-area");
                mouseArea.id = "mouseArea"
                mouseArea.setAttribute("style", "z-index:10");



            let focus = document.createElement("div");
                const tooltipAtt = "padding: 10px; z-index: 9; position: absolute; width:12vw; margin-top: 3vh; word-wrap: break-word; white-space:normal; "
                focus.setAttribute("style", tooltipAtt+ "visibility: hidden; ");
                focus.setAttribute("class", "badge badge-default");
                focus.innerHTML = "Bread";
                cChart.append(mouseArea);
                mouseArea.append(focus);

          
           
                function mousemove(event) {
                        // recover coordinate we need
                        var x0 = (d3.pointer(event, this)[0]);
                        var y0 = (d3.pointer(event, this)[1]);
                        x0  = (x0 < 650 ? x0 + 100: x0 - 240)

                        let yTooltip = yAxisTag + ":" + yScale.invert(y0).toFixed(4);
                        focus.setAttribute("style", tooltipAtt+ "left:" +x0+"; top: "+y0 + ";visibility: visible");

                        focus.innerHTML = "<p class=\"card-title\" style=\"font-size:12px\">"+ regressionResults['string'] + "<br> r2: " + regressionResults['r2'] + "</p>  <p style=\"font-size:12px\">" + xAxisTag + ": " + xScale.invert(x0).toFixed(4) + "<br>"+ yTooltip + "</p>";

                }
                function mouseover() {
                        focus.setAttribute("style", "visibility: visible");

                }
                function mouseout() {
                        focus.setAttribute("style", "visibility: hidden");
                    }
                d3.select(mouseArea)
                    .on('mousemove', mousemove)
                    .on('mouseleave', mouseout)
                    .on('mouseenter', mouseover);
            }
            

            var endTime = performance.now()
            console.log(`Trend Chart Render: ${endTime - startTime}`);
            $.notify({
                icon: "tim-icons icon-check-2",
                message: "Chart made !"

            },{
                type: 'success',
                timer: 300,
                placement: {
                    from: "top",
                    align: "center"
                }
            });
            DataManager.removeStop()
            }
        )}
    catch(err){
        raiesError(msg = 'Chart was unable to generate:<br>' + err)
    }
}



//Hi I'm Alvin and I have decided to do this different <3
//I lied I'm doing it the same huh
//webGL is way faster and svg is slow as with the amount of data we're using :c. svg would lok better
function createMatrix(){
    try{
        originalYScales = []; 
        console.log('Creating \'Matrix\' Chart');
        DataManager.makeStop()
        var startTime = performance.now();
        while(document.getElementById('linediv').children.length > 0){
            for (let c of document.getElementById('linediv').children){
                c.remove();
            }
        }
        const labels = DataManager.getActive();
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



            if (document.getElementById("chart") != undefined) {
                document.getElementById("chart").remove();
            }
            console.log(data);
            test = data;

            var width = 42 //do math by width; 100vw = 1920; 800 default
                padding = 1, //20 padding
                n = labels.length,
                size = (width - 2* padding) / n //dividing remaining area by number of labels

            //Chart generating
            let chartArea = document.getElementById("linediv");
            for(let xTag of labels){
                for (let yTag of labels){

                    //Creating the location to trow the chart into
                    //Use absolute positioning to stack areas on top of each other, THEN translate them into appropiate spots
                    let chartDiv = document.createElement("div");
                    chartDiv.id = xTag + yTag;
                    chartDiv.setAttribute("style", "position: absolute; height:" + size + "vw; width:"+ size + "vw;transform: translate(" + (labels.indexOf(xTag) * size) + "vw, " + (labels.indexOf(yTag)*size) + "vw);")
                    chartArea.append(chartDiv)

                    let xScale;
                    let yScale;
                    var histData =[]//Will be [ {}, {},, {}] as regular data
                     //Catching for x = y charts to geneate histogram
                    let series;

                    if(xTag == yTag){
                        //There is only bar chart no histogram so i must transform the data+scale to be acceptable.
                        //Creating buckets


                        let bin = d3.bin() //Binning function w/ accesor fxn
                            .value(d=>d[xTag])
                            .thresholds(10)
                        let bucketedData = bin(data) //Just rearranges the data into an array(all buckets), holding array(1 bucket) of values
                        test = bucketedData
                        let binEnds = []//create bin labels, to be stored as [ [], [], [] ]
                        let freq = []

                        let extent=fc.extentLinear().accessors([d => d[xTag]])(data)
                        let end=extent[0] + (extent[1]-extent[0])/bucketedData.length *0.5;//starting with left most midpointvalue we equally incrment, probalby not how the program works but you know.
                        //Have to do this since we are using a Linear Scale on a BAR graph to create a HISTOGRAM
                        //Just positioning middle of bar to be in middle of data range instead of the left end.
                        //ALso bukcets will get NaN values
                       for (let b of bucketedData){//Creating arrays of info

                            freq.push(b.length)
                            binEnds.push(end)
                           end = end + ( (extent[1] - extent[0])/bucketedData.length )

                       }
                        for (let b in freq) //doing it outside it was bugger before idk why
                            histData.push({'freq': freq[b], 'ends': binEnds[b]})
                        console.log(histData);
                        test1 = histData
                        test2 = bucketedData
                        xScale = d3.scaleLinear()
                            .domain(extent)

                        yScale = d3.scaleLinear() //Y have values 0 to maximum bin size
                            .domain([0, d3.max(freq, function(d) {return d;})])
                        series = fc.autoBandwidth(fc.seriesWebglBar()).widthFraction(1)
                                .xScale(xScale)
                                .yScale(yScale)
                                .crossValue(d => d['ends'])
                                .mainValue(d => d['freq'])
                                .decorate((program, data, selection) => {
                                     fc.webglFillColor().value(d => {
                                        let rgba;
                                        if(tagColor[yTag] == undefined){
                                            tagColor[yTag] = color.pop();
                                            rgba = tagColor[yTag];

                                        }else{
                                            rgba = d3.color(tagColor[yTag])
                                        }
                                        return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                                    }).data(data)(program);
                                });



                    }else{
                        xScale = d3.scaleLinear()
                            .domain(fc.extentLinear().accessors([d => d[xTag]])(data))
                            ;
                       yScale = d3.scaleLinear()
                            .domain(fc.extentLinear().accessors([d => d[yTag]])(data))
                            ;
                        series = fc
                                .seriesWebglPoint()
                                .crossValue(d => d[xTag])
                                .mainValue(d => d[yTag])
                                .xScale(xScale)
                                .yScale(yScale)
                                .decorate((program, data, selection) => {
                                     fc.webglFillColor().value(d => {
                                        let rgba;
                                        if(tagColor[yTag] == undefined){
                                            tagColor[yTag] = color.pop();
                                            rgba = tagColor[yTag];

                                        }else{
                                            rgba = d3.color(tagColor[yTag])
                                        }
                                        return [rgba.r / 255, rgba.g / 255, rgba.b / 255, rgba.opacity];
                                    }).data(data)(program);

                                });
                         }//end of else
                    const ticks = 5;
                    const gridline = fc.annotationCanvasGridline().xTicks(ticks).yTicks(ticks);
                            const container = document.getElementById(xTag + yTag)


                            const chart = fc
                                    .chartCartesian(xScale, yScale)
                                    .webglPlotArea(series)
                                    .canvasPlotArea(gridline)
                                    .useDevicePixelRatio(true)
                                    .xTicks(ticks)
                                    .xNice()
                                    .yTicks(ticks)
                                    .yNice()
                            //Label maker, check if we are on bottom or top
                            if(labels.indexOf(yTag) == labels.length - 1)
                                chart.xLabel(xTag)
                            if(labels.indexOf(xTag) == labels.length - 1)
                                chart.yLabel(yTag)

                             const render = () => { 
                                 if(xTag == yTag)
                                     d3.select(container).datum(histData).call(chart)
                                 else
                                     d3.select(container).datum(data).call(chart)


                            };

                            render();


                    }
                }
            DataManager.removeStop()
            $.notify({
                    icon: "tim-icons icon-check-2",
                    message: "Chart made !"

                },{
                    type: 'success',
                    timer: 300,
                    placement: {
                        from: "top",
                        align: "center"
                    }
                });

            })
    }
    catch(err){
        raiesError(msg = 'Chart was unable to generate:<br>' + err)
    }
    
}
