import os
from contextlib import redirect_stdout

import dash_antd_components as dac
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
import numpy as np
from dash import callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from dash.dash_table import DataTable

from alphaDeesp.core.grid2op.Grid2opSimulation import (
    Grid2opSimulation,
)
from alphaDeesp.expert_operator import expert_operator

from grid2op.PlotGrid import PlotPlotly
from grid2op.Space import GridObjects
from grid2game.expert.BaseAssistant import BaseAssistant


expert_config = {
    "totalnumberofsimulatedtopos": 25,
    "numberofsimulatedtopospernode": 5,
    "maxUnusedLines": 2,
    "ratioToReconsiderFlowDirection": 0.75,
    "ratioToKeepLoop": 0.25,
    "ThersholdMinPowerOfLoop": 0.1,
    "ThresholdReportOfLine": 0.2,
}

reward_type = "MinMargin_reward"


def compute_losses(obs):
    return (obs.prod_p.sum() - obs.load_p.sum()) / obs.load_p.sum()

def get_ranked_overloads(observation_space, observation):
    timestepsOverflowAllowed = (
        3  # observation_space.parameters.NB_TIMESTEP_OVERFLOW_ALLOWED
    )

    sort_rho = -np.sort(
        -observation.rho
    )  # sort in descending order for positive values
    sort_indices = np.argsort(-observation.rho)
    ltc_list = [sort_indices[i] for i in range(len(sort_rho)) if sort_rho[i] >= 1]

    # now reprioritize ltc if critical or not
    ltc_critical = [
        l
        for l in ltc_list
        if (observation.timestep_overflow[l] == timestepsOverflowAllowed)
    ]
    ltc_not_critical = [
        l
        for l in ltc_list
        if (observation.timestep_overflow[l] != timestepsOverflowAllowed)
    ]

    ltc_list = ltc_critical + ltc_not_critical
    if len(ltc_list) == 0:
        ltc_list = [sort_indices[0]]
    return ltc_list


