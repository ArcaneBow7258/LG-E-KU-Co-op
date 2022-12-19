//Down sampling test;
		/*
		console.log(data);
        const downSample = fc.largestTriangleThreeBucket()
			.bucketSize(20)
			.x(function(d) { return d['time']; }) 
			.y(function(d) { return d[labels[0]];});
		//
		
		const downSample = fc.modeMedian()
			.value(function(d) { return d[labels[0]];})
			.bucketSize(50);
			
		var smoldata = downSample(data);
		data = smoldata;
		console.log(data);
		*/		

//on dataPoint representation cursor;
				/*
			    const r = Math.abs(xScale.invert(x0).getTime() - xScale.invert(x0 - 5).getTime());
				const closest = tree.find(xScale.invert(x0).getTime(), yScale.invert(y0), r)
				console.log(closest);
				if(closest){
				focus.setAttribute("style", tooltipAtt+ "left:" +xScale(closest.time)+"; top: "+yScale(closest[labels[0]]));
				}
				*/




/* Unused function right now. Eventually will be incorporated into the scatter plot matrix. */
function createHistogram(tag_name) {

    // set the dimensions and margins of the graph
    var margin = {top: 10, right: 30, bottom: 30, left: 40},
        width = 560 - margin.left - margin.right,
        height = 200 - margin.top - margin.bottom;

    if (document.getElementById(`${tag_name}_hist_div`) != undefined ) {
        document.getElementById(`${tag_name}_hist_div`).remove();
    }

    let div = createEl.selectById("histogram-chart-area")
        .append("div") // main div for all the elements
            .id(`${tag_name}_hist_div`)
        .subelement("label") // label for the tag name, first visible thing in div
            .innerHTML(tag_name)
            .style("font-size", "30px")
        .subelement("div") // div for the time range selectors
        .end() // Returns final element from a call to append or subelement

    createEl.select(div)
        .append("label") // minTime
            .innerHTML("Bins: ")
        .append("input") // maxTime
            .type("number")
            .id(`${tag_name}-histbins`)
            .step("1")
        .end()

    // Create the svg element for the histogram
    var svg = d3.select(div)
        .append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom)
            .attr("id", `${tag_name}_hist`)
        .append("g")
            .attr("transform",
                "translate(" + margin.left + "," + margin.top + ")");

    // Parse the data
    var data;
    if (arguments.length == 2) {
        data = d3.csvParse(arguments[1]);
    } else {
        data = d3.csvParse(DataManager.toCSVString(tag_name));
    }
    //console.log(data);
    data.forEach(function(d) {
        d.time = d.time;
        d[tag_name] = parseFloat(d[tag_name]);
    });
    var max = parseFloat(d3.max(data, function(d) { return d[tag_name]; } ));
    var min = parseFloat(d3.min(data, function(d) { return d[tag_name]; } ));

    // X axis: scale and draw:
    var x = d3.scaleLinear()
        .domain([min, max])     // can use this instead of 1000 to have the max of data: d3.max(data, function(d) { return +d.price })
        .range([0, width]);
    svg.append("g")
        .attr("transform", "translate(0," + height + ")")
        .call(d3.axisBottom(x));
    
    var y = d3.scaleLinear()
        .range([height, 0]);
    var yAxis = svg.append("g");

    // Create the tooltip for when a histogram bar is hovered
    var tooltip = d3.select(div)
        .append("div")
        .attr("class", "svg-tooltip")
        .style("position", "absolute")
        .style("visibility", "hidden");

    function updateBins(bins) {

        // Calculate the ranges for the bins based on the bin width
        var thresholdArray = [];
        var sum = parseFloat(min), i = 1;
        if (bins <= 0) {
            bins = 10;
        }
        var bin_width = (max - min) / bins;
        while(sum < (max - bin_width)) {
            sum = min + i * bin_width;
            thresholdArray.push(sum);
            i += 1;
        }
        if ((max - sum) < bin_width * 0.5) { thresholdArray.pop(); }

        var histogram = d3.histogram()
            .value(function(d) { return d[tag_name]; })
            .domain(x.domain())
            .thresholds(thresholdArray);

        // And apply this function to data to get the bins
        var bins = histogram(data);

        y.domain([0, d3.max(bins, function(d) { return d.length; })]);
        yAxis.transition()
            .duration(1000)
            .call(d3.axisLeft(y));

        // Join the rect with the bins data
        var u = svg.selectAll("rect")
            .data(bins)

        // Manage the existing bars and eventually the new ones:
        u.enter()
            .append("rect") // Add a new rect for each new elements
            .merge(u) // get the already existing elements as well
            .transition() // and apply changes to all of them
            .duration(1000)
            .attr("x", 1)
            .attr("transform", function(d) { return "translate(" + x(d.x0) + "," + y(d.length) + ")"; })
            .attr("width", function(d) { return x(d.x1) - x(d.x0) ; })
            .attr("height", function(d) { return height - y(d.length); })
            .attr("count", function(d) { return d.length; })
            .attr("start", function(d) { return d.x0; })
            .attr("end", function(d) { return d.x1; })
            .style("fill", color(tag_name))

        // Delete the rectangles not in use anymore
        u.exit().remove()

        // Tooltip with count
        svg.selectAll("rect")
        .on("mouseover", function(d) {
            //console.log(d);
            // change the selection style
            d3.select(this)
                .attr('stroke-width', '2')
                .attr("stroke", "black");
            // make the tooltip visible and update its text
            tooltip
                .style("visibility", "visible")
                .text(`Count: ${Math.round(d.toElement.attributes.count.value)}\nStart: ${d.toElement.attributes.start.value}\nEnd: ${d.toElement.attributes.end.value}`);
        })
        .on("mousemove", function(d) {
            // console.log(d);
            tooltip
                .style("top", d.clientY - 350 + "px")
                .style("left", d.clientX + 10 + "px");
        })
        .on("mouseout", function() {
            // change the selection style
            d3.select(this).attr('stroke-width', '0');
            tooltip.style("visibility", "hidden");
        });
    }

    updateBins(0);
    
    d3.select(document.getElementById(`${tag_name}-histbins`)).on("input", function() {
        updateBins(+this.value);
    });
}

