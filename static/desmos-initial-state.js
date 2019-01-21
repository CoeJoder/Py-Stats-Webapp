// exported from `calculator.getState()`
var SkiSlope__initialGraphState = {
  "version": 7,
  "graph": {
    "squareAxes": false,
    "viewport": {
      "xmin": -10.170007158196135,
      "ymin": -701.629589647906,
      "xmax": 84.82999284180386,
      "ymax": 2828.513016574317
    }
  },
  "expressions": {
    "list": [
      {
        "type": "expression",
        "id": "func",
        "color": "#2d70b3",
        "latex": "y_1\\sim h\\cdot\\cos\\left(\\frac{2\\left(x_1+v\\right)\\pi}{p}\\right)+b",
        "residualVariable": "e_1",
        "regressionParameters": {
          "y_1": 1.4037684528684444,
          "x_1": 16.90122073908046
        }
      },
      {
        "type": "text",
        "id": "2",
        "text": "Select an approximate solution for the parameters.  The more accurate, the faster the calculation will be.  A very poor approximation may not converge at all."
      },
      {
        "type": "expression",
        "id": "h",
        "color": "#388c46",
        "latex": "h = 700",
        "label": "h",
        "slider": {
          "hardMin": true,
          "hardMax": true,
          "max": "1000",
          "step": "0.001"
        }
      },
      {
        "type": "expression",
        "id": "b",
        "color": "#6042a6",
        "latex": "b = 200",
        "label": "b",
        "slider": {
          "hardMin": true,
          "hardMax": true,
          "max": "1000",
          "step": "0.001"
        }
      },
      {
        "type": "expression",
        "id": "v",
        "color": "#000000",
        "latex": "v = 0",
        "label": "v",
        "slider": {
          "hardMin": true,
          "hardMax": true,
          "step": "0.001"
        }
      },
      {
        "type": "expression",
        "id": "p",
        "color": "#c74440",
        "latex": "p = 24",
        "label": "p",
        "slider": {
          "hardMin": true,
          "hardMax": true,
          "max": "100",
          "step": "0.001"
        }
      },
      {
        "type": "text",
        "id": "3",
        "text": "Import a spreadsheet (.xls, .xlxs) with time (Column A) and data (Column B) values."
      }
    ]
  }
};