class Assist(BaseAssistant):
    def __init__(self, env):
        super().__init__()
        self.env = env
        self.grid = GridObjects.init_grid(self.env.observation_space)
        self.lines = self.get_grid_lines()

    def layout(self):
        return html.Div(
            children=[
                html.Div(
                    [
                        html.Label("", id="expert_agent_button", n_clicks=0)
                    ],
                    id="hidden_buttons_for_callbacks",
                    style={'display': 'none'}
                ),
                dcc.Store(id="assistant_actions"),
                dcc.Store(
                    id="assistant-size", data=dict(assist="col-3", graph="col-9")
                ),
                html.P("Choose a line to study:", className="my-2"),
                dac.Select(
                    id="select_lines_to_cut",
                    options=[
                        {"label": line_name, "value": line_name}
                        for line_name in self.lines
                    ],
                    mode="default",
                    value=self.lines[0],
                ),
                html.P("Flow ratio (in %) to get below"),
                dbc.Input(
                    type="number",
                    min=0,
                    max=100,
                    step=1,
                    id="input_flow_ratio",
                    value=100,
                ),
                html.P("Number of simulations to run:", className="my-2"),
                dbc.Input(
                    type="number",
                    min=0,
                    max=50,
                    step=1,
                    id="input_nb_simulations",
                    value=15,
                ),
                dbc.Button(
                    id="assist-evaluate",
                    children=["Evaluate with the Expert system"],
                    color="danger",
                    className="m-3",
                ),
                dbc.Button(
                    id="assist-reset",
                    children=["Reset"],
                    color="secondary",
                    className="m-3",
                ),
                html.Div(id="expert-results"),
                html.Pre(
                    id="assist-action-info",
                    className="more-info-table",
                    children="Select an action in the table above.",
                ),
                dbc.Button(
                    id="add_expert_recommendation",
                    children=["Add to Recommendations"],
                    color="primary",
                    className="m-3",
                    n_clicks=0,
                ),
                dcc.Link(
                    "See the ExpertOP4Grid documentation for more information",
                    href="https://expertop4grid.readthedocs.io/en/latest/DESCRIPTION.html#didactic-example",
                ),
            ],
            id="all_expert_assist"
        )

    def register_callbacks(self, app):
        @app.callback(
            [
                Output("expert-results", "children"),
                Output("assistant_actions", "data"),
                Output("assistant-size", "data"),
            ],
            [
                Input("assist-evaluate", "n_clicks"),
                Input("assist-reset", "n_clicks")],
            [
                State("input_nb_simulations", "value"),
                State("input_flow_ratio", "value"),
                State("select_lines_to_cut", "value"),
            ],
        )
        def evaluate_expert_system(
            evaluate_n_clicks,
            reset_n_clicks,
            nb_simulations,
            flow_ratio,
            line_to_study,
        ):
            if evaluate_n_clicks is None:
                raise PreventUpdate

            ctx = callback_context
            if not ctx.triggered:
                raise PreventUpdate
            else:
                button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            print("evaluate_expert_system")

            if button_id == "assist-evaluate":
                print("evaluate_expert_system: assist-evaluate")
                assistant_size = dict(assist="col-12", graph="hidden")
            else:
                assistant_size = dict(assist="col-3", graph="col-9")
                return "", [], assistant_size

            thermal_limit = self.env.glop_env.get_thermal_limit()

            if nb_simulations is not None:
                expert_config["totalnumberofsimulatedtopos"] = nb_simulations

            if line_to_study is not None:
                line_id = self.get_line_id(line_to_study)
                ltc = [line_id]
            else:
                ltc = [get_ranked_overloads(self.env.observation_space, self.env.obs)[0]]

            if flow_ratio is not None and line_to_study is not None:
                new_thermal_limit = thermal_limit.copy()
                line_id = self.get_line_id(line_to_study)
                new_thermal_limit[line_id] = (
                    flow_ratio / 100.0 * new_thermal_limit[line_id]
                )

            self.env.glop_env.set_thermal_limit(new_thermal_limit)

            #with redirect_stdout(None):
            print("evaluate_expert_system: Grid2opSimulation")
            simulator = Grid2opSimulation(
                self.env.obs,
                self.env.action_space,
                self.env.observation_space,
                param_options=expert_config,
                debug=False,
                ltc=ltc,
                reward_type=reward_type,
            )
            print("evaluate_expert_system: expert_operator")
            ranked_combinations, expert_system_results, actions = expert_operator(
                simulator, plot=False, debug=False
            )

            # reinitialize proper thermal limits
            self.env.glop_env.set_thermal_limit(thermal_limit)

            expert_system_results = expert_system_results.sort_values(
                ["Topology simulated score", "Efficacity"], ascending=False
            )
            actions = [actions[i] for i in expert_system_results.index]

            # Newest versions of DataTable accept only types: [string, number, boolean].
            # Convert list and numpy arrays to strings:
            expert_system_results['Worsened line'] = [','.join(map(str, l)) for l in expert_system_results['Worsened line']]
            expert_system_results['Topology applied'] = [','.join(map(str, l)) for l in expert_system_results['Topology applied']]
            expert_system_results['Internal Topology applied '] = [','.join(map(str, l)) for l in expert_system_results['Internal Topology applied ']]

            return (
                DataTable(
                    id="table",
                    columns=[
                        {"name": i, "id": i} for i in expert_system_results.columns
                    ],
                    data=expert_system_results.to_dict("records"),
                    style_table={"overflowX": "auto"},
                    sort_action="native",
                    row_selectable="single",
                    style_cell={
                        "overflow": "hidden",
                        "textOverflow": "ellipsis",
                        "maxWidth": 0,
                    },
                    tooltip_data=[
                        {
                            column: {"value": str(value), "type": "markdown"}
                            for column, value in row.items()
                        }
                        for row in expert_system_results.to_dict("rows")
                    ],
                ),
                [action.to_vect() for action in actions],
                assistant_size,
            )

        @app.callback(
            [
                Output("assist-action-info", "children"),
            ],
            [
                Input("table", "selected_rows"),
                Input("assist-reset", "n_clicks")
            ],
            [State("assistant_actions", "data")],
        )
        def select_action(selected_rows, n_clicks, actions):
            ctx = callback_context
            if not ctx.triggered:
                raise PreventUpdate
            else:
                component_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if component_id == "assist-reset":
                return [], ""
            if selected_rows is None:
                raise PreventUpdate
            selected_row = selected_rows[0]
            action = actions[selected_row]
            act = self.env.action_space.from_vect(np.array(action))
            self.env.expert_selected_action = action
            return [str(act)]

    def get_line_id(self, line_to_study):
        for line_id, name in enumerate(self.grid.name_line):
            if name == line_to_study:
                return line_id
        return None

    def get_grid_lines(self):
        lines = []
        for line_id, name in enumerate(self.grid.name_line):
            lines.append(name)
        return lines

    def store_to_graph(
        self,
        store_data,
    ):
        act = self.env.action_space.from_vect(np.array(store_data))
        if self.env.obs is not None:
            obs, *_ = self.env.obs.simulate(action=act, time_step=0)
            # make sure rho is properly calibrated. Problem could be that obs_reboot thermal limits are not properly initialized
            obs.rho = (
                obs.rho
                * self.env.obs._obs_env.get_thermal_limit()
                / self.env.get_thermal_limit()
            )
            try:
                network_graph_factory = PlotPlotly(
                    grid_layout=self.env.observation_space.grid_layout,
                    observation_space=self.env.observation_space,
                    responsive=True,
                )
                new_network_graph = network_graph_factory.plot_obs(observation=obs)
            except ValueError:
                import traceback

                new_network_graph = traceback.format_exc()

            return new_network_graph

    def store_to_kpis(
        self,
        store_data,
    ):
        act = self.env.action_space.from_vect(np.array(store_data))
        if self.env.obs is not None:
            obs, reward, *_ = self.env.obs.simulate(action=act, time_step=0)
            # make sure rho is properly calibrated. Problem could be that obs_reboot thermal limits are not properly initialized
            obs.rho = (
                obs.rho
                * self.env.obs._obs_env.get_thermal_limit()
                / self.env.get_thermal_limit()
            )
        else:
            raise RuntimeError(
                f"Assist.store_to_kpis cannot be called before first rebooting the Episode"
            )
        rho_max = f"{obs.rho.max() * 100:.0f}%"
        nb_overflows = f"{(obs.rho > 1).sum():,.0f}"
        losses = f"{compute_losses(obs)*100:.2f}%"
        return reward, rho_max, nb_overflows, losses