/* Needs a lot of work - whoever was her ebefore alvin*/ 
//https://bl.ocks.org/Fil/6d9de24b31cb870fed2e6178a120b17d tihs is copied from here - Alvin
function createScatterplotMatrix(tagName) {

    console.log("Creating Scatterplot Matrix");

    // Remove the previous chart if there is one
    if (document.querySelector("#scatter-matrix") != undefined ) {
        document.querySelector("#scatter-matrix").remove();
    }

    var size = 230,
    padding = 20;

    var x = d3.scaleLinear()
        .range([padding / 2, size - padding / 2]);

    var y = d3.scaleLinear()
        .range([size - padding / 2, padding / 2]);

    var xAxis = d3.axisBottom()
        .scale(x)
        .ticks(6);

    var yAxis = d3.axisLeft()
        .scale(y)
        .ticks(6);

    var color = d3.scaleOrdinal(d3.schemeCategory10);
    
    var data;
    if (arguments.length == 2) {
        data = d3.csvParse(arguments[1]);
    } else {
        data = d3.csvParse(DataManager.toCSVStringAll());
    }

    var domainByTrait = {},
        traits = Object.keys(data[0]).filter(function(d) { return d !== "time"; }),
        n = traits.length;

    traits.forEach(function(trait) {
        domainByTrait[trait] = d3.extent(data, function(d) { return d[trait]; });
    });

    xAxis.tickSize(size * n);
    yAxis.tickSize(-size * n);

    var brush = d3.brush()
        .on("start", brushstart)
        .on("brush", brushmove)
        .on("end", brushend)
        .extent([[0,0],[size,size]]);

    var svg = d3.select("#scatter-chart-area")
        .append("svg")
            .attr("width", $("#scatter-chart-area").parent().width() * n + 150)
            .attr("height", $("#scatter-chart-area").parent().height() * n + 150)
            .attr("id", "scatter-matrix")
        .append("g")
            .attr("transform", "translate(" + padding + "," + padding / 2 + ")");

    svg.selectAll(".x.axis")
        .data(traits)
        .enter().append("g")
        .attr("class", "x axis")
        .attr("transform", function(d, i) { return "translate(" + (n - i - 1) * size + ",0)"; })
        .each(function(d) { x.domain(domainByTrait[d]); d3.select(this).call(xAxis); });

    svg.selectAll(".y.axis")
        .data(traits)
        .enter().append("g")
        .attr("class", "y axis")
        .attr("transform", function(d, i) { return "translate(0," + i * size + ")"; })
        .each(function(d) { y.domain(domainByTrait[d]); d3.select(this).call(yAxis); });

    var cell = svg.selectAll(".cell")
        .data(cross(traits, traits))
        .enter().append("g")
        .attr("class", "cell")
        .attr("transform", function(d) { return "translate(" + (n - d.i - 1) * size + "," + d.j * size + ")"; })
        .each(plot);

    // Titles for the diagonal.
    cell.filter(function(d) { return d.i === d.j; }).append("text")
        .attr("x", padding)
        .attr("y", padding)
        .attr("dy", ".71em")
        .text(function(d) { return d.x; });

    cell.call(brush);

    // Histograms on the diagonal
    cell.filter(function(d) { return d.i === d.j; }).append("text")
        .attr("x", padding)
        .attr("y", padding)
        .attr("dy", ".71em")
        .text(function(d) { return d.x; });

    function plot(p) {
        var cell = d3.select(this);

        x.domain(domainByTrait[p.x]);
        y.domain(domainByTrait[p.y]);

        cell.append("rect")
            .attr("class", "frame")
            .attr("x", padding / 2)
            .attr("y", padding / 2)
            .attr("width", size - padding)
            .attr("height", size - padding);

        cell.selectAll("circle")
            .data(data)
        .enter().append("circle")
            .attr("cx", function(d) { return x(d[p.x]); })
            .attr("cy", function(d) { return y(d[p.y]); })
            .attr("r", 4)
            .style("fill", function(d) { return color(0); });
    }

    var brushCell;

    // Clear the previously-active brush, if any.
    function brushstart(p) {
        if (brushCell !== this) {
            d3.select(brushCell).call(brush.move, null);
            brushCell = this;
            x.domain(domainByTrait[p.x]);
            y.domain(domainByTrait[p.y]);
        }
    }

    // Highlight the selected circles.
    function brushmove(p) {
        var e = d3.brushSelection(this);
        svg.selectAll("circle").classed("hidden", function(d) {
        return !e
            ? false
            : (
            e[0][0] > x(+d[p.x]) || x(+d[p.x]) > e[1][0]
            || e[0][1] > y(+d[p.y]) || y(+d[p.y]) > e[1][1]
            );
        });
    }

    // If the brush is empty, select all circles.
    function brushend() {
        var e = d3.brushSelection(this);
        if (e === null) svg.selectAll(".hidden").classed("hidden", false);
    }

    function cross(a, b) {
    var c = [], n = a.length, m = b.length, i, j;
    for (i = -1; ++i < n;) for (j = -1; ++j < m;) c.push({x: a[i], i: i, y: b[j], j: j});
        return c;
    }
}