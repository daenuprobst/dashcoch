if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.clientside = {
  update_map: function(mode, slider_date_index, div_data) {
    data_raw = JSON.parse(div_data);

    var data = {
      swiss_cases: {},
      swiss_cases_by_date_filled: {},
      swiss_cases_by_date_filled_per_capita: {},
      swiss_fatalities_by_date_filled: {},
      regional_centres: {},
      swiss_cases_by_date_diff: {},
      swiss_fatalities_by_date_diff: {},
      swiss_hospitalizations_by_date_diff: {},
      swiss_hospitalizations_by_date_filled: {},
    };

    for (var n in data) {
      for (var key in data_raw[n]) {
        if (data_raw[n].hasOwnProperty(key)) {
          values = []
          for (var subkey in data_raw[n][key]) {
            if (data_raw[n][key].hasOwnProperty(subkey)) {
              values.push(data_raw[n][key][subkey])
            }
          }
          data[n][key] = values
        }
      }
    }
    
    var d = slider_date_index;
    var map_data = data["swiss_cases_by_date_filled"];
    var labels = []

    for (var region in data.regional_centres)
      if (region !== null)
        labels.push(region + ": " + Math.round(map_data[region][d]).toString());
      else
        labels.push("");

    if (mode === "prevalence") {
      labels = [];
      map_data = data["swiss_cases_by_date_filled_per_capita"];
      for (var region in data.regional_centres)
        if (map_data[region][d] !== null)
          labels.push(region + ": " + (Math.round(map_data[region][d] * 100) / 100).toString());
        else
          labels.push("");
    } else if (mode === "fatalities") {
      labels = [];
      map_data = data["swiss_fatalities_by_date_filled"];
      for (var region in data.regional_centres)
        if (map_data[region][d] !== null)
          labels.push(region + ": " + Math.round(map_data[region][d]).toString());
        else
          labels.push("");
    } else if (mode === "new") {
      labels = [];
      map_data = data["swiss_cases_by_date_diff"];
      for (var region in data.regional_centres)
        if (map_data[region][d] !== null && data_raw["region_updates"][region])
         labels.push(region + ": " + Math.round(map_data[region][d]).toString());
        else
          labels.push("");
    } else if (mode === "new_fatalities") {
      labels = [];
      map_data = data["swiss_fatalities_by_date_diff"];
      for (var region in data.regional_centres)
        if (map_data[region][d] !== null)
          labels.push(region + ": " + Math.round(map_data[region][d]).toString());
        else
          labels.push("");
    } else if (mode === "new_hospitalizations") {
      labels = [];
      map_data = data["swiss_hospitalizations_by_date_diff"];
      for (var region in data.regional_centres)
        if (map_data[region][d] !== null)
          labels.push(region + ": " + Math.round(map_data[region][d]).toString());
        else
          labels.push("");
    } else if (mode === "hospitalizations") {
      labels = [];
      map_data = data["swiss_hospitalizations_by_date_filled"];
      for (var region in data.regional_centres)
        if (map_data[region][d] !== null)
          labels.push(region + ": " + Math.round(map_data[region][d]).toString());
        else
          labels.push("");
    }

    var lat = [];
    var lon = [];

    for (var region in data["regional_centres"]) {
      lat.push(data_raw["regional_centres"][region]["lat"]);
      lon.push(data_raw["regional_centres"][region]["lon"]);
    }

    var z = [];

    for (var region in map_data)
      if (region !== data_raw["settings"]["total_column_name"])
        z.push(map_data[region][d]);

    return {
      data: [
        {
          lat: lat,
          lon: lon,
          text: labels,
          mode: "text",
          type: "scattergeo",
          textfont: {
              family: "Arial, sans-serif",
              size: 16,
              color: "white",
              weight: "bold",
          },
        },
        {
          type: "choropleth",
          showscale: false,
          locations: data_raw["region_labels"],
          z: z,
          colorscale: data_raw["turbo"],
          geojson: data_raw["settings"]["choropleth"]["geojson_file"],
          featureidkey: data_raw["settings"]["choropleth"]["feature"],
          marker: {line: {width: 0.0, color: "#08302A"}},
        },
      ],
      layout: {
        geo: {
          visible: false,
          center: data_raw["settings"]["choropleth"]["center"],
          lataxis: {
            range: data_raw["settings"]["choropleth"]["lataxis"]
          },
          lonaxis: {
            range: data_raw["settings"]["choropleth"]["lonaxis"]
          },
          projection: {type: "transverse mercator"},
        },
        margin: {l: 0, r: 0, t: 0, b: 0},
        plot_bgcolor: data_raw["theme"]["background"],
        paper_bgcolor: data_raw["theme"]["background"],
      },
    }

  },
  update_caseincrease_regional_graph: function (selected_cantons, selected_scale, selected_date_index, hover_data, div_data) {
    hovered_canton = ""
    if (hover_data)
      hovered_canton = selected_cantons[hover_data["points"][0]["curveNumber"]]

    var d = selected_date_index

    data_raw = JSON.parse(div_data);

    var data = {
      swiss_cases_by_date_filled: {},
      moving_total: []
    };

    for (var n in data) {
      for (var key in data_raw[n]) {
        if (data_raw[n].hasOwnProperty(key)) {
          values = []
          for (var subkey in data_raw[n][key]) {
            if (data_raw[n][key].hasOwnProperty(subkey)) {
              values.push(data_raw[n][key][subkey])
            }
          }
          data[n][key] = values
        }
      }
    }

    var x_max = 0
    var y_max = 0

    selected_cantons.forEach(canton => {
      x_max = Math.max(x_max, Math.max(...data["swiss_cases_by_date_filled"][canton]))
      y_max = Math.max(y_max, Math.max(...data["moving_total"][canton]))
    })

    traces = []
    selected_cantons.forEach(canton => {
      traces.push({
        x: data["swiss_cases_by_date_filled"][canton].slice(6, d),
        y: data["moving_total"][canton].slice(6, d),
        mode: "lines",
        name: canton,
        marker: {
          color: "#22e7ff"
        },
        line: {
          width: hovered_canton == canton ? 2.0 : 1.0,
          color: hovered_canton == canton ? "#22e7ff" : "rgba(255, 255, 255, 0.5)",
        },
        text: data.moving_total["date_label"].slice(6, d),
        hovertemplate: data_raw["i18n"]["plot_log_log_region_weekly_hovertemplate"],
        showlegend: false,
      })
    })

    selected_cantons.forEach(canton => {
      traces.push({
        x: [data["swiss_cases_by_date_filled"][canton][d - 1]],
        y: [data["moving_total"][canton][d - 1]],
        mode: "markers+text",
        name: canton,
        text: canton,
        marker: {
          color: "white",
        },
        hoverinfo: "skip",
        showlegend: false,
        textposition: "center right",
      })
    })

    return {
      data: traces,
      layout: {
        height: 750,
        xaxis: {
          showgrid: true,
          color: "#ffffff",
          title: data_raw["i18n"]["plot_loglog_region_x"],
          type: "log",
          range: [0, Math.log10(x_max) * 1.05]
        },
        yaxis: {
          type: "log",
          showgrid: true,
          color: "#ffffff",
          rangemode: "tozero",
          title: data_raw["i18n"]["plot_loglog_region_y"],
          range: [0, Math.log10(y_max) * 1.05]
        },
        legend: {
          x: 0.015,
          y: 1,
          traceorder: "normal",
          font: {
            family: "sans-serif",
            color: "white"
          },
          bgcolor: "#1F2123",
          bordercolor: "#7fafdf",
          borderwidth: 1,
        },
        dragmode: false,
        hovermode: "closest",
        margin: {
          l: 60,
          r: 20,
          t: 60,
          b: 70
        },
        plot_bgcolor: "#1f2123",
        paper_bgcolor: "#1f2123",
        font: {
          color: "#22e7ff"
        },
      }
    }
  }
}