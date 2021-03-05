import dash
import dash_core_components as dcc
import dash_html_components as html

app = dash.Dash()

fnameDict = {'chriddy': ['opt1_c', 'opt2_c', 'opt3_c'], 'jackp': ['opt1_j', 'opt2_j']}

names = list(fnameDict.keys())
nestedOptions = fnameDict[names[0]]

app.layout = html.Div(
    [
        html.Div([
        dcc.Dropdown(
            id='name-dropdown',
            options=[{'label':name, 'value':name} for name in names],
            value = list(fnameDict.keys())[0]
            ),
            ],style={'width': '20%', 'display': 'inline-block'}),
        html.Div([
        dcc.Dropdown(
            id='opt-dropdown',
            ),
            ],style={'width': '20%', 'display': 'inline-block'}
        ),
        html.Hr(),
        html.Div(id='display-selected-values')
    ]
)

@app.callback(
    dash.dependencies.Output('opt-dropdown', 'options'),
    [dash.dependencies.Input('name-dropdown', 'value')]
)
def update_date_dropdown(name):
    return [{'label': i, 'value': i} for i in fnameDict[name]]

@app.callback(
    dash.dependencies.Output('display-selected-values', 'children'),
    [dash.dependencies.Input('opt-dropdown', 'value')])
def set_display_children(selected_value):
    return 'you have selected {} option'.format(selected_value)


if __name__ == '__main__':
    app.run_server(debug=True)