#!/usr/bin/env python
# coding: utf-8

import random
from fuzzywuzzy import process
import pandas as pd
import seaborn as sns
import dash
from dash import dcc
from dash import html
import dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots

sns.set()

players_df = pd.read_csv('clustered_positions.csv')
image_path = '/Users/Felipe/Desktop/Concordia-bootcamps/Final Project/image.jpg'
toggle = False

def get_closest_match(player_name, players_df):
    """Find the closest matching player name using fuzzy matching."""
    player_names = players_df['Player'].values
    closest_match = process.extractOne(player_name, player_names)
    return closest_match[0]


def get_cluster_players(player_name, players_df):
    """Retrieve player's stats, along with five random players of the same position and same cluster,
    and return the analysis output as a string."""

    # Find the cluster and position of the specified player
    player_row = players_df.loc[players_df['Player'] == player_name]
    player_cluster = player_row['Cluster'].values[0]
    player_position = player_row['Pos'].values[0]

    # Filter players of the same position and same cluster
    cluster_players = players_df.loc[(players_df['Cluster'] == player_cluster) & (players_df['Pos'] == player_position)]

    # Exclude the specified player from random player selection
    cluster_players = cluster_players.loc[cluster_players['Player'] != player_name]

    # Select five random players from the same position and same cluster
    random_players = cluster_players.sample(n=5)

    # Get the chosen player's stats
    player_stats = player_row[['Player', 'Age', 'Min', 'Gls', 'Ast', 'G+A', 'CrdY', 'CrdR',
                               'PrgC', 'PrgP', 'PrgR', 'Gls90', 'Ast90', 'G+A90', 'xG90', 'xAG90', 'xG+xAG90']]

    # Get the cluster stats of the same position
    position_cluster_stats = players_df.loc[players_df['Pos'] == player_position].groupby('Cluster').describe()

    # Create the analysis output as a string
    output = ""
    output += f"Player: {player_name}\n"
    output += f"Cluster: {player_cluster}\n\n"
    output += "Player Stats:\n"
    output += player_stats.to_string(index=False)
    output += "\n\n"

    # Create the bar graphs using Plotly
    categories = ['Age', 'Min', 'Gls', 'Ast', 'G+A', 'CrdY', 'CrdR',
                  'PrgC', 'PrgP', 'PrgR', 'Gls90', 'Ast90', 'G+A90', 'xG90', 'xAG90', 'xG+xAG90']

    fig = make_subplots(rows=4, cols=4, subplot_titles=categories)

    for i, category in enumerate(categories):
        player_value = player_stats[category].values[0]
        cluster_avg = cluster_players[category].mean()
        other_clusters_avgs = position_cluster_stats.loc[:, (category, 'mean')].values
        cluster_labels = [str(label) for label in position_cluster_stats.index]

        x_ticks = ['Player', 'Cluster Avg'] + cluster_labels
        x_values = [player_value, cluster_avg] + list(other_clusters_avgs)

        fig.add_trace(
            go.Bar(x=x_ticks, y=x_values, marker_color=['blue', 'orange'] + ['lightgray'] * len(cluster_labels)),
            row=(i // 4) + 1,
            col=(i % 4) + 1
        )

    fig.update_layout(height=800, width=800, showlegend=False)

    # Return the analysis output and graphs
    return html.Div([
        html.Pre(output),
        html.Div([
            dcc.Graph(figure=fig),
            html.H3("Random Players"),
            html.Table([
                html.Thead(html.Tr([html.Th(col) for col in random_players.columns])),
                html.Tbody([
                    html.Tr([html.Td(random_players.iloc[i][col]) for col in random_players.columns])
                    for i in range(len(random_players))
                ])
            ])
        ])
    ])


app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Big 5 European Leagues Player Analysis"),
    html.Div([
        dcc.Input(id='player-name-input', type='text', placeholder='Enter player name', style={'font-family': 'Arial'}),
        html.Button('Submit', id='submit-button', n_clicks=0),
        html.Button('Glossary', id='glossary-button', n_clicks=0),
    ]),
    html.Div([
        html.H2("All Players", style={'font-family': 'Arial'}),
        html.Div(
            dash_table.DataTable(
                id='players-table',
                columns=[{"name": col, "id": col} for col in players_df.columns],
                data=players_df.to_dict('records'),
                page_size=10,
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
                style_cell={
                    'textAlign': 'center',
                    'padding': '8px',
                    'font-family': 'Arial'
                },
                style_header={
                    'fontWeight': 'bold',
                    'font-family': 'Arial'
                }
            )
        )
    ]),
    html.Img(src='assets/football.jpeg', alt='The Stars'),
    html.Div(id='analysis-output', className='analysis-output'),
    html.Div(id='glossary-image')
])


@app.callback(
    Output('analysis-output', 'children'),
    Input('submit-button', 'n_clicks'),
    State('player-name-input', 'value')
)
def analyze_player(n_clicks, player_name):
    if n_clicks > 0:
        closest_match = get_closest_match(player_name, players_df)

        if closest_match in players_df['Player'].values:
            # Generate the analysis output
            analysis_output = get_cluster_players(closest_match, players_df)

            # Return the analysis output
            return analysis_output

        return "Player not found."


@app.callback(
    Output('glossary-image', 'children'),
    Input('glossary-button', 'n_clicks')
)
def display_glossary(n_clicks):
    if n_clicks %2 != 0:
        image_element = html.Img(src='assets/glossary.png', style= {'max-width': '1500px', 'display': 'block'})
        return image_element
    else:
        image_element = html.Img(src='assets/glossary.png', style= {'max-width': '500px', 'display': 'none'})
        return image_element
    #if n_clicks > 0:
        # Create an HTML image element with the source path to your glossary image
        #image_element = html.Img(src='assets/glossary.png', style= {'max-width': '150px'})

        # Return the image element to update the 'glossary-image' Div
        #return image_element
    #else:
        # If the button hasn't been clicked yet, don't display the image
        #return None


if __name__ == '__main__':
    app.run_server(port=8057, debug=True)

