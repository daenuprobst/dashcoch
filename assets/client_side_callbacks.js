if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.clientside = {
  update_caseincrease_regional_graph: function (selected_cantons, selected_scale, selected_date_index, hover_data, div_data) {
    hovered_canton = ""
    if (hover_data)
      hovered_canton = selected_cantons[hover_data["points"][0]["curveNumber"]]

    var d = selected_date_index

    data_raw = JSON.parse(div_data)

    var data = {
      swiss_cases_by_date_filled: {},
      moving_total: []
    }

    // Format the data & let's support IE
    for (var key in data_raw["swiss_cases_by_date_filled"]) {
      if (data_raw["swiss_cases_by_date_filled"].hasOwnProperty(key)) {
        values = []
        for (var subkey in data_raw["swiss_cases_by_date_filled"][key]) {
          if (data_raw["swiss_cases_by_date_filled"][key].hasOwnProperty(subkey)) {
            values.push(data_raw["swiss_cases_by_date_filled"][key][subkey])
          }
        }
        data["swiss_cases_by_date_filled"][key] = values
      }
    }

    for (var key in data_raw["moving_total"]) {
      if (data_raw["moving_total"].hasOwnProperty(key)) {
        values = []
        for (var subkey in data_raw["moving_total"][key]) {
          if (data_raw["moving_total"][key].hasOwnProperty(subkey)) {
            values.push(data_raw["moving_total"][key][subkey])
          }
        }
        data["moving_total"][key] = values
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
          color: "#22E7FF"
        },
        line: {
          width: hovered_canton == canton ? 2.0 : 1.0,
          color: hovered_canton == canton ? "#22E7FF" : "rgba(255, 255, 255, 0.5)",
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

    // Updated the header
    document.getElementById("date-container-regional").innerHTML = data.moving_total["date_label"][d - 1]

    return {
      data: traces,
      layout: {
        title: data_raw["i18n"]["plot_loglog_region_title"],
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
        plot_bgcolor: "#1F2123",
        paper_bgcolor: "#1F2123",
        font: {
          color: "#22E7FF"
        },
      }
    }
  }
}